"""Tầng lưu trữ SQLite WAL cho RepoKSV (Hướng 1 + Hướng 2) — 100% Python stdlib.

Quản lý 6 bảng chuẩn theo docs/tech-spec-huong-1-2.md §5:
    users · scan_sessions · viva_entries · bloom_profiles · github_cache · rate_limit_events

Quyền riêng tư: tuyệt đối không lưu mã nguồn bài nộp của repo đội khác xuống SQLite;
chỉ lưu metadata, hard_flags, checks, line_counts, trích dẫn ngắn và hồ sơ Bloom.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(ROOT, ".study_logs", "repoksv.db")

_STRIPPED_SOURCE_KEYS = frozenset({
    "files_content",
    "file_contents",
    "raw_files",
    "files_raw",
    "source_files",
})

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  google_sub TEXT UNIQUE,
  email TEXT NOT NULL DEFAULT '',
  display_name TEXT NOT NULL DEFAULT '',
  picture_url TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scan_sessions (
  scan_id TEXT PRIMARY KEY,
  owner_user_id TEXT NOT NULL REFERENCES users(user_id),
  source_type TEXT NOT NULL,
  source_label TEXT NOT NULL,
  commit_sha TEXT NOT NULL DEFAULT '',
  mode TEXT NOT NULL,
  members_json TEXT NOT NULL DEFAULT '[]',
  audit_output TEXT NOT NULL,
  hard_flags_json TEXT NOT NULL DEFAULT '[]',
  checks_json TEXT NOT NULL DEFAULT '{}',
  missing_required_json TEXT NOT NULL DEFAULT '[]',
  line_counts_json TEXT NOT NULL DEFAULT '{}',
  tracing_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scans_owner_time
  ON scan_sessions(owner_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scans_label
  ON scan_sessions(owner_user_id, source_label, created_at DESC);

CREATE TABLE IF NOT EXISTS viva_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scan_id TEXT NOT NULL REFERENCES scan_sessions(scan_id) ON DELETE CASCADE,
  member_slug TEXT NOT NULL,
  member_name TEXT NOT NULL,
  mode TEXT NOT NULL,
  concept_key TEXT NOT NULL DEFAULT '',
  question TEXT NOT NULL DEFAULT '',
  answer TEXT NOT NULL DEFAULT '',
  ai_feedback TEXT NOT NULL DEFAULT '',
  bloom_level INTEGER,
  draft_json TEXT NOT NULL DEFAULT '{}',
  saved_by_user INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_viva_scan_member
  ON viva_entries(scan_id, member_slug);

CREATE TABLE IF NOT EXISTS bloom_profiles (
  owner_user_id TEXT NOT NULL REFERENCES users(user_id),
  member_slug TEXT NOT NULL,
  concept_key TEXT NOT NULL,
  term TEXT NOT NULL DEFAULT '',
  tag TEXT NOT NULL DEFAULT 'khai_niem',
  source_cite TEXT NOT NULL DEFAULT '',
  bloom_level INTEGER NOT NULL DEFAULT 0,
  highest_bloom_level INTEGER NOT NULL DEFAULT 0,
  understood_json TEXT NOT NULL DEFAULT '[]',
  missing_json TEXT NOT NULL DEFAULT '[]',
  misconceptions_json TEXT NOT NULL DEFAULT '[]',
  resolved_misconceptions_json TEXT NOT NULL DEFAULT '[]',
  next_probe TEXT NOT NULL DEFAULT '',
  prompt TEXT NOT NULL DEFAULT '',
  reference TEXT NOT NULL DEFAULT '',
  rubric TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'needs_review',
  history_json TEXT NOT NULL DEFAULT '[]',
  updated_at TEXT NOT NULL,
  PRIMARY KEY (owner_user_id, member_slug, concept_key)
);

CREATE TABLE IF NOT EXISTS github_cache (
  cache_key TEXT PRIMARY KEY,
  commit_sha TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL,
  expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS rate_limit_events (
  bucket_key TEXT PRIMARY KEY,
  window_start INTEGER NOT NULL,
  count INTEGER NOT NULL
);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text: str, default: str = "user") -> str:
    """Chuẩn hoá chuỗi thành slug an toàn cho DB và tên file (chống path traversal)."""
    raw = (text or "").strip()
    if not raw:
        return default
    raw = raw.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFKD", raw)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    cleaned = re.sub(r"[^a-z0-9_-]+", "-", ascii_only)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-_")
    if not cleaned or cleaned in {".", ".."}:
        return default
    return cleaned[:80]


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return fallback


def _dedup_str_list(items: list[Any] | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items or []:
        text = str(item).strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _flag_signature(flag: Any) -> str:
    if isinstance(flag, dict):
        return f"{flag.get('rule_id', '')}|{flag.get('file', '')}|{flag.get('line', '')}"
    return str(flag)


def _strip_source_blobs(payload: Any) -> Any:
    """Loại bỏ trường chứa mã nguồn thô trước khi lưu xuống SQLite."""
    if isinstance(payload, dict):
        return {
            k: _strip_source_blobs(v)
            for k, v in payload.items()
            if k not in _STRIPPED_SOURCE_KEYS
        }
    if isinstance(payload, list):
        return [_strip_source_blobs(item) for item in payload]
    return payload


class RepoKsvDB:
    """Kho lưu trữ SQLite WAL thread-safe cho toàn bộ phiên quét, hồ sơ Bloom, cache và rate-limit."""

    def __init__(self, db_path: str | os.PathLike[str] | None = None) -> None:
        raw_path = os.fspath(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path = raw_path if raw_path == ":memory:" else os.path.abspath(raw_path)
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._local = threading.local()
        self._write_lock = threading.RLock()
        self._conn_lock = threading.Lock()
        self._conns: list[sqlite3.Connection] = []
        self._init_schema()

    def __enter__(self) -> "RepoKsvDB":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def _configure_conn(self, conn: sqlite3.Connection) -> None:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA foreign_keys=ON;")

    def _get_conn(self) -> sqlite3.Connection:
        conn: sqlite3.Connection | None = getattr(self._local, "conn", None)
        if conn is not None:
            return conn
        # Mỗi thread giữ một connection riêng qua threading.local();
        # check_same_thread=False chỉ để close() dọn sạch mọi handle khi shutdown trên Windows.
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        self._configure_conn(conn)
        self._local.conn = conn
        with self._conn_lock:
            self._conns.append(conn)
        return conn

    def _init_schema(self) -> None:
        with self._write_lock:
            conn = self._get_conn()
            conn.executescript(SCHEMA_SQL)
            cols = {r["name"] for r in conn.execute("PRAGMA table_info(bloom_profiles)").fetchall()}
            if "source_repo" not in cols:
                conn.execute("ALTER TABLE bloom_profiles ADD COLUMN source_repo TEXT NOT NULL DEFAULT ''")
            if "source_scan_id" not in cols:
                conn.execute("ALTER TABLE bloom_profiles ADD COLUMN source_scan_id TEXT NOT NULL DEFAULT ''")
            conn.commit()

    def close_thread(self) -> None:
        """Đóng connection riêng của thread hiện tại."""
        conn: sqlite3.Connection | None = getattr(self._local, "conn", None)
        if conn is None:
            return
        self._local.conn = None
        with self._conn_lock:
            if conn in self._conns:
                self._conns.remove(conn)
        try:
            conn.close()
        except sqlite3.Error:
            pass

    def close(self) -> None:
        """Đóng mọi connection đã mở (hữu ích khi dọn thư mục tạm trên Windows)."""
        with self._conn_lock:
            conns = list(self._conns)
            self._conns.clear()
        self._local = threading.local()
        for conn in conns:
            try:
                conn.close()
            except sqlite3.Error:
                pass

    # ── Users ──────────────────────────────────────────────────────────────

    def upsert_user(
        self,
        user_id: str,
        google_sub: str | None = None,
        email: str = "",
        display_name: str = "",
        picture_url: str = "",
        created_at: str | None = None,
    ) -> dict[str, Any]:
        """Thêm mới hoặc cập nhật thông tin người dùng."""
        uid = (user_id or "").strip()
        if not uid:
            raise ValueError("user_id không được rỗng.")
        sub = (google_sub or "").strip() or None
        now = created_at or _now_iso()
        with self._write_lock:
            conn = self._get_conn()
            with conn:
                conn.execute(
                    """
                    INSERT INTO users (user_id, google_sub, email, display_name, picture_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        google_sub = COALESCE(excluded.google_sub, users.google_sub),
                        email = CASE WHEN excluded.email != '' THEN excluded.email ELSE users.email END,
                        display_name = CASE WHEN excluded.display_name != '' THEN excluded.display_name ELSE users.display_name END,
                        picture_url = CASE WHEN excluded.picture_url != '' THEN excluded.picture_url ELSE users.picture_url END
                    """,
                    (uid, sub, email or "", display_name or "", picture_url or "", now),
                )
        row = self.get_user(uid)
        assert row is not None
        return row

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        """Lấy thông tin user theo user_id."""
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def get_user_by_google_sub(self, google_sub: str) -> dict[str, Any] | None:
        """Lấy thông tin user theo google_sub."""
        if not google_sub:
            return None
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM users WHERE google_sub = ?", (google_sub,)).fetchone()
        return dict(row) if row else None

    # ── Scan Sessions ──────────────────────────────────────────────────────

    def _row_to_scan_session(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "scan_id": row["scan_id"],
            "owner_user_id": row["owner_user_id"],
            "source_type": row["source_type"],
            "source_label": row["source_label"],
            "commit_sha": row["commit_sha"],
            "mode": row["mode"],
            "members": _json_loads(row["members_json"], []),
            "audit_output": row["audit_output"],
            "hard_flags": _json_loads(row["hard_flags_json"], []),
            "checks": _json_loads(row["checks_json"], {}),
            "missing_required": _json_loads(row["missing_required_json"], []),
            "line_counts": _json_loads(row["line_counts_json"], {}),
            "tracing": _json_loads(row["tracing_json"], {}),
            "created_at": row["created_at"],
        }

    def create_scan_session(
        self,
        owner_user_id: str,
        source_type: str,
        source_label: str,
        audit_output: str,
        *,
        commit_sha: str = "",
        mode: str = "personal",
        members: list[Any] | None = None,
        hard_flags: list[Any] | None = None,
        checks: dict[str, Any] | None = None,
        missing_required: list[str] | None = None,
        line_counts: dict[str, int] | None = None,
        tracing: dict[str, Any] | None = None,
        scan_id: str | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        """Tạo phiên quét mới (chỉ lưu metadata, lỗi cứng, trích dẫn ngắn và audit_output)."""
        now = created_at or _now_iso()
        sid = scan_id or f"scan-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{slugify(source_label, 'repo')[:24]}-{uuid.uuid4().hex[:6]}"
        safe_checks = _strip_source_blobs(checks or {})
        with self._write_lock:
            conn = self._get_conn()
            with conn:
                conn.execute(
                    """
                    INSERT INTO scan_sessions (
                        scan_id, owner_user_id, source_type, source_label, commit_sha,
                        mode, members_json, audit_output, hard_flags_json, checks_json,
                        missing_required_json, line_counts_json, tracing_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sid,
                        owner_user_id,
                        source_type,
                        source_label,
                        commit_sha or "",
                        mode or "personal",
                        _json_dumps(members or []),
                        audit_output or "",
                        _json_dumps(hard_flags or []),
                        _json_dumps(safe_checks),
                        _json_dumps(missing_required or []),
                        _json_dumps(line_counts or {}),
                        _json_dumps(tracing or {}),
                        now,
                    ),
                )
        session = self.get_scan_session(sid)
        assert session is not None
        return session

    def list_scan_sessions(
        self,
        owner_user_id: str,
        limit: int = 50,
        source_label: str | None = None,
    ) -> list[dict[str, Any]]:
        """Liệt kê lịch sử phiên quét của một user, mới nhất trước."""
        conn = self._get_conn()
        if source_label is not None:
            rows = conn.execute(
                """
                SELECT * FROM scan_sessions
                WHERE owner_user_id = ? AND source_label = ?
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?
                """,
                (owner_user_id, source_label, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM scan_sessions
                WHERE owner_user_id = ?
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?
                """,
                (owner_user_id, limit),
            ).fetchall()
        return [self._row_to_scan_session(r) for r in rows]

    def get_scan_session(
        self,
        scan_id: str,
        owner_user_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Lấy chi tiết một phiên quét (tuỳ chọn kiểm tra đúng chủ sở hữu)."""
        conn = self._get_conn()
        if owner_user_id is not None:
            row = conn.execute(
                "SELECT * FROM scan_sessions WHERE scan_id = ? AND owner_user_id = ?",
                (scan_id, owner_user_id),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM scan_sessions WHERE scan_id = ?",
                (scan_id,),
            ).fetchone()
        return self._row_to_scan_session(row) if row else None

    def compare_with_previous_scan(
        self,
        scan_id: str,
        owner_user_id: str | None = None,
    ) -> dict[str, Any]:
        """So sánh lỗi cứng & bậc Bloom của phiên hiện tại với phiên liền trước cùng source_label."""
        conn = self._get_conn()
        if owner_user_id is not None:
            cur_row = conn.execute(
                "SELECT rowid, * FROM scan_sessions WHERE scan_id = ? AND owner_user_id = ?",
                (scan_id, owner_user_id),
            ).fetchone()
        else:
            cur_row = conn.execute(
                "SELECT rowid, * FROM scan_sessions WHERE scan_id = ?",
                (scan_id,),
            ).fetchone()

        if cur_row is None:
            raise ValueError(f"Không tìm thấy scan_id: {scan_id}")

        current = self._row_to_scan_session(cur_row)
        prev_row = conn.execute(
            """
            SELECT * FROM scan_sessions
            WHERE owner_user_id = ?
              AND source_label = ?
              AND scan_id != ?
              AND (created_at < ? OR (created_at = ? AND rowid < ?))
            ORDER BY created_at DESC, rowid DESC
            LIMIT 1
            """,
            (
                current["owner_user_id"],
                current["source_label"],
                current["scan_id"],
                current["created_at"],
                current["created_at"],
                cur_row["rowid"],
            ),
        ).fetchone()

        cur_flags = current["hard_flags"]
        cur_viva = self.list_viva_entries(current["scan_id"])
        cur_blooms = [e["bloom_level"] for e in cur_viva if e["bloom_level"] is not None]
        cur_avg_bloom = round(sum(cur_blooms) / len(cur_blooms), 2) if cur_blooms else None

        if prev_row is None:
            return {
                "has_previous": False,
                "current_scan_id": current["scan_id"],
                "previous_scan_id": None,
                "source_label": current["source_label"],
                "current_flag_count": len(cur_flags),
                "previous_flag_count": None,
                "flag_delta": 0,
                "fixed_flags": [],
                "new_flags": cur_flags,
                "current_avg_bloom": cur_avg_bloom,
                "previous_avg_bloom": None,
                "bloom_delta": None,
            }

        previous = self._row_to_scan_session(prev_row)
        prev_flags = previous["hard_flags"]
        cur_sigs = {_flag_signature(f) for f in cur_flags}
        prev_sigs = {_flag_signature(f) for f in prev_flags}
        fixed_flags = [f for f in prev_flags if _flag_signature(f) not in cur_sigs]
        new_flags = [f for f in cur_flags if _flag_signature(f) not in prev_sigs]

        prev_viva = self.list_viva_entries(previous["scan_id"])
        prev_blooms = [e["bloom_level"] for e in prev_viva if e["bloom_level"] is not None]
        prev_avg_bloom = round(sum(prev_blooms) / len(prev_blooms), 2) if prev_blooms else None
        bloom_delta = (
            round(cur_avg_bloom - prev_avg_bloom, 2)
            if cur_avg_bloom is not None and prev_avg_bloom is not None
            else None
        )

        return {
            "has_previous": True,
            "current_scan_id": current["scan_id"],
            "previous_scan_id": previous["scan_id"],
            "source_label": current["source_label"],
            "current_flag_count": len(cur_flags),
            "previous_flag_count": len(prev_flags),
            "flag_delta": len(cur_flags) - len(prev_flags),
            "fixed_flags": fixed_flags,
            "new_flags": new_flags,
            "current_avg_bloom": cur_avg_bloom,
            "previous_avg_bloom": prev_avg_bloom,
            "bloom_delta": bloom_delta,
        }

    # ── Viva Entries & Bloom Profiles ──────────────────────────────────────

    def _row_to_viva_entry(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "scan_id": row["scan_id"],
            "member_slug": row["member_slug"],
            "member_name": row["member_name"],
            "mode": row["mode"],
            "concept_key": row["concept_key"],
            "question": row["question"],
            "answer": row["answer"],
            "ai_feedback": row["ai_feedback"],
            "bloom_level": row["bloom_level"],
            "draft": _json_loads(row["draft_json"], {}),
            "saved_by_user": bool(row["saved_by_user"]),
            "created_at": row["created_at"],
        }

    def save_viva_entry(
        self,
        scan_id: str,
        member_name: str,
        mode: str,
        *,
        member_slug: str | None = None,
        concept_key: str = "",
        question: str = "",
        answer: str = "",
        ai_feedback: str = "",
        bloom_level: int | None = None,
        draft: dict[str, Any] | None = None,
        saved_by_user: bool | int = 0,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        """Lưu một lượt hỏi vặn / phản biện / tư vấn (nháp chưa tự gộp vào hồ sơ Bloom)."""
        slug = (member_slug or "").strip() or slugify(member_name, "member")
        now = created_at or _now_iso()
        with self._write_lock:
            conn = self._get_conn()
            with conn:
                cur = conn.execute(
                    """
                    INSERT INTO viva_entries (
                        scan_id, member_slug, member_name, mode, concept_key,
                        question, answer, ai_feedback, bloom_level, draft_json,
                        saved_by_user, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        scan_id,
                        slug,
                        member_name,
                        mode,
                        concept_key or "",
                        question or "",
                        answer or "",
                        ai_feedback or "",
                        bloom_level,
                        _json_dumps(draft or {}),
                        1 if saved_by_user else 0,
                        now,
                    ),
                )
                entry_id = cur.lastrowid
        row = conn.execute("SELECT * FROM viva_entries WHERE id = ?", (entry_id,)).fetchone()
        assert row is not None
        return self._row_to_viva_entry(row)

    def list_viva_entries(
        self,
        scan_id: str,
        member_slug: str | None = None,
    ) -> list[dict[str, Any]]:
        """Liệt kê các lượt phỏng vấn của một phiên quét."""
        conn = self._get_conn()
        if member_slug is not None:
            rows = conn.execute(
                """
                SELECT * FROM viva_entries
                WHERE scan_id = ? AND member_slug = ?
                ORDER BY id ASC
                """,
                (scan_id, member_slug),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM viva_entries WHERE scan_id = ? ORDER BY id ASC",
                (scan_id,),
            ).fetchall()
        return [self._row_to_viva_entry(r) for r in rows]

    def _row_to_bloom_item(self, row: sqlite3.Row) -> dict[str, Any]:
        keys = set(row.keys())
        return {
            "owner_user_id": row["owner_user_id"],
            "member_slug": row["member_slug"],
            "concept_key": row["concept_key"],
            "term": row["term"],
            "tag": row["tag"],
            "source_cite": row["source_cite"],
            "source_repo": row["source_repo"] if "source_repo" in keys else "",
            "source_scan_id": row["source_scan_id"] if "source_scan_id" in keys else "",
            "bloom_level": row["bloom_level"],
            "highest_bloom_level": row["highest_bloom_level"],
            "understood_points": _json_loads(row["understood_json"], []),
            "missing_points": _json_loads(row["missing_json"], []),
            "misconceptions": _json_loads(row["misconceptions_json"], []),
            "resolved_misconceptions": _json_loads(row["resolved_misconceptions_json"], []),
            "next_probe": row["next_probe"],
            "prompt": row["prompt"],
            "reference": row["reference"],
            "rubric": row["rubric"],
            "status": row["status"],
            "history": _json_loads(row["history_json"], []),
            "updated_at": row["updated_at"],
        }

    def confirm_bloom_draft(
        self,
        owner_user_id: str,
        member_name_or_slug: str = "",
        draft: dict[str, Any] | None = None,
        *,
        viva_entry_id: int | None = None,
        member_slug: str | None = None,
        question: str = "",
        updated_at: str | None = None,
        scan_id: str | None = None,
        source_repo: str = "",
    ) -> dict[str, Any]:
        """Xác nhận bản nháp Bloom (HITL) và hợp nhất vào bloom_profiles của user."""
        now = updated_at or _now_iso()
        with self._write_lock:
            conn = self._get_conn()
            entry_scan_id: str | None = None
            resolved_slug = (member_slug or "").strip()
            resolved_question = question
            effective_draft: dict[str, Any] = dict(draft) if draft else {}

            with conn:
                if viva_entry_id is not None:
                    entry_row = conn.execute(
                        """
                        SELECT v.*, s.owner_user_id
                        FROM viva_entries v
                        JOIN scan_sessions s ON s.scan_id = v.scan_id
                        WHERE v.id = ?
                        """,
                        (viva_entry_id,),
                    ).fetchone()
                    if entry_row is None:
                        raise ValueError(f"Không tìm thấy viva_entry id={viva_entry_id}")
                    if entry_row["owner_user_id"] != owner_user_id:
                        raise PermissionError("viva_entry không thuộc owner_user_id hiện tại.")
                    entry_scan_id = entry_row["scan_id"]
                    if not resolved_slug:
                        resolved_slug = entry_row["member_slug"]
                    if not resolved_question:
                        resolved_question = entry_row["question"]
                    if not effective_draft:
                        effective_draft = _json_loads(entry_row["draft_json"], {})
                    conn.execute(
                        "UPDATE viva_entries SET saved_by_user = 1 WHERE id = ?",
                        (viva_entry_id,),
                    )

                if not resolved_slug:
                    resolved_slug = slugify(member_name_or_slug, "member")

                concept_key = str(
                    effective_draft.get("concept_key")
                    or slugify(str(effective_draft.get("term") or "general"), "general")
                ).strip()
                if not concept_key:
                    raise ValueError("draft thiếu concept_key.")

                raw_level = effective_draft.get("bloom_level", 0)
                new_level = max(0, min(6, int(raw_level if raw_level is not None else 0)))

                existing_row = conn.execute(
                    """
                    SELECT * FROM bloom_profiles
                    WHERE owner_user_id = ? AND member_slug = ? AND concept_key = ?
                    """,
                    (owner_user_id, resolved_slug, concept_key),
                ).fetchone()

                if existing_row is not None:
                    old = self._row_to_bloom_item(existing_row)
                    highest = max(old["highest_bloom_level"], new_level)
                    understood = _dedup_str_list(
                        old["understood_points"] + list(effective_draft.get("understood_points") or [])
                    )
                    if "missing_points" in effective_draft:
                        raw_missing = _dedup_str_list(effective_draft.get("missing_points"))
                    else:
                        raw_missing = list(old["missing_points"])
                    understood_set = set(understood)
                    missing = [m for m in raw_missing if m not in understood_set]

                    explicit_resolved = _dedup_str_list(effective_draft.get("resolved_misconceptions"))
                    explicit_resolved_set = set(explicit_resolved)
                    if "misconceptions" in effective_draft:
                        active_misconceptions = [
                            m
                            for m in _dedup_str_list(effective_draft.get("misconceptions"))
                            if m not in explicit_resolved_set
                        ]
                    else:
                        active_misconceptions = [
                            m for m in old["misconceptions"] if m not in explicit_resolved_set
                        ]
                    active_set = set(active_misconceptions)
                    auto_resolved = [
                        m for m in old["misconceptions"] if m not in active_set
                    ]
                    resolved_misconceptions = [
                        m
                        for m in _dedup_str_list(
                            old["resolved_misconceptions"] + explicit_resolved + auto_resolved
                        )
                        if m not in active_set
                    ]

                    term = str(effective_draft.get("term") or old["term"])
                    tag = str(effective_draft.get("tag") or old["tag"] or "khai_niem")
                    source_cite = str(effective_draft.get("source_cite") or old["source_cite"])
                    next_probe = str(effective_draft.get("next_probe") or old["next_probe"])
                    prompt_txt = str(effective_draft.get("prompt") or resolved_question or old["prompt"])
                    reference = str(effective_draft.get("reference") or old["reference"])
                    rubric = str(effective_draft.get("rubric") or old["rubric"])
                    history = list(old["history"])
                else:
                    highest = new_level
                    understood = _dedup_str_list(effective_draft.get("understood_points"))
                    understood_set = set(understood)
                    missing = [
                        m
                        for m in _dedup_str_list(effective_draft.get("missing_points"))
                        if m not in understood_set
                    ]
                    explicit_resolved = _dedup_str_list(effective_draft.get("resolved_misconceptions"))
                    explicit_resolved_set = set(explicit_resolved)
                    active_misconceptions = [
                        m
                        for m in _dedup_str_list(effective_draft.get("misconceptions"))
                        if m not in explicit_resolved_set
                    ]
                    active_set = set(active_misconceptions)
                    resolved_misconceptions = [
                        m for m in explicit_resolved if m not in active_set
                    ]
                    term = str(effective_draft.get("term") or concept_key)
                    tag = str(effective_draft.get("tag") or "khai_niem")
                    source_cite = str(effective_draft.get("source_cite") or "")
                    next_probe = str(effective_draft.get("next_probe") or "")
                    prompt_txt = str(effective_draft.get("prompt") or resolved_question or "")
                    reference = str(effective_draft.get("reference") or "")
                    rubric = str(effective_draft.get("rubric") or "")
                    history = []

                explicit_status = effective_draft.get("status")
                if explicit_status in {"needs_review", "mastered"}:
                    status = explicit_status
                elif new_level >= 4 and not active_misconceptions and not missing:
                    status = "mastered"
                else:
                    status = "needs_review"

                resolved_scan_id = (entry_scan_id or scan_id or str(effective_draft.get("source_scan_id") or "")).strip()
                resolved_source_repo = (source_repo or str(effective_draft.get("source_repo") or "")).strip()
                if not resolved_source_repo and resolved_scan_id:
                    s_row = conn.execute(
                        "SELECT source_label FROM scan_sessions WHERE scan_id = ? AND owner_user_id = ?",
                        (resolved_scan_id, owner_user_id),
                    ).fetchone()
                    if s_row is not None:
                        resolved_source_repo = str(s_row["source_label"] or "")

                history.append({
                    "bloom_level": new_level,
                    "timestamp": now,
                    "scan_id": resolved_scan_id or entry_scan_id,
                    "source_repo": resolved_source_repo,
                    "viva_entry_id": viva_entry_id,
                    "resolved_count": len(resolved_misconceptions),
                })

                conn.execute(
                    """
                    INSERT INTO bloom_profiles (
                        owner_user_id, member_slug, concept_key, term, tag, source_cite,
                        source_repo, source_scan_id,
                        bloom_level, highest_bloom_level, understood_json, missing_json,
                        misconceptions_json, resolved_misconceptions_json, next_probe,
                        prompt, reference, rubric, status, history_json, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(owner_user_id, member_slug, concept_key) DO UPDATE SET
                        term = excluded.term,
                        tag = excluded.tag,
                        source_cite = excluded.source_cite,
                        source_repo = CASE WHEN excluded.source_repo != '' THEN excluded.source_repo ELSE bloom_profiles.source_repo END,
                        source_scan_id = CASE WHEN excluded.source_scan_id != '' THEN excluded.source_scan_id ELSE bloom_profiles.source_scan_id END,
                        bloom_level = excluded.bloom_level,
                        highest_bloom_level = excluded.highest_bloom_level,
                        understood_json = excluded.understood_json,
                        missing_json = excluded.missing_json,
                        misconceptions_json = excluded.misconceptions_json,
                        resolved_misconceptions_json = excluded.resolved_misconceptions_json,
                        next_probe = excluded.next_probe,
                        prompt = excluded.prompt,
                        reference = excluded.reference,
                        rubric = excluded.rubric,
                        status = excluded.status,
                        history_json = excluded.history_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        owner_user_id,
                        resolved_slug,
                        concept_key,
                        term,
                        tag,
                        source_cite,
                        resolved_source_repo,
                        resolved_scan_id,
                        new_level,
                        highest,
                        _json_dumps(understood),
                        _json_dumps(missing),
                        _json_dumps(active_misconceptions),
                        _json_dumps(resolved_misconceptions),
                        next_probe,
                        prompt_txt,
                        reference,
                        rubric,
                        status,
                        _json_dumps(history),
                        now,
                    ),
                )

            row = conn.execute(
                """
                SELECT * FROM bloom_profiles
                WHERE owner_user_id = ? AND member_slug = ? AND concept_key = ?
                """,
                (owner_user_id, resolved_slug, concept_key),
            ).fetchone()
            assert row is not None
            return self._row_to_bloom_item(row)

    def update_card_status(
        self,
        owner_user_id: str,
        member_name_or_slug: str,
        concept_key: str,
        status: str,
        *,
        member_slug: str | None = None,
    ) -> dict[str, Any] | None:
        """Cập nhật trạng thái thẻ ôn ('needs_review' | 'mastered') trên web."""
        if status not in {"needs_review", "mastered"}:
            raise ValueError("status phải là 'needs_review' hoặc 'mastered'.")
        slug = (member_slug or "").strip() or slugify(member_name_or_slug, "member")
        now = _now_iso()
        with self._write_lock:
            conn = self._get_conn()
            with conn:
                conn.execute(
                    """
                    UPDATE bloom_profiles
                    SET status = ?, updated_at = ?
                    WHERE owner_user_id = ? AND member_slug = ? AND concept_key = ?
                    """,
                    (status, now, owner_user_id, slug, concept_key),
                )
            row = conn.execute(
                """
                SELECT * FROM bloom_profiles
                WHERE owner_user_id = ? AND member_slug = ? AND concept_key = ?
                """,
                (owner_user_id, slug, concept_key),
            ).fetchone()
        return self._row_to_bloom_item(row) if row else None

    def get_user_bloom_profile(
        self,
        owner_user_id: str,
        member_name_or_slug: str,
        *,
        member_slug: str | None = None,
    ) -> dict[str, Any]:
        """Lấy hồ sơ Bloom xuyên suốt của thành viên theo owner_user_id."""
        slug = (member_slug or "").strip() or slugify(member_name_or_slug, "member")
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT * FROM bloom_profiles
            WHERE owner_user_id = ? AND member_slug = ?
            ORDER BY bloom_level ASC, updated_at DESC
            """,
            (owner_user_id, slug),
        ).fetchall()
        concepts = [self._row_to_bloom_item(r) for r in rows]
        total = len(concepts)
        mastered = sum(1 for c in concepts if c["status"] == "mastered")
        needs_review = total - mastered
        avg_bloom = round(sum(c["bloom_level"] for c in concepts) / total, 2) if total else 0.0
        max_bloom = max((c["highest_bloom_level"] for c in concepts), default=0)
        misconception_count = sum(len(c["misconceptions"]) for c in concepts)
        return {
            "owner_user_id": owner_user_id,
            "member_slug": slug,
            "concepts": concepts,
            "summary": {
                "total_concepts": total,
                "mastered_count": mastered,
                "needs_review_count": needs_review,
                "avg_bloom": avg_bloom,
                "max_bloom": max_bloom,
                "misconception_count": misconception_count,
            },
        }

    def list_all_bloom_concepts(self, owner_user_id: str) -> list[dict[str, Any]]:
        """Lấy toàn bộ khái niệm Bloom mọi repo của tài khoản (tự khớp source_repo cho dữ liệu cũ)."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM bloom_profiles WHERE owner_user_id = ? ORDER BY bloom_level ASC, updated_at DESC",
            (owner_user_id,),
        ).fetchall()
        concepts = [self._row_to_bloom_item(r) for r in rows]
        scan_map = {
            r["scan_id"]: r["source_label"]
            for r in conn.execute(
                "SELECT scan_id, source_label FROM scan_sessions WHERE owner_user_id = ?",
                (owner_user_id,),
            ).fetchall()
        }
        for item in concepts:
            if not item.get("source_repo"):
                cand_scan = item.get("source_scan_id") or ""
                if not cand_scan and item.get("history"):
                    last_hist = item["history"][-1]
                    if isinstance(last_hist, dict):
                        cand_scan = str(last_hist.get("scan_id") or "")
                        if last_hist.get("source_repo"):
                            item["source_repo"] = str(last_hist["source_repo"])
                if not item.get("source_repo") and cand_scan and cand_scan in scan_map:
                    item["source_repo"] = scan_map[cand_scan]
                if not item.get("source_scan_id") and cand_scan:
                    item["source_scan_id"] = cand_scan
        return concepts

    def summarize_profile_for_prompt(
        self,
        owner_user_id: str,
        member_name_or_slug: str,
        max_items: int = 12,
    ) -> str:
        """Tạo chuỗi tóm tắt ngắn gọn BLOOM_MEMORY nạp vào VIVA_COACH."""
        profile = self.get_user_bloom_profile(owner_user_id, member_name_or_slug)
        concepts = profile["concepts"]
        if not concepts:
            return "(Chưa có lịch sử Bloom trước đó — bắt đầu đánh giá từ nền tảng L1–L2.)"

        lines: list[str] = []
        prioritized = sorted(
            concepts,
            key=lambda c: (
                0 if (c["bloom_level"] <= 1 or c["misconceptions"]) else (1 if c["bloom_level"] <= 3 else 2),
                c["bloom_level"],
            ),
        )[:max_items]
        for item in prioritized:
            level = item["bloom_level"]
            cite = f" [{item['source_cite']}]" if item["source_cite"] else ""
            if level >= 4 and not item["misconceptions"] and not item["missing_points"]:
                lines.append(f"- ĐÃ VỮNG L{level} ({item['concept_key']}{cite}): {item['term']} [bỏ qua không hỏi lại]")
            else:
                mis = "; ".join(item["misconceptions"][:2]) or "không"
                miss = "; ".join(item["missing_points"][:2]) or "không"
                lines.append(
                    f"- CẦN NÂNG L{level}->L{min(6, level + 1)} ({item['concept_key']}{cite}): "
                    f"{item['term']} | ngộ nhận: {mis} | thiếu: {miss}"
                )
        return "\n".join(lines)

    # ── GitHub Cache ───────────────────────────────────────────────────────

    def get_cached_github(
        self,
        cache_key: str,
        now_ts: int | None = None,
    ) -> dict[str, Any] | None:
        """Đọc cache metadata GitHub nếu chưa hết hạn TTL."""
        key = (cache_key or "").strip().lower()
        if not key:
            return None
        now = int(time.time()) if now_ts is None else int(now_ts)
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM github_cache WHERE cache_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        if int(row["expires_at"]) <= now:
            with self._write_lock:
                with conn:
                    conn.execute("DELETE FROM github_cache WHERE cache_key = ?", (key,))
            return None
        return {
            "cache_key": row["cache_key"],
            "commit_sha": row["commit_sha"],
            "payload": _json_loads(row["payload_json"], {}),
            "expires_at": int(row["expires_at"]),
        }

    def set_cached_github(
        self,
        cache_key: str,
        commit_sha: str,
        payload: dict[str, Any],
        ttl_seconds: int = 300,
        now_ts: int | None = None,
    ) -> None:
        """Lưu cache metadata GitHub (tự động lọc bỏ mã nguồn thô trước khi ghi DB)."""
        key = (cache_key or "").strip().lower()
        if not key:
            raise ValueError("cache_key không được rỗng.")
        now = int(time.time()) if now_ts is None else int(now_ts)
        expires_at = now + max(1, int(ttl_seconds))
        sanitized = _strip_source_blobs(payload or {})
        with self._write_lock:
            conn = self._get_conn()
            with conn:
                conn.execute(
                    """
                    INSERT INTO github_cache (cache_key, commit_sha, payload_json, expires_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(cache_key) DO UPDATE SET
                        commit_sha = excluded.commit_sha,
                        payload_json = excluded.payload_json,
                        expires_at = excluded.expires_at
                    """,
                    (key, commit_sha or "", _json_dumps(sanitized), expires_at),
                )

    # ── Rate Limiting ──────────────────────────────────────────────────────

    def check_and_increment_rate_limit(
        self,
        bucket_key: str,
        limit: int,
        window_seconds: int,
        now_ts: int | None = None,
    ) -> tuple[bool, int, int]:
        """Kiểm tra và tăng bộ đếm giới hạn tần suất (atomic).

        Trả về: (allowed, remaining, retry_after_seconds).
        """
        key = (bucket_key or "").strip()
        if not key:
            raise ValueError("bucket_key không được rỗng.")
        win = max(1, int(window_seconds))
        lim = int(limit)
        now = int(time.time()) if now_ts is None else int(now_ts)

        with self._write_lock:
            conn = self._get_conn()
            with conn:
                row = conn.execute(
                    "SELECT window_start, count FROM rate_limit_events WHERE bucket_key = ?",
                    (key,),
                ).fetchone()

                if row is None or (now - int(row["window_start"])) >= win:
                    if lim <= 0:
                        conn.execute(
                            """
                            INSERT INTO rate_limit_events (bucket_key, window_start, count)
                            VALUES (?, ?, 0)
                            ON CONFLICT(bucket_key) DO UPDATE SET
                                window_start = excluded.window_start,
                                count = 0
                            """,
                            (key, now),
                        )
                        return (False, 0, win)
                    conn.execute(
                        """
                        INSERT INTO rate_limit_events (bucket_key, window_start, count)
                        VALUES (?, ?, 1)
                        ON CONFLICT(bucket_key) DO UPDATE SET
                            window_start = excluded.window_start,
                            count = 1
                        """,
                        (key, now),
                    )
                    return (True, lim - 1, win)

                window_start = int(row["window_start"])
                current_count = int(row["count"])
                retry_after = max(1, win - (now - window_start))
                if current_count >= lim:
                    return (False, 0, retry_after)

                new_count = current_count + 1
                conn.execute(
                    "UPDATE rate_limit_events SET count = ? WHERE bucket_key = ?",
                    (new_count, key),
                )
                return (True, max(0, lim - new_count), retry_after)
