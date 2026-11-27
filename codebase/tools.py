"""Công cụ của bài toán Giám khảo ảo (Track A · A6) — chỉ dùng thư viện chuẩn Python.

Giữ nguyên 5 công cụ theo hợp đồng trong spec.md §4 và docs/cp2-plan.md:
    list_submission_files · scan_hard_rules · get_rubric · read_file_lines · verify_audit_output
Bổ sung công cụ nhận diện Team/Cá nhân cho Hướng 2:
    extract_project_identity
"""
import csv
import io
import json
import os
import re
import unicodedata

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

CITE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.(?:md|csv|yaml|yml|json|txt)):L(\d{1,4})\b"
)

SECRET_PATTERNS = [
    (r"sk-[A-Za-z0-9_-]{10,}", "Phát hiện chuỗi dạng OpenAI/API key (sk-...)"),
    (r"AIza[A-Za-z0-9_-]{10,}", "Phát hiện chuỗi dạng Google API key (AIza...)"),
    (r"^\s*API_KEY\s*=\s*\S+", "Phát hiện giá trị API_KEY gán trực tiếp trong file nộp"),
    (r"(?<!\d)0[35789]\d{8}(?!\d)", "Phát hiện chuỗi giống số điện thoại cá nhân thật"),
    (
        r"[A-Za-z0-9._%+-]+@(?!example\.invalid\b|example\.com\b|users\.noreply\.github\.com\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "Phát hiện địa chỉ email cá nhân",
    ),
]

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"b[oỏ]\s+qua\s+(m[oọ]i|t[aấ]t\s+c[aả]|c[aá]c)\s+(l[oỗ]i|h[uư][oớ]ng\s+d[aẫ]n)",
    r"bo\s+qua\s+moi\s+loi",
    r"x[aá]c\s+nh[aậ]n\s+b[aà]i\s+[đd][aạ]t\s+100%",
    r"xac\s+nhan\s+bai\s+dat\s+100%",
    r"ch[aấ]m\s+(9[0-9]|100)\s*/\s*100",
    r"cham\s+(9[0-9]|100)\s*/\s*100",
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


def _to_lines(content: str | list[str]) -> list[str]:
    if isinstance(content, list):
        return [str(ln) for ln in content]
    text = (content or "").lstrip("\ufeff")
    return text.splitlines()


def _find_key_line_in_lines(lines: list[str], key: str) -> int:
    """Tìm số dòng (1-based) chứa khoá JSON hoặc YAML đầu tiên trong danh sách dòng."""
    target = f'"{key}"'
    for idx, ln in enumerate(lines, 1):
        if target in ln:
            return idx
    return 1


def _find_key_line(path: str, key: str) -> int:
    """Tìm số dòng (1-based) chứa khoá JSON hoặc YAML đầu tiên."""
    return _find_key_line_in_lines(_read_lines(path), key)


def format_numbered_lines(content: list[str] | str, limit: int = 120) -> str:
    """Đánh số dòng L01, L02... cho nội dung file để AI trích dẫn chính xác."""
    lines = _to_lines(content)
    numbered = [f"L{idx:02d}: {ln}" for idx, ln in enumerate(lines[:limit], 1)]
    if len(lines) > limit:
        numbered.append(f"... (còn {len(lines) - limit} dòng nữa)")
    return "\n".join(numbered)


def _slugify(text: str) -> str:
    """Chuyển họ tên tiếng Việt thành slug ASCII không dấu."""
    norm = unicodedata.normalize("NFKD", (text or "").replace("đ", "d").replace("Đ", "D"))
    ascii_text = "".join(ch for ch in norm if not unicodedata.combining(ch))
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "member"


def load_submission_bundle(submission_id: str) -> dict:
    """Đọc toàn bộ hồ sơ bài nộp cục bộ vào RAM (text + meta.json) để quét và định danh."""
    folder = _resolve_submission_dir(submission_id)
    if not folder:
        return {
            "exists": False,
            "submission_id": submission_id,
            "file_info": {
                "exists": False,
                "submission_id": submission_id,
                "present_files": [],
                "missing_required": list(REQUIRED_FILES),
                "line_counts": {},
            },
            "files_content": {},
            "meta": None,
        }

    present = sorted(
        f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))
    )
    missing = [req for req in REQUIRED_FILES if req not in present]
    files_content: dict[str, str] = {}
    line_counts: dict[str, int] = {}

    for fname in present:
        fpath = os.path.join(folder, fname)
        with open(fpath, encoding="utf-8-sig", errors="replace") as f:
            raw = f.read()
        files_content[fname] = raw
        line_counts[fname] = len(raw.splitlines())

    reflection_dir = os.path.join(folder, "reflection")
    if os.path.isdir(reflection_dir):
        for fname in sorted(os.listdir(reflection_dir)):
            fpath = os.path.join(reflection_dir, fname)
            if os.path.isfile(fpath) and fname.endswith(".md"):
                rel_key = f"reflection/{fname}"
                with open(fpath, encoding="utf-8-sig", errors="replace") as f:
                    raw = f.read()
                files_content[rel_key] = raw
                line_counts[rel_key] = len(raw.splitlines())

    meta = None
    if "meta.json" in files_content:
        try:
            meta = json.loads(files_content["meta.json"])
        except Exception:
            meta = None

    return {
        "exists": True,
        "submission_id": submission_id,
        "file_info": {
            "exists": True,
            "submission_id": submission_id,
            "present_files": present,
            "missing_required": missing,
            "line_counts": line_counts,
        },
        "files_content": files_content,
        "meta": meta,
    }


@tool
def list_submission_files(submission_id: str) -> dict:
    """Liệt kê các file hiện có và file bắt buộc bị thiếu trong hồ sơ bài nộp.
    Input: submission_id (str). Output: dict {exists, submission_id, present_files, missing_required, line_counts}. Không tác động ra ngoài."""
    return load_submission_bundle(submission_id)["file_info"]


def scan_teams_lines(lines: list[str], filename: str = "TEAMS.md") -> list[dict]:
    """Quét định dạng TEAMS.md từ danh sách dòng."""
    findings = []
    joined = "\n".join(lines)
    if not re.search(r"-\s*Lớp\s*:\s*L3[AB]\b", joined):
        findings.append({
            "rule_id": "TEAMS-FORMAT",
            "severity": "cao",
            "file": filename,
            "line": 1,
            "detail": "Dòng Lớp phải ghi L3A hoặc L3B.",
        })
    if not re.search(r"-\s*Track\s*:\s*[A-F]\s*$", joined, re.MULTILINE):
        findings.append({
            "rule_id": "TEAMS-FORMAT",
            "severity": "cao",
            "file": filename,
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
                    "file": filename,
                    "line": idx,
                    "detail": f"Thành viên dòng L{idx:02d} còn ô trống hoặc chưa thay '____'.",
                })
    if not (3 <= len(members) <= 5):
        findings.append({
            "rule_id": "TEAMS-FORMAT",
            "severity": "cao",
            "file": filename,
            "line": members[0][0] if members else 1,
            "detail": f"Số thành viên phải từ 3–5 người (hiện có {len(members)}).",
        })
    if members and members[0][1][3] != "Đội trưởng":
        findings.append({
            "rule_id": "TEAMS-FORMAT",
            "severity": "cao",
            "file": filename,
            "line": members[0][0],
            "detail": "Đội trưởng phải nằm ở dòng thành viên số 1.",
        })
    return findings


def scan_canvas_lines(lines: list[str], filename: str = "canvas.md") -> list[dict]:
    """Quét bảng 7 dòng và lỗi pain chứa chữ 'AI' trong canvas.md từ danh sách dòng."""
    findings = []
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
                    "file": filename,
                    "line": idx,
                    "detail": f"Dòng {cells[0]} trong {filename} còn trống hoặc chứa '____'.",
                })
    if len(numbered) < 7:
        findings.append({
            "rule_id": "CANVAS-7ROWS",
            "severity": "trung_binh",
            "file": filename,
            "line": 1,
            "detail": f"Canvas chưa đủ 7 dòng bắt buộc (mới thấy {len(numbered)}/7).",
        })
    if "3" in numbered:
        ln_no, pain_text = numbered["3"]
        if re.search(r"(?<![A-Za-zÀ-ỹ0-9])AI(?![A-Za-zÀ-ỹ0-9])", pain_text):
            findings.append({
                "rule_id": "CANVAS-7ROWS",
                "severity": "cao",
                "file": filename,
                "line": ln_no,
                "detail": "Dòng 3 (Pain) vi phạm quy tắc: có chứa chữ 'AI'.",
            })
    return findings


def scan_benchmark_lines(
    lines: list[str],
    filename: str = "benchmark.csv",
    expected_min_count: int | None = None,
) -> list[dict]:
    """Quét cấu trúc và ngưỡng CP2/CP3 của benchmark.csv từ danh sách dòng."""
    findings = []
    cleaned = list(lines)
    if cleaned:
        cleaned[0] = cleaned[0].lstrip("\ufeff")
    reader = list(csv.reader(io.StringIO("\n".join(cleaned))))
    if not reader:
        return [{
            "rule_id": "R4-BENCHMARK",
            "severity": "cao",
            "file": filename,
            "line": 1,
            "detail": f"{filename} trống.",
        }]
    header = [h.strip() for h in reader[0]]
    req_cols = ["id", "input", "expected", "pass_criterion", "type", "source"]
    missing_cols = [c for c in req_cols if c not in header]
    if missing_cols:
        findings.append({
            "rule_id": "R4-BENCHMARK",
            "severity": "cao",
            "file": filename,
            "line": 1,
            "detail": f"Thiếu cột bắt buộc: {', '.join(missing_cols)}.",
        })
    data_rows = reader[1:]
    if len(data_rows) < 10:
        findings.append({
            "rule_id": "R4-BENCHMARK",
            "severity": "cao",
            "file": filename,
            "line": 1,
            "detail": f"Mới có {len(data_rows)} câu thử (CP2 cần >=10, CP3 cần 20-30).",
        })
    if expected_min_count is not None and len(data_rows) < expected_min_count:
        findings.append({
            "rule_id": "PENALTY-STANDARD",
            "severity": "rat_cao",
            "file": filename,
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
                "file": filename,
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
            "file": filename,
            "line": 1,
            "detail": f"Số câu loại 'kho' mới có {kho} (cần >=5).",
        })
    if tu_choi < 2:
        findings.append({
            "rule_id": "R4-BENCHMARK",
            "severity": "cao",
            "file": filename,
            "line": 1,
            "detail": f"Số câu loại 'tu_choi' mới có {tu_choi} (cần >=2).",
        })
    if "source" in col_idx and data_rows and real_src * 3 < len(data_rows):
        findings.append({
            "rule_id": "R4-BENCHMARK",
            "severity": "trung_binh",
            "file": filename,
            "line": 1,
            "detail": f"Tỉ lệ câu từ nguồn người dùng / data thật là {real_src}/{len(data_rows)} (<1/3).",
        })
    return findings


def scan_metric_spec_lines(lines: list[str], filename: str = "metric_spec.yaml") -> list[dict]:
    """Quét metric_spec.yaml từ danh sách dòng."""
    findings = []
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
                    "file": filename,
                    "line": idx,
                    "detail": f"Metric dòng L{idx:02d} còn chỗ trống hoặc mẫu '<…>'.",
                })
    if valid_metrics < 3:
        findings.append({
            "rule_id": "R4-BENCHMARK",
            "severity": "cao",
            "file": filename,
            "line": 1,
            "detail": f"{filename} mới có {valid_metrics} metric hợp lệ (cần >=3).",
        })
    return findings


def scan_secrets_and_injection_map(files_lines: dict[str, list[str]]) -> list[dict]:
    """Quét lộ API key/PII và chỉ dẫn prompt injection trên map {filename: lines}."""
    findings = []
    for fname, lines in (files_lines or {}).items():
        if os.path.basename(fname) == "meta.json":
            continue
        for idx, ln in enumerate(lines, 1):
            for pat, msg in SECRET_PATTERNS:
                if re.search(pat, ln):
                    findings.append({
                        "rule_id": "PENALTY-KEY",
                        "severity": "rat_cao",
                        "file": fname,
                        "line": idx,
                        "detail": f"{msg} — vi phạm trừ 10 điểm.",
                    })
                    break
            for pat in INJECTION_PATTERNS:
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


def _scan_meta_dict(
    meta: dict,
    meta_lines: list[str] | None = None,
    filename: str = "meta.json",
) -> tuple[list[dict], int | None]:
    """Kiểm tra các cờ mô phỏng và trạng thái git trong meta.json."""
    findings = []
    expected_bench_count = None
    lines = meta_lines or []

    if meta.get("repo_private"):
        findings.append({
            "rule_id": "PUBLIC-ACCESS",
            "severity": "rat_cao",
            "file": filename,
            "line": _find_key_line_in_lines(lines, "repo_private"),
            "detail": "CHƯA KIỂM ĐƯỢC (G10) — Repo đang để chế độ riêng tư (private: true), không truy cập được ở chế độ công khai.",
        })

    if meta.get("pr_target") == "upstream" or "starter" in str(meta.get("git_remote", "")).lower():
        findings.append({
            "rule_id": "GIT-FORK-PR",
            "severity": "rat_cao",
            "file": filename,
            "line": _find_key_line_in_lines(lines, "pr_target"),
            "detail": "Đích PR/push đang trỏ về repo gốc của khoá (upstream) thay vì repo fork của nhóm — cảnh báo nguy cơ lộ bài, cần huỷ PR trên repo gốc và đổi remote về repo fork của nhóm.",
        })

    base_thr = str(meta.get("cp2_baseline_threshold", "")).strip()
    cur_thr = str(meta.get("current_threshold", "")).strip()
    if base_thr and cur_thr and base_thr != cur_thr:
        findings.append({
            "rule_id": "PENALTY-STANDARD",
            "severity": "rat_cao",
            "file": filename,
            "line": _find_key_line_in_lines(lines, "current_threshold"),
            "detail": f"Chuẩn đạt đã bị đổi từ {base_thr} (CP2) thành {cur_thr} — vi phạm luật chốt CP2 (0 điểm R4).",
        })

    tamper = meta.get("post_cp2_tamper")
    if tamper:
        tamper_note = ""
        if isinstance(tamper, dict):
            parts = [str(tamper.get(k)) for k in ("file", "sha", "detail") if tamper.get(k)]
            tamper_note = f" ({', '.join(parts)})" if parts else ""
        elif isinstance(tamper, str):
            tamper_note = f" ({tamper.strip()})"
        elif isinstance(tamper, list):
            tamper_note = f" ({', '.join(str(x) for x in tamper if x)})"
        findings.append({
            "rule_id": "PENALTY-STANDARD",
            "severity": "rat_cao",
            "file": filename,
            "line": _find_key_line_in_lines(lines, "post_cp2_tamper"),
            "detail": f"Phát hiện chỉnh sửa chuẩn đạt / bộ câu thử sau mốc chốt CP2{tamper_note} — 0 điểm khối R4.",
        })

    leaked = meta.get("leaked_files")
    if leaked:
        leaked_list = [str(x).strip() for x in (leaked if isinstance(leaked, list) else [leaked]) if str(x).strip()]
        if leaked_list:
            findings.append({
                "rule_id": "PENALTY-KEY",
                "severity": "rat_cao",
                "file": filename,
                "line": _find_key_line_in_lines(lines, "leaked_files"),
                "detail": f"Phát hiện file nhạy cảm bị đẩy lên repo ({', '.join(leaked_list)}) — vi phạm trừ 10 điểm.",
            })

    if isinstance(meta.get("cp2_benchmark_count"), int):
        expected_bench_count = meta["cp2_benchmark_count"]

    return findings, expected_bench_count


def _pick_file(files_lines: dict[str, list[str]], candidates: tuple[str, ...]) -> tuple[str | None, list[str] | None]:
    """Tìm file theo danh sách đường dẫn ưu tiên, sau đó đối chiếu theo tên file gốc."""
    for cand in candidates:
        if cand in files_lines:
            return cand, files_lines[cand]
    basenames = {os.path.basename(c) for c in candidates}
    for fname, lines in files_lines.items():
        if os.path.basename(fname) in basenames:
            return fname, lines
    return None, None


def scan_in_memory_submission(
    files_content: dict[str, str | list[str]],
    meta: dict | None = None,
    expected_bench_count: int | None = None,
) -> list[dict]:
    """Quét toàn bộ luật cứng trên dữ liệu nằm trong RAM (dùng chung cho S01..S25 và GitHub Live Guard)."""
    files_lines = {fname: _to_lines(content) for fname, content in (files_content or {}).items()}
    findings = []

    meta_fname, meta_lines = _pick_file(files_lines, ("meta.json",))
    parsed_meta = meta
    if parsed_meta is None and meta_lines is not None:
        try:
            parsed_meta = json.loads("\n".join(meta_lines))
        except Exception as e:
            findings.append({
                "rule_id": "TEAMS-FORMAT",
                "severity": "trung_binh",
                "file": meta_fname or "meta.json",
                "line": 1,
                "detail": f"Không đọc được meta.json: {e}",
            })
    if isinstance(parsed_meta, dict):
        meta_findings, meta_bench_count = _scan_meta_dict(
            parsed_meta, meta_lines=meta_lines, filename=meta_fname or "meta.json"
        )
        findings.extend(meta_findings)
        if expected_bench_count is None:
            expected_bench_count = meta_bench_count

    teams_name, teams_lines = _pick_file(files_lines, ("TEAMS.md",))
    if teams_lines is not None and teams_name is not None:
        findings.extend(scan_teams_lines(teams_lines, filename=teams_name))

    canvas_name, canvas_lines = _pick_file(files_lines, ("canvas.md",))
    if canvas_lines is not None and canvas_name is not None:
        findings.extend(scan_canvas_lines(canvas_lines, filename=canvas_name))

    bench_name, bench_lines = _pick_file(files_lines, ("eval/benchmark.csv", "benchmark.csv"))
    if bench_lines is not None and bench_name is not None:
        findings.extend(scan_benchmark_lines(bench_lines, filename=bench_name, expected_min_count=expected_bench_count))

    metric_name, metric_lines = _pick_file(files_lines, ("eval/metric_spec.yaml", "metric_spec.yaml"))
    if metric_lines is not None and metric_name is not None:
        findings.extend(scan_metric_spec_lines(metric_lines, filename=metric_name))

    findings.extend(scan_secrets_and_injection_map(files_lines))
    return findings


def _scan_teams(path: str) -> list[dict]:
    return scan_teams_lines(_read_lines(path), filename=os.path.basename(path))


def _scan_canvas(path: str) -> list[dict]:
    return scan_canvas_lines(_read_lines(path), filename=os.path.basename(path))


def _scan_benchmark(path: str, expected_min_count: int | None = None) -> list[dict]:
    return scan_benchmark_lines(_read_lines(path), filename=os.path.basename(path), expected_min_count=expected_min_count)


def _scan_secrets_and_injection(folder: str, files: list[str]) -> list[dict]:
    files_lines = {
        fname: _read_lines(os.path.join(folder, fname))
        for fname in files
        if fname != "meta.json"
    }
    return scan_secrets_and_injection_map(files_lines)


def _scan_metric_spec(path: str) -> list[dict]:
    return scan_metric_spec_lines(_read_lines(path), filename=os.path.basename(path))


@tool
def scan_hard_rules(submission_id: str) -> list:
    """Quét tự động bằng code các lỗi cứng (lộ key/PII, TEAMS, Canvas pain có AI, PR nhầm repo gốc, sửa chuẩn đạt, benchmark/metric_spec, prompt injection).
    Input: submission_id (str). Output: list[dict] các lỗi tìm được {rule_id, severity, file, line, detail}. Không tác động ra ngoài."""
    bundle = load_submission_bundle(submission_id)
    if not bundle["exists"]:
        return []
    return scan_in_memory_submission(bundle["files_content"], meta=bundle["meta"])


@tool
def extract_project_identity(files_content: dict, github_owner: str = "") -> dict:
    """Nhận diện danh tính dự án (nhóm >=2 thành viên vs cá nhân 0-1 người) từ TEAMS.md, spec.md §10 và reflection/*.md.
    Input: files_content (dict[str, str]), github_owner (str). Output: dict {mode, default_user, members, member_names, team_name, track}. Không tác động ra ngoài."""
    files_lines = {fname: _to_lines(content) for fname, content in (files_content or {}).items()}
    _, teams_lines = _pick_file(files_lines, ("TEAMS.md",))
    _, spec_lines = _pick_file(files_lines, ("spec.md",))

    team_name = ""
    track = ""
    members: list[dict] = []

    if teams_lines:
        for ln in teams_lines:
            m_team = re.match(r"^\s*-\s*Tên\s+nhóm\s*:\s*(.+)$", ln)
            if m_team:
                val = m_team.group(1).strip()
                if val and "____" not in val:
                    team_name = val
            m_track = re.match(r"^\s*-\s*Track\s*:\s*([A-F])\b", ln)
            if m_track:
                track = m_track.group(1).strip()

            s = ln.strip()
            if not s.startswith("|") or s.startswith("|---") or "Họ và tên" in s:
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 5 and cells[0].isdigit():
                name = cells[1].strip()
                if not name or "____" in name:
                    continue
                members.append({
                    "stt": cells[0].strip(),
                    "name": name,
                    "slug": _slugify(name),
                    "student_id": cells[2].strip(),
                    "role": cells[3].strip(),
                    "tasks": cells[4].strip(),
                    "reflection_file": "",
                })

    reflection_files = [
        fname for fname in files_lines
        if fname.startswith("reflection/") and fname.endswith(".md")
    ]
    spec_s10_lines: list[str] = []
    if spec_lines:
        in_s10 = False
        for ln in spec_lines:
            if re.match(r"^\s*##\s*§10\b", ln):
                in_s10 = True
                continue
            if in_s10 and re.match(r"^\s*##\s*§\d+", ln):
                break
            if in_s10:
                spec_s10_lines.append(ln)

    for member in members:
        m_slug = member["slug"]
        m_name_low = member["name"].lower()
        last_token = m_slug.split("-")[-1] if m_slug else ""
        for rfile in reflection_files:
            rbase = os.path.basename(rfile).lower()
            if m_slug in rbase or (last_token and last_token in rbase):
                member["reflection_file"] = rfile
                break
        if spec_s10_lines:
            matched_notes = [ln.strip() for ln in spec_s10_lines if m_name_low in ln.lower()]
            if matched_notes:
                member["spec_tasks"] = " | ".join(matched_notes[:2])

    if len(members) >= 2:
        mode = "team"
        default_user = None
    elif len(members) == 1:
        mode = "personal"
        default_user = members[0]["name"]
    else:
        mode = "personal"
        default_user = (github_owner or "").strip() or "Người dùng cá nhân"

    return {
        "mode": mode,
        "default_user": default_user,
        "members": members,
        "member_names": [m["name"] for m in members],
        "team_name": team_name,
        "track": track,
    }


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
    return format_numbered_lines(_read_lines(path), limit=120)


@tool
def verify_audit_output(report: str, hard_flags: list, files: dict) -> dict:
    """Hậu kiểm kết quả đánh giá của AI: kiểm mọi trích dẫn file:Lxx có tồn tại thật, chặn tự chấm điểm cuối, và ép giữ nguyên mọi lỗi cứng từ code.
    Input: report (str), hard_flags (list), files (dict từ list_submission_files). Output: dict {verified_output, valid_citations, invalid_citations, auto_grade_blocked, hard_flags_enforced}. Không tác động ra ngoài."""
    line_counts = (files or {}).get("line_counts") or {}
    cite_matches = CITE_PATH_RE.findall(report or "")
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

    # Chặn AI tự chấm điểm số cuối (/100) nhưng không chặn nhầm thang Bloom (Level X/6)
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
        has_cite = bool(
            fname
            and re.search(r"(?<![A-Za-z0-9_./-])" + re.escape(fname) + r":L0*" + str(ln_no) + r"\b", out_text)
        )
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
