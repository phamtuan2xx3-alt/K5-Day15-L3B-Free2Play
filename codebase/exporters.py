"""4 Bộ Export đa định dạng cho RepoKSV — 100% Python stdlib, chống path traversal.

Hỗ trợ 4 định dạng theo docs/tech-spec-huong-1-2.md §6.2:
    1. export_anki_tsv       -> Anki 2.1+ (.tsv 3 cột: Front, Back, Tags)
    2. export_markdown_guide -> Tài liệu học nhanh (.md gom nhóm L0-L1 -> L2 -> L3+)
    3. export_etude_pack_json-> Gói thẻ tự luận chuẩn "etude": "pack/1" (.pack.json)
    4. export_session_json   -> Bản sao lưu đầy đủ phiên quét + viva_entries (.json)
"""
from __future__ import annotations

import html
import json
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

BLOOM_INSTRUCTIONS_VI = (
    "Bạn là Giám khảo ảo & Mentor phản biện hackathon AI20K. Chấm câu trả lời của học viên "
    "dựa chặt vào Reference và Rubric của thẻ, đối chiếu số liệu và trích dẫn file:Lxx có thật.\n"
    "NGUYÊN TẮC: Không chấp nhận học vẹt từ khóa; không xu nịnh; giữ cứng NO-AUTO-GRADE (/100).\n"
    "THANG BLOOM 6 BẬC: L1 Remember (nhớ định nghĩa) -> L2 Understand (diễn đạt Feynman & phân biệt cặp dễ nhầm) "
    "-> L3 Apply (đặt đúng vào luồng hệ thống) -> L4 Analyze (trade-off & failure mode) "
    "-> L5 Evaluate (chốt bằng chứng định lượng file:Lxx) -> L6 Create (thiết kế đầu-cuối kèm guardrails & HITL)."
)

BLOOM_LABELS = {
    0: "L0 — Chưa nắm / Lệch căn cứ",
    1: "L1 — Remember (Nhớ mặt chữ)",
    2: "L2 — Understand (Feynman)",
    3: "L3 — Apply (Thực chiến)",
    4: "L4 — Analyze (Trade-off)",
    5: "L5 — Evaluate (Bằng chứng)",
    6: "L6 — Create (Thiết kế hệ thống)",
}


def slugify(text: str, default: str = "export") -> str:
    """Chuẩn hoá tên file/thành viên thành slug an toàn, chặn path traversal (.., /, \\)."""
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


def _extract_concepts(profile: Any) -> list[dict[str, Any]]:
    """Chuẩn hoá tham số profile (dict có 'concepts', dict theo key, hoặc list) về list[dict]."""
    if isinstance(profile, dict):
        if isinstance(profile.get("concepts"), list):
            return [dict(c) for c in profile["concepts"] if isinstance(c, dict)]
        if isinstance(profile.get("items"), list):
            return [dict(c) for c in profile["items"] if isinstance(c, dict)]
        items = []
        for k, v in profile.items():
            if isinstance(v, dict):
                entry = dict(v)
                entry.setdefault("concept_key", k)
                items.append(entry)
        return items
    if isinstance(profile, list):
        return [dict(c) for c in profile if isinstance(c, dict)]
    return []


def _fallback_cards_from_session(session: dict[str, Any]) -> list[dict[str, Any]]:
    """Tạo thẻ ôn fallback từ hard_flags của session khi user chưa có lịch sử Bloom."""
    flags = session.get("hard_flags") or []
    cards: list[dict[str, Any]] = []
    for idx, flag in enumerate(flags, 1):
        if isinstance(flag, dict):
            rule_id = str(flag.get("rule_id") or f"FLAG-{idx}")
            file_name = str(flag.get("file") or "repo")
            line_no = flag.get("line")
            cite = f"{file_name}:L{int(line_no):02d}" if isinstance(line_no, int) else file_name
            detail = str(flag.get("detail") or "Cần kiểm tra lại lỗi cứng này.")
        else:
            rule_id = f"FLAG-{idx}"
            cite = str(session.get("source_label") or "repo")
            detail = str(flag)
        cards.append({
            "concept_key": slugify(f"{rule_id}-{idx}", f"flag-{idx}"),
            "term": f"Lỗi cứng {rule_id}",
            "tag": "loi_cung",
            "source_cite": cite,
            "bloom_level": 1,
            "understood_points": [],
            "missing_points": [detail],
            "misconceptions": [],
            "resolved_misconceptions": [],
            "next_probe": f"Vì sao `{rule_id}` tại `{cite}` lại vi phạm quy chế và cách khắc phục đúng?",
            "prompt": f"Giải thích lỗi `{rule_id}` tại `{cite}` và cách khắc phục đạt chuẩn.",
            "reference": detail,
            "rubric": f"Nêu đúng nguyên nhân lỗi {rule_id} tại {cite} và phương án sửa không vi phạm quy chế.",
            "status": "needs_review",
        })
    return cards


def _select_study_concepts(session: dict[str, Any], profile: Any) -> list[dict[str, Any]]:
    """Lọc các mục cần ôn (L0-L2 hoặc còn misconceptions/missing_points) kèm fallback hợp lý."""
    concepts = _extract_concepts(profile)
    if not concepts:
        return _fallback_cards_from_session(session)

    weak = [
        c
        for c in concepts
        if int(c.get("bloom_level", 0)) <= 2
        or bool(c.get("misconceptions"))
        or bool(c.get("missing_points"))
    ]
    target = weak if weak else concepts
    return sorted(target, key=lambda c: int(c.get("bloom_level", 0)))


def _sanitize_tsv_cell(text: str) -> str:
    """Xoá tab/xuống dòng thô và chặn CSV/TSV formula injection (=, +, -, @)."""
    cleaned = str(text or "").replace("\t", "    ")
    cleaned = cleaned.replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")
    if cleaned.lstrip().startswith(("=", "+", "-", "@")):
        cleaned = "'" + cleaned
    return cleaned


def _tsv_cell(text: str) -> str:
    """Escape HTML, chặn formula injection và giữ nguyên 3 cột TSV."""
    escaped = html.escape(str(text or ""), quote=True)
    return _sanitize_tsv_cell(escaped)


def _format_card_front(item: dict[str, Any], source_label: str) -> str:
    term = str(item.get("term") or item.get("concept_key") or "Khái niệm").strip()
    cite = str(item.get("source_cite") or source_label or "").strip()
    level = int(item.get("bloom_level", 0))
    probe = str(item.get("next_probe") or item.get("prompt") or "").strip()
    parts = [f"<b>{term}</b> (Bloom L{level})"]
    if cite:
        parts.append(f"<i>Nguồn: {cite}</i>")
    if probe:
        parts.append(probe)
    else:
        parts.append(f"Hãy tự giải thích cơ chế và bằng chứng của `{term}` theo Feynman.")
    return "\n".join(parts)


def _format_card_back(item: dict[str, Any]) -> str:
    parts: list[str] = []
    ref = str(item.get("reference") or "").strip()
    if ref:
        parts.append(f"<b>Bản chất / Reference:</b> {ref}")
    understood = item.get("understood_points") or []
    if understood:
        parts.append("<b>Đã nắm:</b> " + "; ".join(str(x) for x in understood))
    missing = item.get("missing_points") or []
    if missing:
        parts.append("<b>Còn thiếu:</b> " + "; ".join(str(x) for x in missing))
    misconceptions = item.get("misconceptions") or []
    if misconceptions:
        parts.append("<b>Ngộ nhận cần tránh:</b> " + "; ".join(str(x) for x in misconceptions))
    if not parts:
        parts.append("Đối chiếu lại file:Lxx tương ứng trong hồ sơ nộp.")
    return "\n".join(parts)


def export_anki_tsv(
    session: dict[str, Any],
    user_name: str,
    profile: Any,
) -> tuple[str, str]:
    """Xuất bộ thẻ ôn Anki 2.1+ (.tsv) gồm 3 cột Front\\tBack\\tTags."""
    user_slug = slugify(user_name, "user")
    repo_slug = slugify(str(session.get("source_label") or "session"), "session")
    filename = f"anki-{user_slug}-{repo_slug}.tsv"

    lines = [
        "#separator:tab",
        "#html:true",
        "#tags column:3",
    ]
    source_label = str(session.get("source_label") or "")
    cards = _select_study_concepts(session, profile)
    for item in cards:
        front = _tsv_cell(_format_card_front(item, source_label))
        back = _tsv_cell(_format_card_back(item))
        level = int(item.get("bloom_level", 0))
        tag_slug = slugify(str(item.get("tag") or "khai_niem"), "khai-niem")
        concept_slug = slugify(str(item.get("concept_key") or "concept"), "concept")
        tags = f"repoksv bloom-L{level} {tag_slug} {concept_slug}"
        if repo_slug:
            tags = f"{tags} repo-{repo_slug}"
        lines.append(f"{front}\t{back}\t{_sanitize_tsv_cell(tags)}")

    return filename, "\n".join(lines) + "\n"


def export_markdown_guide(
    session: dict[str, Any],
    user_name: str,
    profile: Any,
) -> tuple[str, str]:
    """Xuất tài liệu học nhanh Markdown gom 3 nhóm L0-L1 -> L2 -> L3+."""
    user_slug = slugify(user_name, "user")
    filename = f"study-guide-{user_slug}.md"

    source_label = str(session.get("source_label") or "N/A")
    created_at = str(session.get("created_at") or "")
    concepts = _extract_concepts(profile)
    if not concepts:
        concepts = _fallback_cards_from_session(session)

    g_l0_l1 = [c for c in concepts if int(c.get("bloom_level", 0)) <= 1]
    g_l2 = [c for c in concepts if int(c.get("bloom_level", 0)) == 2]
    g_l3_plus = [c for c in concepts if int(c.get("bloom_level", 0)) >= 3]

    sections = [
        ("Nhóm 1: L0–L1 (Ưu tiên gỡ ngộ nhận & nắm bản chất)", g_l0_l1),
        ("Nhóm 2: L2 (Củng cố Feynman -> Nâng lên L3–L4)", g_l2),
        ("Nhóm 3: L3+ (Bảo vệ bằng chứng số liệu & tình huống biên)", g_l3_plus),
    ]

    out: list[str] = [
        f"# Study Guide Phản Biện — {user_name or user_slug}",
        "",
        f"- **Hồ sơ:** `{source_label}`",
        f"- **Phiên quét:** `{session.get('scan_id', '')}` ({created_at})",
        f"- **Tổng khái niệm:** {len(concepts)}",
        "",
    ]

    hard_flags = session.get("hard_flags") or []
    if hard_flags:
        out.append("## Cảnh báo lỗi cứng từ phiên quét")
        for f in hard_flags:
            if isinstance(f, dict):
                cite = f"{f.get('file', '')}:L{int(f['line']):02d}" if isinstance(f.get("line"), int) else f.get("file", "")
                out.append(f"- **[{f.get('rule_id', 'FLAG')}]** (`{cite}`): {f.get('detail', '')}")
            else:
                out.append(f"- {f}")
        out.append("")

    for title, group in sections:
        out.append(f"## {title}")
        if not group:
            out.append("_Không có mục nào trong nhóm này._")
            out.append("")
            continue
        for item in group:
            level = int(item.get("bloom_level", 0))
            term = str(item.get("term") or item.get("concept_key") or "Khái niệm")
            cite = str(item.get("source_cite") or source_label)
            out.append(f"### {term} (`{item.get('concept_key', '')}` · {BLOOM_LABELS.get(level, f'L{level}')})")
            out.append(f"- **Trích dẫn:** `{cite}`")
            if item.get("reference"):
                out.append(f"- **Bản chất:** {item['reference']}")
            if item.get("understood_points"):
                out.append("- **Đã trúng:** " + "; ".join(str(x) for x in item["understood_points"]))
            if item.get("missing_points"):
                out.append("- **Còn thiếu:** " + "; ".join(str(x) for x in item["missing_points"]))
            if item.get("misconceptions"):
                out.append("- **Ngộ nhận cần tránh:** " + "; ".join(str(x) for x in item["misconceptions"]))
            if item.get("resolved_misconceptions"):
                out.append("- **Đã gỡ ngộ nhận:** " + "; ".join(str(x) for x in item["resolved_misconceptions"]))
            if item.get("next_probe"):
                out.append(f"- **Câu hỏi nâng bậc (+1 Bloom):** {item['next_probe']}")
            out.append("")

    return filename, "\n".join(out).rstrip() + "\n"


def export_etude_pack_json(
    session: dict[str, Any],
    user_name: str,
    profile: Any,
) -> tuple[str, str]:
    """Xuất gói thẻ luyện tập chuẩn 'etude': 'pack/1' dùng type 'free'."""
    user_slug = slugify(user_name, "user")
    filename = f"study-pack-{user_slug}.pack.json"
    source_label = str(session.get("source_label") or "RepoKSV")
    deck_name = f"RepoKSV Viva ({source_label}) — {user_name or user_slug}"

    cards = _select_study_concepts(session, profile)
    items: list[dict[str, Any]] = []
    for idx, item in enumerate(cards, 1):
        concept_key = str(item.get("concept_key") or f"concept-{idx}")
        term = str(item.get("term") or concept_key)
        cite = str(item.get("source_cite") or source_label)
        level = int(item.get("bloom_level", 0))
        prompt_text = str(
            item.get("next_probe")
            or item.get("prompt")
            or f"Giải thích cơ chế, trade-off và bằng chứng `{cite}` cho khái niệm **{term}**."
        )
        ref_parts = [str(item.get("reference") or "").strip()]
        if item.get("understood_points"):
            ref_parts.append("Ý cốt lõi: " + "; ".join(str(x) for x in item["understood_points"]))
        if item.get("missing_points"):
            ref_parts.append("Cần bổ sung: " + "; ".join(str(x) for x in item["missing_points"]))
        reference_text = "\n".join(p for p in ref_parts if p) or f"Trình bày đúng bản chất `{term}` kèm trích dẫn `{cite}`."

        rubric_text = str(item.get("rubric") or "").strip()
        if not rubric_text:
            rubric_parts = [f"Mục tiêu: nâng từ Bloom L{level} lên L{min(6, level + 1)}."]
            if item.get("missing_points"):
                rubric_parts.append("Phải phủ: " + "; ".join(str(x) for x in item["missing_points"]))
            if item.get("misconceptions"):
                rubric_parts.append("Tránh ngộ nhận: " + "; ".join(str(x) for x in item["misconceptions"]))
            rubric_text = " ".join(rubric_parts)

        explanation_parts = [f"### {term} (`{cite}`)"]
        if item.get("reference"):
            explanation_parts.append(str(item["reference"]))
        if item.get("misconceptions"):
            explanation_parts.append("**Ngộ nhận thường gặp:** " + "; ".join(str(x) for x in item["misconceptions"]))
        if item.get("next_probe"):
            explanation_parts.append(f"**Câu hỏi nâng bậc:** {item['next_probe']}")

        items.append({
            "id": f"repoksv.{user_slug}.{slugify(concept_key, f'c{idx}')}",
            "type": "free",
            "deck": deck_name,
            "tags": [
                f"bloom::L{level}",
                f"topic::{slugify(str(item.get('tag') or 'khai_niem'), 'khai-niem')}",
                f"member::{user_slug}",
            ],
            "fields": {
                "prompt": prompt_text,
                "reference": reference_text,
                "rubric": rubric_text,
                "input": "long",
                "explanation": "\n\n".join(explanation_parts),
            },
            "source": cite,
        })

    pack = {
        "etude": "pack/1",
        "name": f"RepoKSV Study Pack — {user_name or user_slug}",
        "description": f"Bộ thẻ ôn tập phản biện Bloom L0–L6 trích từ phiên quét {source_label}.",
        "decks": [
            {
                "name": deck_name,
                "description": f"Ôn các điểm hổng và nâng bậc Bloom cho {user_name or user_slug} trên {source_label}.",
                "instructions": BLOOM_INSTRUCTIONS_VI,
            }
        ],
        "items": items,
    }
    return filename, json.dumps(pack, ensure_ascii=False, indent=2)


def export_session_json(
    session: dict[str, Any],
    viva_entries: list[dict[str, Any]],
) -> tuple[str, str]:
    """Xuất toàn bộ dữ liệu phiên quét và các lượt phỏng vấn thành JSON."""
    raw_id = str(session.get("scan_id") or session.get("source_label") or "session")
    filename = f"session-{slugify(raw_id, 'session')}.json"
    payload = {
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scan_session": session,
        "viva_entries": viva_entries or [],
    }
    return filename, json.dumps(payload, ensure_ascii=False, indent=2)
