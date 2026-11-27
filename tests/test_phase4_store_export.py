"""Phase 4 Tests — SQLite WAL Store (6 tables + concurrency) & 4 Exporters."""
import json
import os
import sqlite3
import tempfile
import threading
import unittest

from codebase.db import DEFAULT_DB_PATH, RepoKsvDB, slugify
from codebase.exporters import (
    export_anki_tsv,
    export_etude_pack_json,
    export_markdown_guide,
    export_session_json,
)


class TestPhase4StoreAndExport(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "repoksv_test.db")
        self.db = RepoKsvDB(self.db_path)

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_default_path_and_schema_wal_pragmas(self) -> None:
        self.assertTrue(DEFAULT_DB_PATH.replace("\\", "/").endswith(".study_logs/repoksv.db"))
        conn = sqlite3.connect(self.db_path)
        try:
            mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
            self.assertEqual(mode.lower(), "wal")
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            self.assertTrue(
                {
                    "users",
                    "scan_sessions",
                    "viva_entries",
                    "bloom_profiles",
                    "github_cache",
                    "rate_limit_events",
                }.issubset(tables)
            )
        finally:
            conn.close()

        # Verify connection pragmas inside RepoKsvDB
        db_conn = self.db._get_conn()
        self.assertEqual(db_conn.execute("PRAGMA foreign_keys;").fetchone()[0], 1)
        self.assertEqual(db_conn.execute("PRAGMA busy_timeout;").fetchone()[0], 5000)

    def test_users_and_scan_sessions_compare(self) -> None:
        u1 = self.db.upsert_user("u-tuan", google_sub="", email="tuan@example.com", display_name="Tuấn")
        u2 = self.db.upsert_user("u-vy", google_sub="", email="vy@example.com", display_name="Vỹ")
        self.assertIsNone(u1["google_sub"])
        self.assertIsNone(u2["google_sub"])

        # Foreign key enforcement
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.create_scan_session("missing-user", "local", "S04", "output")

        s1 = self.db.create_scan_session(
            "u-tuan",
            "github",
            "team/repo",
            "Lần 1 phát hiện GIT-FORK-PR",
            commit_sha="aaa111",
            mode="team",
            members=[{"name": "Tuấn"}, {"name": "Vỹ"}],
            hard_flags=[
                {"rule_id": "GIT-FORK-PR", "file": "TEAMS.md", "line": 1, "detail": "PR nhầm upstream"},
                {"rule_id": "PENALTY-KEY", "file": ".env", "line": 1, "detail": "Lộ .env"},
            ],
            checks={"public_access": True, "git_fork_pr": False, "files_content": {"secret": "MUST_NOT_SAVE"}},
            line_counts={"spec.md": 120},
            created_at="2026-11-28T01:00:00Z",
        )
        # Privacy: raw source blob must be stripped
        self.assertNotIn("files_content", s1["checks"])

        self.db.save_viva_entry(
            s1["scan_id"], "Tuấn", "defense", concept_key="git-fork", bloom_level=1
        )

        s2 = self.db.create_scan_session(
            "u-tuan",
            "github",
            "team/repo",
            "Lần 2 đã đóng PR",
            commit_sha="bbb222",
            mode="team",
            members=[{"name": "Tuấn"}, {"name": "Vỹ"}],
            hard_flags=[
                {"rule_id": "PENALTY-KEY", "file": ".env", "line": 1, "detail": "Lộ .env"},
            ],
            created_at="2026-11-28T02:00:00Z",
        )
        self.db.save_viva_entry(
            s2["scan_id"], "Tuấn", "defense", concept_key="git-fork", bloom_level=3
        )

        # Ownership isolation
        self.assertIsNone(self.db.get_scan_session(s2["scan_id"], owner_user_id="u-vy"))
        self.assertIsNotNone(self.db.get_scan_session(s2["scan_id"], owner_user_id="u-tuan"))

        sessions = self.db.list_scan_sessions("u-tuan")
        self.assertEqual([s["scan_id"] for s in sessions], [s2["scan_id"], s1["scan_id"]])

        diff = self.db.compare_with_previous_scan(s2["scan_id"], owner_user_id="u-tuan")
        self.assertTrue(diff["has_previous"])
        self.assertEqual(diff["previous_scan_id"], s1["scan_id"])
        self.assertEqual(diff["flag_delta"], -1)
        self.assertEqual(len(diff["fixed_flags"]), 1)
        self.assertEqual(diff["fixed_flags"][0]["rule_id"], "GIT-FORK-PR")
        self.assertEqual(diff["bloom_delta"], 2.0)

    def test_bloom_hitl_merge_l0_to_l3_and_card_status(self) -> None:
        self.db.upsert_user("u-tuan", display_name="Phạm Quang Tuấn")
        s1 = self.db.create_scan_session("u-tuan", "local", "S04", "Audit S04")

        # Save draft entry (NOT confirmed yet -> bloom_profiles must remain empty)
        draft_l0 = {
            "concept_key": "git-fork-pr",
            "term": "Rủi ro GIT-FORK-PR",
            "tag": "quy_che",
            "source_cite": "spec.md:L18",
            "bloom_level": 0,
            "understood_points": ["Biết cần nộp qua GitHub"],
            "missing_points": ["Phân biệt fork upstream PR và repo độc lập"],
            "misconceptions": ["Nghĩ mở PR về repo gốc BTC là đúng quy trình"],
            "resolved_misconceptions": [],
            "next_probe": "Tại sao mở PR về repo đề lại làm lộ bài và dính GIT-FORK-PR?",
            "reference": "Không mở PR về repo gốc BTC; tách repo riêng hoặc giữ nhánh sạch.",
            "rubric": "Nêu cơ chế lộ bài khi PR upstream và cách kiểm tra parent/pulls.",
        }
        entry1 = self.db.save_viva_entry(
            s1["scan_id"],
            "Phạm Quang Tuấn",
            "defense",
            concept_key="git-fork-pr",
            question="Giải thích GIT-FORK-PR?",
            answer="Mở PR về repo gốc BTC để nộp bài.",
            ai_feedback="Level 0/6",
            bloom_level=0,
            draft=draft_l0,
            saved_by_user=0,
        )
        self.assertFalse(entry1["saved_by_user"])
        self.assertEqual(self.db.get_user_bloom_profile("u-tuan", "Phạm Quang Tuấn")["concepts"], [])

        # Confirm L0 draft
        p1 = self.db.confirm_bloom_draft("u-tuan", "Phạm Quang Tuấn", viva_entry_id=entry1["id"])
        self.assertEqual(p1["bloom_level"], 0)
        self.assertEqual(p1["highest_bloom_level"], 0)
        self.assertEqual(p1["misconceptions"], ["Nghĩ mở PR về repo gốc BTC là đúng quy trình"])
        self.assertEqual(p1["resolved_misconceptions"], [])
        self.assertEqual(len(p1["history"]), 1)

        entries_after_confirm = self.db.list_viva_entries(s1["scan_id"])
        self.assertTrue(entries_after_confirm[0]["saved_by_user"])

        # Re-defense L3 fixing the misconception (even without repeating resolved_misconceptions explicitly)
        draft_l3 = {
            "concept_key": "git-fork-pr",
            "term": "Rủi ro GIT-FORK-PR",
            "source_cite": "spec.md:L18",
            "bloom_level": 3,
            "understood_points": ["Phân biệt fork upstream PR và repo độc lập"],
            "missing_points": [],
            "misconceptions": [],
            "next_probe": "Nếu user chỉ đưa link fork nhưng đã đóng PR, check gì thêm?",
        }
        entry2 = self.db.save_viva_entry(
            s1["scan_id"],
            "Phạm Quang Tuấn",
            "defense",
            concept_key="git-fork-pr",
            question=draft_l0["next_probe"],
            answer="PR vào repo gốc làm mọi đội khác thấy bài trên GitHub.",
            ai_feedback="Level 3/6",
            bloom_level=3,
            draft=draft_l3,
        )
        p2 = self.db.confirm_bloom_draft("u-tuan", "Phạm Quang Tuấn", viva_entry_id=entry2["id"])
        self.assertEqual(p2["bloom_level"], 3)
        self.assertEqual(p2["highest_bloom_level"], 3)
        self.assertEqual(p2["misconceptions"], [])
        self.assertEqual(
            p2["resolved_misconceptions"],
            ["Nghĩ mở PR về repo gốc BTC là đúng quy trình"],
        )
        self.assertEqual(
            p2["understood_points"],
            ["Biết cần nộp qua GitHub", "Phân biệt fork upstream PR và repo độc lập"],
        )
        self.assertEqual(p2["missing_points"], [])
        self.assertEqual(len(p2["history"]), 2)

        # Card status toggle & prompt summary
        updated = self.db.update_card_status("u-tuan", "Phạm Quang Tuấn", "git-fork-pr", "mastered")
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["status"], "mastered")
        with self.assertRaises(ValueError):
            self.db.update_card_status("u-tuan", "Phạm Quang Tuấn", "git-fork-pr", "invalid")

        summary = self.db.summarize_profile_for_prompt("u-tuan", "Phạm Quang Tuấn")
        self.assertIn("git-fork-pr", summary)

    def test_github_cache_and_rate_limit(self) -> None:
        self.db.set_cached_github(
            "Owner/Repo",
            "sha123",
            {"public": True, "files_content": {"a.py": "secret code"}},
            ttl_seconds=60,
            now_ts=1000,
        )
        hit = self.db.get_cached_github("owner/repo", now_ts=1030)
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit["commit_sha"], "sha123")
        self.assertNotIn("files_content", hit["payload"])
        self.assertIsNone(self.db.get_cached_github("owner/repo", now_ts=1060))

        # Rate limit: 3 per 60s
        self.assertEqual(self.db.check_and_increment_rate_limit("ip:1.2.3.4:scan", 3, 60, now_ts=100), (True, 2, 60))
        self.assertEqual(self.db.check_and_increment_rate_limit("ip:1.2.3.4:scan", 3, 60, now_ts=110), (True, 1, 50))
        self.assertEqual(self.db.check_and_increment_rate_limit("ip:1.2.3.4:scan", 3, 60, now_ts=120), (True, 0, 40))
        allowed, rem, retry = self.db.check_and_increment_rate_limit("ip:1.2.3.4:scan", 3, 60, now_ts=130)
        self.assertFalse(allowed)
        self.assertEqual(rem, 0)
        self.assertEqual(retry, 30)
        # Window reset
        self.assertEqual(self.db.check_and_increment_rate_limit("ip:1.2.3.4:scan", 3, 60, now_ts=160), (True, 2, 60))

    def test_four_exporters_and_path_traversal(self) -> None:
        self.assertNotIn("..", slugify("../../etc/passwd"))
        self.assertNotIn("/", slugify("a/b\\c"))

        self.db.upsert_user("u1", display_name="Tuấn")
        session = self.db.create_scan_session(
            "u1",
            "github",
            "phamtuan2xx3-alt/K5-Day15-L3B-Free2Play",
            "Audit ok",
            hard_flags=[{"rule_id": "PENALTY-KEY", "file": ".env", "line": 1, "detail": "Không commit .env"}],
        )
        self.db.confirm_bloom_draft(
            "u1",
            "../../Phạm Quang Tuấn",
            {
                "concept_key": "xss-safe",
                "term": "Chống XSS\t& Injection",
                "tag": "bao_mat",
                "source_cite": "codebase/tools.py:L12",
                "bloom_level": 1,
                "missing_points": ["Escape HTML\ndòng mới"],
                "misconceptions": ["Dùng <script>alert(1)</script> trực tiếp"],
                "next_probe": "Tại sao không dùng innerHTML?",
                "reference": "Escape HTML và bọc <submission_data_untrusted>.",
            },
        )
        self.db.confirm_bloom_draft(
            "u1",
            "../../Phạm Quang Tuấn",
            {
                "concept_key": "wal-mode",
                "term": "SQLite WAL",
                "source_cite": "codebase/db.py:L01",
                "bloom_level": 2,
                "understood_points": ["Đọc song song không chặn ghi"],
                "missing_points": ["Cấu hình busy_timeout=5000"],
                "next_probe": "Khi nào WAL cần busy_timeout?",
                "reference": "WAL cho phép concurrent readers + 1 writer.",
            },
        )
        self.db.confirm_bloom_draft(
            "u1",
            "../../Phạm Quang Tuấn",
            {
                "concept_key": "no-auto-grade",
                "term": "NO-AUTO-GRADE",
                "source_cite": "spec.md:L120",
                "bloom_level": 5,
                "understood_points": ["Chặn /100"],
                "missing_points": [],
                "misconceptions": [],
                "reference": "Không tự chấm /100.",
            },
        )
        profile = self.db.get_user_bloom_profile("u1", "../../Phạm Quang Tuấn")
        viva = [
            self.db.save_viva_entry(
                session["scan_id"], "../../Phạm Quang Tuấn", "defense", concept_key="xss-safe", bloom_level=1
            )
        ]

        # 1. Anki TSV
        anki_name, anki_txt = export_anki_tsv(session, "../../Phạm Quang Tuấn", profile)
        self.assertTrue(anki_name.endswith(".tsv"))
        self.assertNotIn("..", anki_name)
        self.assertNotIn("/", anki_name)
        anki_lines = anki_txt.strip().splitlines()
        self.assertEqual(anki_lines[0], "#separator:tab")
        self.assertEqual(anki_lines[1], "#html:true")
        self.assertEqual(anki_lines[2], "#tags column:3")
        card_rows = anki_lines[3:]
        self.assertEqual(len(card_rows), 2)  # L1 and L2 included; clean L5 excluded
        for row in card_rows:
            self.assertEqual(len(row.split("\t")), 3)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", anki_txt)
        self.assertIn("<br>", anki_txt)

        # 2. Markdown guide
        md_name, md_txt = export_markdown_guide(session, "../../Phạm Quang Tuấn", profile)
        self.assertTrue(md_name.startswith("study-guide-") and md_name.endswith(".md"))
        self.assertNotIn("..", md_name)
        self.assertIn("Nhóm 1: L0–L1", md_txt)
        self.assertIn("Nhóm 2: L2", md_txt)
        self.assertIn("Nhóm 3: L3+", md_txt)

        # 3. Etude pack JSON
        etude_name, etude_txt = export_etude_pack_json(session, "../../Phạm Quang Tuấn", profile)
        self.assertTrue(etude_name.startswith("study-pack-") and etude_name.endswith(".pack.json"))
        self.assertNotIn("..", etude_name)
        pack = json.loads(etude_txt)
        self.assertEqual(pack["etude"], "pack/1")
        self.assertGreaterEqual(len(pack["decks"]), 1)
        self.assertIn("BLOOM", pack["decks"][0]["instructions"].upper())
        self.assertEqual(len(pack["items"]), 2)
        for item in pack["items"]:
            self.assertEqual(item["type"], "free")
            self.assertTrue(item["fields"]["prompt"])
            self.assertTrue(item["fields"]["reference"])

        # 4. Session JSON
        sess_name, sess_txt = export_session_json(session, viva)
        self.assertTrue(sess_name.startswith("session-") and sess_name.endswith(".json"))
        sess_obj = json.loads(sess_txt)
        self.assertEqual(sess_obj["scan_session"]["scan_id"], session["scan_id"])
        self.assertEqual(len(sess_obj["viva_entries"]), 1)

        # Fallback 1: all concepts mastered (L5) -> still exports review cards instead of empty
        mastered_only = {
            "concepts": [c for c in profile["concepts"] if c["bloom_level"] >= 5]
        }
        _, anki_mastered = export_anki_tsv(session, "Tuấn", mastered_only)
        self.assertEqual(len(anki_mastered.strip().splitlines()), 4)  # 3 header lines + 1 fallback card

        # Fallback 2: empty profile -> generates cards from session.hard_flags
        _, etude_empty = export_etude_pack_json(session, "Tuấn", {"concepts": []})
        pack_empty = json.loads(etude_empty)
        self.assertEqual(pack_empty["etude"], "pack/1")
        self.assertEqual(len(pack_empty["items"]), 1)
        self.assertEqual(pack_empty["items"][0]["type"], "free")

    def test_concurrency_15_threads_wal_no_locked_errors(self) -> None:
        self.db.upsert_user("u-load", display_name="Load Tester")
        base_scan = self.db.create_scan_session("u-load", "local", "S01", "Seed scan")

        errors: list[BaseException] = []
        barrier = threading.Barrier(15)

        def worker(tid: int) -> None:
            try:
                barrier.wait(timeout=10)
                for step in range(5):
                    scan = self.db.create_scan_session(
                        "u-load",
                        "local",
                        f"S{(tid % 5) + 1:02d}",
                        f"Thread {tid} step {step}",
                    )
                    entry = self.db.save_viva_entry(
                        scan["scan_id"],
                        f"Member {tid}",
                        "defense",
                        concept_key=f"concept-{step}",
                        bloom_level=min(6, step),
                        draft={
                            "concept_key": f"concept-{step}",
                            "term": f"Term {step}",
                            "bloom_level": min(6, step),
                            "understood_points": [f"ok-{tid}-{step}"],
                        },
                    )
                    self.db.confirm_bloom_draft(
                        "u-load", f"Member {tid}", viva_entry_id=entry["id"]
                    )
                    self.db.get_user_bloom_profile("u-load", f"Member {tid}")
                    self.db.list_scan_sessions("u-load", limit=5)
                    self.db.set_cached_github(f"org/repo-{tid}", f"sha-{step}", {"ok": True})
                    self.db.get_cached_github(f"org/repo-{tid}")
                    self.db.check_and_increment_rate_limit(f"user:u-load:t{tid}", 10, 60)
                self.db.get_scan_session(base_scan["scan_id"])
            except BaseException as exc:  # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(15)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
            self.assertFalse(t.is_alive(), "Worker thread timed out")

        self.assertEqual(errors, [], f"Concurrent SQLite errors: {errors}")
        all_scans = self.db.list_scan_sessions("u-load", limit=200)
        self.assertEqual(len(all_scans), 1 + 15 * 5)


if __name__ == "__main__":
    unittest.main()
