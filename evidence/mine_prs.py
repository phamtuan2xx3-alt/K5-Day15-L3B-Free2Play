"""Đào data lần 2: PR học viên mở nhầm vào repo đề gốc của khoá (org VinUni-AI20k).

Chạy:  python evidence/mine_prs.py            (cần GitHub CLI `gh` đã đăng nhập)

Đếm gì (viết trước khi chạy, xem evidence/data-mining.md phần 6):
  - Tập: PR mọi trạng thái trong các repo đề lab L3 khoá K5 của org VinUni-AI20k
    (tên khớp REPO_RE bên dưới). Mọi lab nộp bằng fork / repo riêng + link LMS,
    không lab nào yêu cầu PR vào repo gốc → PR của người học vào đây là PR nhầm.
  - Loại: tác giả có author_association OWNER / MEMBER / COLLABORATOR (BTC, coach) và bot.
  - In: số PR nhầm, số tài khoản khác nhau, số repo bị PR nhầm, trạng thái
    (mở / đóng / bị merge), trung vị thời gian đến lúc đóng, riêng repo hackathon Day 15.

Quyền riêng tư: chỉ in số tổng hợp. Không in, không lưu tên tài khoản, tiêu đề hay nội dung PR.
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from statistics import median

ORG = "VinUni-AI20k"
REPO_RE = re.compile(r"^(K5-L3|K5_L3_|K5-L34-|K5-Day8-|K5-Day9-)")
HACKATHON = "K5-L3-Day15-AI-Product-Hackathon"
STAFF = {"OWNER", "MEMBER", "COLLABORATOR"}


def gh_json(args):
    out = subprocess.run(["gh"] + args, capture_output=True, text=True, check=True,
                         encoding="utf-8").stdout
    return out


def list_repos():
    out = gh_json(["repo", "list", ORG, "--limit", "1000", "--json", "name"])
    return sorted(r["name"] for r in json.loads(out) if REPO_RE.match(r["name"]))


def list_pulls(repo):
    # --paginate nối nhiều trang JSON; --jq '.[]' cho mỗi PR một dòng JSON
    out = gh_json(["api", "--paginate", "repos/%s/%s/pulls?state=all&per_page=100" % (ORG, repo),
                   "--jq", ".[] | {user_type: .user.type, assoc: .author_association, "
                           "login: .user.login, state: .state, created: .created_at, "
                           "closed: .closed_at, merged: .merged_at, number: .number, "
                           "head_repo: .head.repo.name}"])
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def closed_by(repo, number):
    out = gh_json(["api", "repos/%s/%s/issues/%d" % (ORG, repo, number), "--jq", ".closed_by.login // \"\""])
    return out.strip()


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def pct(x, n):
    return "%d/%d (%d%%)" % (x, n, round(100 * x / n)) if n else "0/0"


def main():
    run_at = datetime.now(timezone.utc)
    repos = list_repos()
    wrong = []           # (repo, pr) của người học
    staff_count = 0
    per_repo = Counter()
    for repo in repos:
        for pr in list_pulls(repo):
            if pr["user_type"] == "Bot" or pr["assoc"] in STAFF:
                staff_count += 1
                continue
            wrong.append((repo, pr))
            per_repo[repo] += 1

    accounts = {pr["login"] for _, pr in wrong}
    n = len(wrong)
    merged = sum(1 for _, pr in wrong if pr["merged"])
    still_open = sum(1 for _, pr in wrong if pr["state"] == "open")
    closed_unmerged = n - merged - still_open
    hours_to_close = [(ts(pr["closed"]) - ts(pr["created"])).total_seconds() / 3600
                      for _, pr in wrong if pr["closed"]]
    hk = [pr for repo, pr in wrong if repo == HACKATHON]
    hk_accounts = {pr["login"] for pr in hk}
    multi = sum(1 for c in Counter(pr["login"] for _, pr in wrong).values() if c > 1)

    # Bổ sung sau lần chạy đầu (xem data-mining.md phần 6, mục "Bổ sung"):
    # (a) ai đóng PR: chính tác giả hay người khác; (b) nhánh nguồn nằm trong repo đã đổi tên.
    closed = [(repo, pr) for repo, pr in wrong if pr["closed"]]
    with ThreadPoolExecutor(max_workers=8) as ex:
        closers = list(ex.map(lambda rp: closed_by(rp[0], rp[1]["number"]), closed))
    self_closed = sum(1 for (_, pr), c in zip(closed, closers) if c == pr["login"])
    renamed = sum(1 for repo, pr in wrong if pr["head_repo"] and pr["head_repo"] != repo)
    no_head = sum(1 for _, pr in wrong if not pr["head_repo"])

    print("Chạy lúc %s UTC (giờ VN = UTC+7)" % run_at.strftime("%d/%m/%Y %H:%M"))
    print("Repo đề lab L3 K5 trong org %s: %d" % (ORG, len(repos)))
    print("PR của BTC / coach / bot (loại ra): %d" % staff_count)
    print()
    print("PR nhầm của người học: %d" % n)
    print("  Tài khoản khác nhau: %d (cận dưới; %d tài khoản mở nhầm hơn 1 lần)" % (len(accounts), multi))
    print("  Repo đề bị PR nhầm: %s" % pct(len(per_repo), len(repos)))
    print("  Trạng thái: còn mở %s · đóng không merge %s · BỊ MERGE vào repo gốc %s"
          % (pct(still_open, n), pct(closed_unmerged, n), pct(merged, n)))
    if hours_to_close:
        print("  Thời gian đến lúc đóng: trung vị %.0f phút · %s đóng trong 1 giờ · %s trong 24 giờ"
              % (60 * median(hours_to_close),
                 pct(sum(1 for h in hours_to_close if h <= 1), len(hours_to_close)),
                 pct(sum(1 for h in hours_to_close if h <= 24), len(hours_to_close))))
    print("  Ai đóng: chính người mở PR %s · người khác (BTC / coach) %s"
          % (pct(self_closed, len(closed)), pct(len(closed) - self_closed, len(closed))))
    print("  Nhánh nguồn nằm trong repo đã đổi tên khác repo đề (repo nộp bài): %s · repo nguồn đã xoá %s"
          % (pct(renamed, n), pct(no_head, n)))
    print()
    print("Riêng repo hackathon Day 15: %d PR nhầm từ %d tài khoản" % (len(hk), len(hk_accounts)))
    print()
    print("Theo repo đề (tên repo đề là repo công khai của khoá):")
    for repo in repos:
        print("  %-60s %d" % (repo, per_repo.get(repo, 0)))


if __name__ == "__main__":
    sys.exit(main())
