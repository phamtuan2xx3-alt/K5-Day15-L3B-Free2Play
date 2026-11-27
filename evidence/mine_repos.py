"""Đào data: repo công khai của các nhóm hackathon K5 Day15 có đạt phần nộp CP1 không.

Chạy:  python evidence/mine_repos.py            (cần GitHub CLI `gh` đã đăng nhập để tìm repo)

Đếm gì (viết trước khi chạy, xem evidence/data-mining.md):
  - Tập: mọi repo công khai có tên dạng K5-Day15-L3A-… / K5-Day15-L3B-… tìm được qua GitHub search
    tại thời điểm chạy. Mẫu số N = số repo tìm được (kể cả repo trống hoặc chưa sửa gì).
  - TEAMS.md: có file không · có qua hàm kiểm check_teams() của khung BTC (eval/run_eval.py) không,
    tức đúng format để BTC quét ghép điểm. Gom cảnh báo thành nhóm.
  - canvas.md: có file không · đủ 7 dòng đã điền không (ô "Nhóm điền" của dòng 1–7 không trống,
    không còn "____") · dòng 3 (pain) có chữ "AI" đứng riêng không (đề yêu cầu bài toán không viết chữ AI).

Quyền riêng tư: chỉ in số tổng hợp. Không in, không lưu tên repo / tên nhóm / tên người.
Repo công khai là của bạn cùng khoá: không trích nội dung, không nêu nhóm nào sai.
"""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "eval"))
import run_eval  # noqa: E402  hàm check_teams của khung BTC

NAME_RE = re.compile(r"(?i)^K5-Day15-L3[AB]-")


def find_repos():
    out = subprocess.run(
        ["gh", "search", "repos", "K5-Day15", "--limit", "1000", "--json", "fullName,name"],
        capture_output=True, text=True, check=True, encoding="utf-8").stdout
    return sorted({r["fullName"] for r in json.loads(out) if NAME_RE.match(r["name"])})


def fetch(full_name, path):
    url = "https://raw.githubusercontent.com/%s/HEAD/%s" % (full_name, path)
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return unicodedata.normalize("NFC", r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def teams_warnings(text):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(text)
        tmp = f.name
    old = run_eval.TEAMS
    try:
        run_eval.TEAMS = tmp
        with contextlib.redirect_stdout(io.StringIO()):
            return run_eval.check_teams()
    finally:
        run_eval.TEAMS = old
        os.unlink(tmp)


def warning_group(w):
    if "chưa điền" in w:
        return "còn ô chưa điền (____)"
    if "tiêu đề bảng" in w:
        return "sai tiêu đề bảng"
    if "Đội trưởng" in w:
        return "sai dòng / số Đội trưởng"
    if "thiếu dòng" in w:
        return "thiếu dòng thông tin nhóm"
    if "Lớp" in w or "Track" in w:
        return "Lớp / Track ghi sai chữ"
    if "3–5 người" in w:
        return "số thành viên ngoài 3–5"
    return "khác"


def canvas_rows(text):
    rows = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0] in {"1", "2", "3", "4", "5", "6", "7"}:
            rows[cells[0]] = cells[2]
    return rows


def main():
    repos = find_repos()
    n = len(repos)
    c = Counter()
    groups = Counter()
    for full in repos:
        teams = fetch(full, "TEAMS.md")
        if teams is None:
            c["teams_missing"] += 1
        else:
            warns = teams_warnings(teams)
            if warns:
                c["teams_fail"] += 1
                for g in {warning_group(w) for w in warns}:
                    groups[g] += 1
            else:
                c["teams_ok"] += 1
        canvas = fetch(full, "canvas.md")
        if canvas is None:
            c["canvas_missing"] += 1
            continue
        rows = canvas_rows(canvas)
        filled = [k for k in "1234567" if rows.get(k) and "____" not in rows[k]]
        c["canvas_full" if len(filled) == 7 else ("canvas_empty" if not filled else "canvas_partial")] += 1
        if rows.get("3") and re.search(r"(?<![A-Za-z])AI(?![A-Za-z])", rows["3"]):
            c["pain_has_AI"] += 1

    pct = lambda x: "%d/%d (%.0f%%)" % (x, n, 100.0 * x / n) if n else "0/0"
    print("Thời điểm chạy (UTC):", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
    print("N = %d repo tìm được" % n)
    print("TEAMS.md qua hàm kiểm của BTC :", pct(c["teams_ok"]))
    print("TEAMS.md có nhưng chưa qua    :", pct(c["teams_fail"]))
    print("Không có TEAMS.md             :", pct(c["teams_missing"]))
    for g, v in groups.most_common():
        print("   - %-32s %s" % (g, pct(v)))
    print("canvas.md đủ 7 dòng           :", pct(c["canvas_full"]))
    print("canvas.md điền một phần       :", pct(c["canvas_partial"]))
    print("canvas.md còn trống hoàn toàn :", pct(c["canvas_empty"]))
    print("Không có canvas.md            :", pct(c["canvas_missing"]))
    print("Dòng 3 (pain) có chữ AI       :", pct(c["pain_has_AI"]))


if __name__ == "__main__":
    main()
