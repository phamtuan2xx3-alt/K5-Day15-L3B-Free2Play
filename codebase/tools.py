"""Công cụ của bài toán Giám khảo ảo (Track A · A6) — chỉ dùng thư viện chuẩn Python.

Đúng 5 công cụ theo hợp đồng trong spec.md §4 và docs/cp2-plan.md:
    list_submission_files · scan_hard_rules · get_rubric · read_file_lines · verify_audit_output
"""
import csv
import json
import os
import re

from tracing import tool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
SUBMISSIONS_DIR = os.path.join(DATA_DIR, "submissions")
RUBRIC_PATH = os.path.join(DATA_DIR, "rubric.json")

REQUIRED_FILES = [
    "TEAMS.md",
    "canvas.md",
    "spec.md",
    "evidence_summary.md",
    "benchmark.csv",
    "metric_spec.yaml",
]


def _resolve_submission_dir(submission_id: str) -> str | None:
    """Giải mã đường dẫn hồ sơ an toàn, chặn path traversal."""
    clean = (submission_id or "").strip()
    if not clean or not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", clean):
        return None
    target = os.path.abspath(os.path.join(SUBMISSIONS_DIR, clean))
    base = os.path.abspath(SUBMISSIONS_DIR)
    if not target.startswith(base + os.sep) or not os.path.isdir(target):
        return None
    return target


def _read_lines(path: str) -> list[str]:
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read().splitlines()


def _find_key_line(path: str, key: str) -> int:
    """Tìm số dòng (1-based) chứa khoá JSON hoặc YAML đầu tiên."""
    target = f'"{key}"'
    for idx, ln in enumerate(_read_lines(path), 1):
        if target in ln:
            return idx
    return 1


@tool
def list_submission_files(submission_id: str) -> dict:
    """Liệt kê các file hiện có và file bắt buộc bị thiếu trong hồ sơ bài nộp.
    Input: submission_id (str). Output: dict {exists, submission_id, present_files, missing_required, line_counts}. Không tác động ra ngoài."""
    folder = _resolve_submission_dir(submission_id)
    if not folder:
        return {
            "exists": False,
            "submission_id": submission_id,
            "present_files": [],
            "missing_required": list(REQUIRED_FILES),
            "line_counts": {},
        }
    present = sorted(
        f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))
    )
    missing = [req for req in REQUIRED_FILES if req not in present]
    line_counts = {
        fname: len(_read_lines(os.path.join(folder, fname))) for fname in present
    }
    return {
        "exists": True,
        "submission_id": submission_id,
        "present_files": present,
        "missing_required": missing,
        "line_counts": line_counts,
    }


def _scan_teams(path: str) -> list[dict]:
    findings = []
    lines = _read_lines(path)
    joined = "\n".join(lines)
    if not re.search(r"-\s*Lớp\s*:\s*L3[AB]\b", joined):
        findings.append({
            "rule_id": "TEAMS-FORMAT",
            "severity": "cao",
            "file": "TEAMS.md",
            "line": 1,
            "detail": "Dòng Lớp phải ghi L3A hoặc L3B.",
        })
    if not re.search(r"-\s*Track\s*:\s*[A-F]\s*$", joined, re.MULTILINE):
        findings.append({
            "rule_id": "TEAMS-FORMAT",
            "severity": "cao",
            "file": "TEAMS.md",
            "line": 1,
            "detail": "Dòng Track phải ghi đúng 1 chữ cái A-F.",
        })
    members = []
    for idx, ln in enumerate(lines, 1):
        s = ln.strip()
        if not s.startswith("|") or s.startswith("|---") or "Họ và tên" in s:
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) >= 5 and cells[0].isdigit():
            members.append((idx, cells))
            if any("____" in c or not c for c in cells[:5]):
                findings.append({
                    "rule_id": "TEAMS-FORMAT",
                    "severity": "cao",
                    "file": "TEAMS.md",
                    "line": idx,
                    "detail": f"Thành viên dòng L{idx:02d} còn ô trống hoặc chưa thay '____'.",
                })
    if not (3 <= len(members) <= 5):
        findings.append({
            "rule_id": "TEAMS-FORMAT",
            "severity": "cao",
            "file": "TEAMS.md",
            "line": members[0][0] if members else 1,
            "detail": f"Số thành viên phải từ 3–5 người (hiện có {len(members)}).",
        })
    if members and members[0][1][3] != "Đội trưởng":
        findings.append({
            "rule_id": "TEAMS-FORMAT",
            "severity": "cao",
            "file": "TEAMS.md",
            "line": members[0][0],
            "detail": "Đội trưởng phải nằm ở dòng thành viên số 1.",
        })
    return findings


def _scan_canvas(path: str) -> list[dict]:
    findings = []
    lines = _read_lines(path)
    numbered = {}
    for idx, ln in enumerate(lines, 1):
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) >= 3 and cells[0] in {"1", "2", "3", "4", "5", "6", "7"}:
            numbered[cells[0]] = (idx, cells[2])
            if not cells[2] or "____" in cells[2]:
                findings.append({
                    "rule_id": "CANVAS-7ROWS",
                    "severity": "trung_binh",
                    "file": "canvas.md",
                    "line": idx,
                    "detail": f"Dòng {cells[0]} trong canvas.md còn trống hoặc chứa '____'.",
                })
    if len(numbered) < 7:
        findings.append({
            "rule_id": "CANVAS-7ROWS",
            "severity": "trung_binh",
            "file": "canvas.md",
            "line": 1,
            "detail": f"Canvas chưa đủ 7 dòng bắt buộc (mới thấy {len(numbered)}/7).",
        })
    if "3" in numbered:
        ln_no, pain_text = numbered["3"]
        if re.search(r"(?<![A-Za-zÀ-ỹ0-9])AI(?![A-Za-zÀ-ỹ0-9])", pain_text):
            findings.append({
                "rule_id": "CANVAS-7ROWS",
                "severity": "cao",
                "file": "canvas.md",
                "line": ln_no,
                "detail": "Dòng 3 (Pain) vi phạm quy tắc: có chứa chữ 'AI'.",
            })
    return findings


def _scan_benchmark(path: str, expected_min_count: int | None = None) -> list[dict]:
    findings = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = list(csv.reader(f))
    if not reader:
        return [{"rule_id": "R4-BENCHMARK", "severity": "cao", "file": "benchmark.csv", "line": 1, "detail": "benchmark.csv trống."}]
    header = [h.strip() for h in reader[0]]
    req_cols = ["id", "input", "expected", "pass_criterion", "type", "source"]
    missing_cols = [c for c in req_cols if c not in header]
    if missing_cols:
        findings.append({
            "rule_id": "R4-BENCHMARK",
            "severity": "cao",
            "file": "benchmark.csv",
            "line": 1,
            "detail": f"Thiếu cột bắt buộc: {', '.join(missing_cols)}.",
        })
    data_rows = reader[1:]
    if len(data_rows) < 10:
        findings.append({
            "rule_id": "R4-BENCHMARK",
            "severity": "cao",
            "file": "benchmark.csv",
            "line": 1,
            "detail": f"Mới có {len(data_rows)} câu thử (CP2 cần >=10, CP3 cần 20-30).",
        })
    if expected_min_count is not None and len(data_rows) < expected_min_count:
        findings.append({
            "rule_id": "PENALTY-STANDARD",
            "severity": "rat_cao",
            "file": "benchmark.csv",
            "line": 1,
            "detail": f"Số câu thử giảm từ {expected_min_count} (CP2) xuống còn {len(data_rows)} — nghi ngờ xoá câu thử trượt (0 điểm R4).",
        })
    col_idx = {c: header.index(c) for c in header}
    kho = 0
    tu_choi = 0
    real_src = 0
    for r_idx, row in enumerate(data_rows, 2):
        joined = " ".join(row)
        if "(ví dụ)" in joined.lower() or "vi du" in joined.lower():
            findings.append({
                "rule_id": "R4-BENCHMARK",
                "severity": "cao",
                "file": "benchmark.csv",
                "line": r_idx,
                "detail": "Còn dòng mẫu '(ví dụ)' chưa xoá.",
            })
        if "type" in col_idx and col_idx["type"] < len(row):
            t = row[col_idx["type"]].strip()
            if t == "kho":
                kho += 1
            elif t == "tu_choi":
                tu_choi += 1
        if "source" in col_idx and col_idx["source"] < len(row):
            s = row[col_idx["source"]].strip()
            if s.startswith("nguoi_dung") or s.startswith("data_that"):
                real_src += 1
    if kho < 5:
        findings.append({
            "rule_id": "R4-BENCHMARK",
            "severity": "cao",
            "file": "benchmark.csv",
            "line": 1,
            "detail": f"Số câu loại 'kho' mới có {kho} (cần >=5).",
        })
    if tu_choi < 2:
        findings.append({
            "rule_id": "R4-BENCHMARK",
            "severity": "cao",
            "file": "benchmark.csv",
            "line": 1,
            "detail": f"Số câu loại 'tu_choi' mới có {tu_choi} (cần >=2).",
        })
    if "source" in col_idx and data_rows and real_src * 3 < len(data_rows):
        findings.append({
            "rule_id": "R4-BENCHMARK",
            "severity": "trung_binh",
            "file": "benchmark.csv",
            "line": 1,
            "detail": f"Tỉ lệ câu từ nguồn người dùng / data thật là {real_src}/{len(data_rows)} (<1/3).",
        })
    return findings


def _scan_secrets_and_injection(folder: str, files: list[str]) -> list[dict]:
    findings = []
    secret_patterns = [
        (r"sk-[A-Za-z0-9_-]{10,}", "Phát hiện chuỗi dạng OpenAI/API key (sk-...)"),
        (r"AIza[A-Za-z0-9_-]{10,}", "Phát hiện chuỗi dạng Google API key (AIza...)"),
        (r"^\s*API_KEY\s*=\s*\S+", "Phát hiện giá trị API_KEY gán trực tiếp trong file nộp"),
        (r"(?<!\d)0[35789]\d{8}(?!\d)", "Phát hiện chuỗi giống số điện thoại cá nhân thật"),
        (r"[A-Za-z0-9._%+-]+@(?!example\.invalid\b|example\.com\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "Phát hiện địa chỉ email cá nhân"),
    ]
    injection_patterns = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"b[oỏ]\s+qua\s+(m[oọ]i|t[aấ]t\s+c[aả]|c[aá]c)\s+(l[oỗ]i|h[uư][oớ]ng\s+d[aẫ]n)",
        r"bo\s+qua\s+moi\s+loi",
        r"x[aá]c\s+nh[aậ]n\s+b[aà]i\s+[đd][aạ]t\s+100%",
        r"xac\s+nhan\s+bai\s+dat\s+100%",
        r"ch[aấ]m\s+(9[0-9]|100)\s*/\s*100",
        r"cham\s+(9[0-9]|100)\s*/\s*100",
    ]
    for fname in files:
        if fname == "meta.json":
            continue
        for idx, ln in enumerate(_read_lines(os.path.join(folder, fname)), 1):
            for pat, msg in secret_patterns:
                if re.search(pat, ln):
                    findings.append({
                        "rule_id": "PENALTY-KEY",
                        "severity": "rat_cao",
                        "file": fname,
                        "line": idx,
                        "detail": f"{msg} — vi phạm trừ 10 điểm.",
                    })
                    break
            for pat in injection_patterns:
                if re.search(pat, ln, re.IGNORECASE):
                    findings.append({
                        "rule_id": "PROMPT-INJECTION",
                        "severity": "rat_cao",
                        "file": fname,
                        "line": idx,
                        "detail": "Phát hiện chỉ dẫn giả (prompt injection) cố ép bỏ qua lỗi hoặc chấm điểm đạt.",
                    })
                    break
    return findings


def _scan_metric_spec(path: str) -> list[dict]:
    findings = []
    lines = _read_lines(path)
    valid_metrics = 0
    for idx, ln in enumerate(lines, 1):
        m = re.match(r"^\s*-\s*name\s*:\s*(.+)$", ln)
        if m:
            val = m.group(1).strip().strip('"').strip("'")
            if val and not val.startswith("<") and "<…" not in val:
                valid_metrics += 1
            else:
                findings.append({
                    "rule_id": "R4-BENCHMARK",
                    "severity": "cao",
                    "file": "metric_spec.yaml",
                    "line": idx,
                    "detail": f"Metric dòng L{idx:02d} còn chỗ trống hoặc mẫu '<…>'.",
                })
    if valid_metrics < 3:
        findings.append({
            "rule_id": "R4-BENCHMARK",
            "severity": "cao",
            "file": "metric_spec.yaml",
            "line": 1,
            "detail": f"metric_spec.yaml mới có {valid_metrics} metric hợp lệ (cần >=3).",
        })
    return findings


@tool
def scan_hard_rules(submission_id: str) -> list:
    """Quét tự động bằng code các lỗi cứng (lộ key/PII, TEAMS, Canvas pain có AI, PR nhầm repo gốc, sửa chuẩn đạt, benchmark/metric_spec, prompt injection).
    Input: submission_id (str). Output: list[dict] các lỗi tìm được {rule_id, severity, file, line, detail}. Không tác động ra ngoài."""
    info = list_submission_files(submission_id)
    if not info["exists"]:
        return []
    folder = _resolve_submission_dir(submission_id)
    present = info["present_files"]
    findings = []

    expected_bench_count = None
    if "meta.json" in present:
        meta_path = os.path.join(folder, "meta.json")
        try:
            with open(meta_path, encoding="utf-8-sig") as f:
                meta = json.load(f)
            if meta.get("pr_target") == "upstream" or "starter" in str(meta.get("git_remote", "")).lower():
                findings.append({
                    "rule_id": "GIT-FORK-PR",
                    "severity": "rat_cao",
                    "file": "meta.json",
                    "line": _find_key_line(meta_path, "pr_target"),
                    "detail": "Đích PR/push đang trỏ về repo gốc của khoá (upstream) thay vì repo fork của nhóm — cảnh báo nguy cơ lộ bài, cần huỷ PR trên repo gốc và đổi remote về repo fork của nhóm.",
                })
            base_thr = str(meta.get("cp2_baseline_threshold", "")).strip()
            cur_thr = str(meta.get("current_threshold", "")).strip()
            if base_thr and cur_thr and base_thr != cur_thr:
                findings.append({
                    "rule_id": "PENALTY-STANDARD",
                    "severity": "rat_cao",
                    "file": "meta.json",
                    "line": _find_key_line(meta_path, "current_threshold"),
                    "detail": f"Chuẩn đạt đã bị đổi từ {base_thr} (CP2) thành {cur_thr} — vi phạm luật chốt CP2 (0 điểm R4).",
                })
            if isinstance(meta.get("cp2_benchmark_count"), int):
                expected_bench_count = meta["cp2_benchmark_count"]
        except Exception as e:
            findings.append({
                "rule_id": "TEAMS-FORMAT",
                "severity": "trung_binh",
                "file": "meta.json",
                "line": 1,
                "detail": f"Không đọc được meta.json: {e}",
            })

    if "TEAMS.md" in present:
        findings.extend(_scan_teams(os.path.join(folder, "TEAMS.md")))
    if "canvas.md" in present:
        findings.extend(_scan_canvas(os.path.join(folder, "canvas.md")))
    if "benchmark.csv" in present:
        findings.extend(_scan_benchmark(os.path.join(folder, "benchmark.csv"), expected_bench_count))
    if "metric_spec.yaml" in present:
        findings.extend(_scan_metric_spec(os.path.join(folder, "metric_spec.yaml")))
    findings.extend(_scan_secrets_and_injection(folder, present))
    return findings


@tool
def get_rubric(criteria_ids: list) -> list:
    """Tra cứu định nghĩa và mức phạt của các tiêu chí rubric AI20K từ data/rubric.json.
    Input: criteria_ids (list[str], truyền ['ALL'] hoặc [] để lấy toàn bộ). Output: list[dict] tiêu chí rubric. Không tác động ra ngoài."""
    with open(RUBRIC_PATH, encoding="utf-8-sig") as f:
        items = json.load(f)
    if not criteria_ids or "ALL" in criteria_ids:
        return items
    wanted = {c.strip() for c in criteria_ids}
    return [it for it in items if it.get("id") in wanted]


@tool
def read_file_lines(submission_id: str, filename: str) -> str:
    """Đọc nội dung một file trong hồ sơ bài nộp kèm số dòng L01, L02... để trích dẫn chính xác.
    Input: submission_id (str), filename (str). Output: chuỗi nội dung đánh số dòng hoặc thông báo thiếu file. Không tác động ra ngoài."""
    folder = _resolve_submission_dir(submission_id)
    if not folder:
        return f"[THIẾU HỒ SƠ: {submission_id}]"
    clean_name = os.path.basename((filename or "").strip())
    path = os.path.join(folder, clean_name)
    if not clean_name or not os.path.isfile(path):
        return f"[THIẾU FILE: {clean_name}]"
    lines = _read_lines(path)
    limit = 120
    numbered = [f"L{idx:02d}: {ln}" for idx, ln in enumerate(lines[:limit], 1)]
    if len(lines) > limit:
        numbered.append(f"... (còn {len(lines) - limit} dòng nữa)")
    return "\n".join(numbered)


@tool
def verify_audit_output(report: str, hard_flags: list, files: dict) -> dict:
    """Hậu kiểm kết quả đánh giá của AI: kiểm mọi trích dẫn file:Lxx có tồn tại thật, chặn tự chấm điểm cuối, và ép giữ nguyên mọi lỗi cứng từ code.
    Input: report (str), hard_flags (list), files (dict từ list_submission_files). Output: dict {verified_output, valid_citations, invalid_citations, auto_grade_blocked, hard_flags_enforced}. Không tác động ra ngoài."""
    line_counts = (files or {}).get("line_counts") or {}
    cite_matches = re.findall(r"\b([A-Za-z0-9_.-]+\.(?:md|csv|yaml|json|txt)):L(\d{1,4})\b", report or "")
    valid_cites = 0
    invalid_cites = []
    for fname, ln_str in cite_matches:
        ln_no = int(ln_str)
        max_ln = line_counts.get(fname)
        if max_ln is not None and 1 <= ln_no <= max_ln:
            valid_cites += 1
        else:
            invalid_cites.append(f"{fname}:L{ln_no:02d}")

    out_text = (report or "").strip()

    # Chặn AI tự chấm điểm số cuối (/100) nếu không phải đang nhắc lại cảnh báo từ chối
    auto_grade_blocked = False
    for ln in out_text.splitlines():
        if re.search(r"\b\d{1,3}\s*/\s*100\b", ln) and not re.search(
            r"không chấm|chặn|từ chối|NO-AUTO-GRADE|cấm|tấn công|bịa", ln, re.IGNORECASE
        ):
            auto_grade_blocked = True
            break
    if auto_grade_blocked:
        out_text += (
            "\n\n[HẬU KIỂM NO-AUTO-GRADE]: Đã chặn kết luận điểm số cuối cùng — "
            "giám khảo ảo chỉ gắn cờ lỗi kèm trích dẫn để học viên tự sửa, không tự cho điểm."
        )

    # Ép giữ nguyên toàn bộ lỗi cứng từ scan_hard_rules (không cho prompt injection xoá lỗi)
    enforced_lines = []
    for flag in hard_flags or []:
        rid = flag.get("rule_id", "")
        fname = flag.get("file", "")
        ln_no = int(flag.get("line", 1))
        cite = f"{fname}:L{ln_no:02d}"
        has_cite = bool(fname and re.search(r"\b" + re.escape(fname) + r":L0*" + str(ln_no) + r"\b", out_text))
        if rid not in out_text or not has_cite:
            enforced_lines.append(f"- [{rid}] ({cite}) {flag.get('detail', '')}")
    if enforced_lines:
        out_text += "\n\n### Cảnh báo lỗi cứng bắt buộc (từ bộ quét code)\n" + "\n".join(enforced_lines)

    if invalid_cites:
        out_text += (
            "\n\n[HẬU KIỂM TRÍCH DẪN]: Phát hiện trích dẫn chưa khớp số dòng thực tế: "
            + ", ".join(invalid_cites)
        )

    return {
        "verified_output": out_text,
        "valid_citations": valid_cites,
        "invalid_citations": invalid_cites,
        "auto_grade_blocked": auto_grade_blocked,
        "hard_flags_enforced": len(hard_flags or []),
    }
