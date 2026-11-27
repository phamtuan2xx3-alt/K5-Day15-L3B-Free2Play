"""Hướng 1: GitHub Live Guard (100% Python stdlib).

Kiểm tra trạng thái repo công khai trên GitHub hoàn toàn trong RAM:
- Chống SSRF cứng: chỉ cho phép HTTPS tới `api.github.com` và `raw.githubusercontent.com`,
  resolve DNS trước khi fetch và chặn mọi IP private/loopback/link-local/reserved + redirect ngoài host.
- 4 lớp kiểm chứng: PUBLIC-ACCESS, GIT-FORK-PR, PENALTY-STANDARD (sau CP2 19:30), PENALTY-KEY + raw files.
- Fallback 2 tầng sang raw.githubusercontent.com khi gặp 403/429 rate-limit.
"""
from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from tools import extract_project_identity, scan_in_memory_submission

USER_AGENT = "RepoKSV-Auditor/1.0"
CP2_CUTOFF_ISO = "2026-11-27T12:30:00Z"  # 19:30 UTC+7 ngày 27/11/2026
DEFAULT_TIMEOUT_S = 12
DEFAULT_CACHE_TTL_S = 300
DEFAULT_MAX_FILES = 120
DEFAULT_MAX_FILE_BYTES = 200 * 1024

ALLOWED_GITHUB_HOSTS = frozenset({"api.github.com", "raw.githubusercontent.com"})
ALLOWED_APP_HOSTS = frozenset({"repoksv.tuanpq.com", "mydomain.com"})

_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
_INTERNAL_ROUTES = frozenset({
    "api",
    "auth",
    "login",
    "privacy",
    "terms",
    "health",
    "assets",
    "static",
    "favicon.ico",
    "robots.txt",
    "eval",
    "evidence",
    "reflection",
    "codebase",
    "data",
    "docs",
    "tests",
    "web",
    "deploy",
    "cost",
    "traces",
})
_DOC_FILE_EXTS = (
    ".md",
    ".csv",
    ".yaml",
    ".yml",
    ".json",
    ".txt",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".html",
    ".css",
)

_SENSITIVE_TREE_PATTERNS = [
    re.compile(r"(^|/)\.env(\..+)?$", re.IGNORECASE),
    re.compile(r"\.pem$", re.IGNORECASE),
    re.compile(r"(^|/)id_rsa$", re.IGNORECASE),
    re.compile(r"(^|/)id_ed25519$", re.IGNORECASE),
    re.compile(r"(^|/)[^/]*credentials[^/]*\.json$", re.IGNORECASE),
    re.compile(r"(^|/)[^/]*service-account[^/]*\.json$", re.IGNORECASE),
]
_ENV_SAFE_ALLOWLIST = frozenset({".env.example", ".env.sample", ".env.template"})

_CANDIDATE_RAW_PATHS = [
    "TEAMS.md",
    "canvas.md",
    "spec.md",
    "evidence/summary.md",
    "evidence_summary.md",
    "eval/benchmark.csv",
    "benchmark.csv",
    "eval/metric_spec.yaml",
    "metric_spec.yaml",
    "README.md",
]

_RAM_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


class SSRFBlockedError(ValueError):
    """Ngoại lệ khi phát hiện URL hoặc IP có nguy cơ SSRF."""


def clear_memory_cache() -> None:
    """Xoá cache RAM trong process (hữu ích cho unit test)."""
    _RAM_CACHE.clear()


def _is_valid_owner_repo(owner: str, repo: str, *, bare: bool = False) -> bool:
    if not owner or not repo:
        return False
    if ".." in owner or ".." in repo:
        return False
    if owner.startswith(".") or owner.endswith(".") or repo.startswith("."):
        return False
    if not _SEGMENT_RE.fullmatch(owner) or not _SEGMENT_RE.fullmatch(repo):
        return False
    low_owner = owner.lower()
    low_repo = repo.lower()
    if low_owner in _INTERNAL_ROUTES:
        return False
    if bare and (low_repo.endswith(_DOC_FILE_EXTS) or low_repo in _INTERNAL_ROUTES):
        return False
    # Chặn trường hợp nhập IP làm owner (vd 169.254.169.254/latest)
    try:
        ipaddress.ip_address(owner)
        return False
    except ValueError:
        pass
    return True


def _clean_repo_name(repo: str) -> str:
    if repo.endswith(".git") and len(repo) > 4:
        return repo[:-4]
    return repo


def parse_github_target(text: str) -> dict[str, str] | None:
    """Phân tích URL GitHub hoặc URL-hack an toàn; trả về None nếu không hợp lệ hoặc có dấu hiệu SSRF.

    Hỗ trợ:
    - https://github.com/<owner>/<repo>
    - github.com/<owner>/<repo>
    - repoksv.tuanpq.com/<owner>/<repo> hoặc /https://github.com/<owner>/<repo>
    - /<owner>/<repo> hoặc <owner>/<repo>
    """
    raw = (text or "").strip()
    if not raw or ".." in raw or "\\" in raw:
        return None

    # Chặn dứt khoát mọi scheme khác https (http://, file://, ftp://, ...)
    scheme_matches = re.findall(r"([A-Za-z][A-Za-z0-9+.-]*)://", raw)
    if any(s.lower() != "https" for s in scheme_matches):
        return None

    # 1. Tìm URL https://github.com/owner/repo trong chuỗi (bao gồm /https://github.com/...)
    m_gh_https = re.search(
        r"https://(?:www\.)?github\.com/([A-Za-z0-9._-]{1,100})/([A-Za-z0-9._-]{1,100})(?:[/?#]|$)",
        raw,
        re.IGNORECASE,
    )
    if m_gh_https:
        owner = m_gh_https.group(1)
        repo = _clean_repo_name(m_gh_https.group(2))
        if _is_valid_owner_repo(owner, repo):
            return {
                "owner": owner,
                "repo": repo,
                "full_name": f"{owner}/{repo}",
                "url": f"https://github.com/{owner}/{repo}",
            }
        return None

    # Nếu có URL https:// khác mà không phải app host được phép -> từ chối
    m_any_https = re.search(r"https://([^/\s?#]+)(/[^\s?#]*)?", raw, re.IGNORECASE)
    if m_any_https:
        host = m_any_https.group(1).split("@")[-1].split(":")[0].lower()
        path_part = (m_any_https.group(2) or "").lstrip("/")
        if host in ALLOWED_APP_HOSTS:
            return parse_github_target(path_part)
        return None

    # 2. Hỗ trợ dạng không scheme: github.com/owner/repo hoặc repoksv.tuanpq.com/owner/repo
    m_bare_domain = re.search(
        r"(?:^|[\s|:/])(?:www\.)?(github\.com|repoksv\.tuanpq\.com|mydomain\.com)/([A-Za-z0-9._-]{1,100})/([A-Za-z0-9._-]{1,100})(?:[/?#]|$)",
        raw,
        re.IGNORECASE,
    )
    if m_bare_domain:
        # Chặn domain giả mạo kiểu github.com.evil.com
        matched_start = m_bare_domain.start()
        prefix_slice = raw[max(0, matched_start - 1):m_bare_domain.end()]
        if re.search(r"github\.com\.[A-Za-z0-9-]", raw, re.IGNORECASE):
            return None
        owner = m_bare_domain.group(2)
        repo = _clean_repo_name(m_bare_domain.group(3))
        if _is_valid_owner_repo(owner, repo):
            _ = prefix_slice
            return {
                "owner": owner,
                "repo": repo,
                "full_name": f"{owner}/{repo}",
                "url": f"https://github.com/{owner}/{repo}",
            }
        return None

    # Chặn các chuỗi có host giả mạo github.com.evil.com
    if re.search(r"github\.com\.[A-Za-z0-9-]", raw, re.IGNORECASE):
        return None

    # 3. Hỗ trợ URL-hack /owner/repo hoặc chuỗi thuần owner/repo (hoặc sau AUDIT_GITHUB | ...)
    candidate = raw
    m_cmd = re.match(r"^AUDIT_GITHUB\s*\|\s*(.+)$", raw, re.IGNORECASE)
    if m_cmd:
        candidate = m_cmd.group(1).strip()
        if ".." in candidate or "://" in candidate:
            return parse_github_target(candidate)

    candidate = candidate.split("?", 1)[0].split("#", 1)[0].strip()
    if candidate.startswith("/") and candidate.count("/") == 2:
        candidate = candidate[1:]

    m_pair = re.fullmatch(r"([A-Za-z0-9._-]{1,100})/([A-Za-z0-9._-]{1,100})", candidate)
    if m_pair:
        owner = m_pair.group(1)
        repo = _clean_repo_name(m_pair.group(2))
        if _is_valid_owner_repo(owner, repo, bare=True):
            return {
                "owner": owner,
                "repo": repo,
                "full_name": f"{owner}/{repo}",
                "url": f"https://github.com/{owner}/{repo}",
            }

    return None


parse_github_url = parse_github_target


def _is_forbidden_ip(ip_text: str) -> bool:
    clean = (ip_text or "").split("%", 1)[0].strip()
    try:
        ip_obj = ipaddress.ip_address(clean)
    except ValueError:
        return True
    return bool(
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
    )


def _assert_safe_url(url: str) -> None:
    """Kiểm tra URL đích thuộc whitelist GitHub, dùng HTTPS và DNS không trỏ vào IP nội bộ."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() != "https":
        raise SSRFBlockedError(f"Chỉ cho phép HTTPS, từ chối scheme: {parsed.scheme!r}")
    if parsed.username or parsed.password:
        raise SSRFBlockedError("Từ chối URL chứa thông tin xác thực userinfo.")
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_GITHUB_HOSTS:
        raise SSRFBlockedError(f"Từ chối host ngoài danh sách cho phép: {host!r}")
    port = parsed.port
    if port not in (None, 443):
        raise SSRFBlockedError(f"Từ chối cổng không hợp lệ: {port}")

    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise RuntimeError(f"Không phân giải được DNS cho {host}: {exc}") from exc
    if not infos:
        raise RuntimeError(f"Không có bản ghi IP cho {host}.")

    for info in infos:
        sockaddr = info[4]
        ip_addr = sockaddr[0] if sockaddr else ""
        if _is_forbidden_ip(ip_addr):
            raise SSRFBlockedError(f"Chặn SSRF: {host} phân giải ra IP cấm ({ip_addr}).")


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Chặn HTTP redirect trỏ sang scheme/host/IP ngoài danh sách an toàn."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        abs_url = urllib.parse.urljoin(req.full_url, newurl)
        _assert_safe_url(abs_url)
        return super().redirect_request(req, fp, code, msg, headers, abs_url)


def _http_get_bytes(
    url: str,
    headers: dict[str, str],
    timeout: int = DEFAULT_TIMEOUT_S,
) -> tuple[int, dict[str, str], bytes]:
    _assert_safe_url(url)
    req_headers = {"User-Agent": USER_AGENT}
    req_headers.update(headers)
    req = urllib.request.Request(url, method="GET", headers=req_headers)
    opener = urllib.request.build_opener(_SafeRedirectHandler())
    try:
        with opener.open(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200) or 200
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            return int(status), resp_headers, resp.read()
    except urllib.error.HTTPError as e:
        resp_headers = {k.lower(): v for k, v in (e.headers.items() if e.headers else [])}
        body = e.read() if hasattr(e, "read") else b""
        return int(e.code), resp_headers, body


def _api_headers(token: str | None = None) -> dict[str, str]:
    tok = (token if token is not None else os.environ.get("GITHUB_TOKEN") or "").strip()
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
    }
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    return headers


def _raw_headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT}


def _is_rate_limited(status: int, headers: dict[str, str], body: bytes) -> bool:
    if status == 429:
        return True
    if status == 403:
        if headers.get("x-ratelimit-remaining") == "0":
            return True
        text = body.decode("utf-8", "replace").lower()
        if "rate limit" in text or "abuse detection" in text:
            return True
    return False


def _is_sensitive_tree_path(path: str) -> bool:
    base = os.path.basename(path).lower()
    if base in _ENV_SAFE_ALLOWLIST:
        return False
    return any(pat.search(path) for pat in _SENSITIVE_TREE_PATTERNS)


def _select_paths_from_tree(tree_items: list[dict[str, Any]], max_files: int) -> tuple[list[str], list[str]]:
    """Chọn danh sách file trọng yếu để tải qua raw và lọc file nhạy cảm trên tree."""
    sensitive_paths: list[str] = []
    blob_paths: list[str] = []
    for item in tree_items:
        if item.get("type") != "blob":
            continue
        path = str(item.get("path") or "").strip()
        if not path:
            continue
        blob_paths.append(path)
        if _is_sensitive_tree_path(path):
            sensitive_paths.append(path)

    blob_set = set(blob_paths)
    selected: list[str] = []
    for cand in _CANDIDATE_RAW_PATHS:
        if cand in blob_set and cand not in selected:
            selected.append(cand)

    reflection_paths = sorted(
        p for p in blob_paths if p.startswith("reflection/") and p.endswith(".md")
    )[:5]
    for rp in reflection_paths:
        if rp not in selected:
            selected.append(rp)

    # Nếu chưa có đủ file chuẩn nhưng repo có .env* hoặc file cấu hình khác
    for sp in sensitive_paths:
        if sp not in selected and len(selected) < max_files:
            selected.append(sp)

    return selected[:max_files], sensitive_paths


def _fetch_raw_files(
    owner: str,
    repo: str,
    branch: str,
    paths: list[str],
    *,
    max_file_bytes: int,
    timeout: int,
) -> tuple[dict[str, str], list[str]]:
    """Tải nội dung các file vào RAM qua raw.githubusercontent.com."""
    files_content: dict[str, str] = {}
    oversized_files: list[str] = []
    quoted_branch = urllib.parse.quote(branch, safe="/")
    for rel_path in paths:
        quoted_path = urllib.parse.quote(rel_path, safe="/")
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{quoted_branch}/{quoted_path}"
        status, _, body = _http_get_bytes(raw_url, _raw_headers(), timeout=timeout)
        if status != 200:
            continue
        if len(body) > max_file_bytes:
            oversized_files.append(rel_path)
            body = body[:max_file_bytes]
        files_content[rel_path] = body.decode("utf-8-sig", errors="replace")
    return files_content, oversized_files


def _check_fork_open_prs(
    owner: str,
    repo: str,
    repo_meta: dict[str, Any],
    headers: dict[str, str],
    timeout: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    """Lớp 2: Kiểm tra GIT-FORK-PR nếu repo là fork và còn PR mở lên repo gốc."""
    is_fork = bool(repo_meta.get("fork"))
    parent_full = str((repo_meta.get("parent") or {}).get("full_name") or "").strip()
    if not is_fork or not parent_full or "/" not in parent_full:
        return {"status": "pass", "is_fork": is_fork, "parent": parent_full, "open_prs": []}, [], False

    p_owner, p_repo = parent_full.split("/", 1)
    pulls_url = f"https://api.github.com/repos/{p_owner}/{p_repo}/pulls?state=open&per_page=30"
    status, resp_headers, body = _http_get_bytes(pulls_url, headers, timeout=timeout)
    if _is_rate_limited(status, resp_headers, body):
        return {
            "status": "unknown_g10",
            "is_fork": True,
            "parent": parent_full,
            "detail": "CHƯA KIỂM ĐƯỢC (G10) — Hết hạn mức GitHub API khi kiểm tra PR upstream.",
        }, [], True
    if status != 200:
        return {
            "status": "unknown_g10",
            "is_fork": True,
            "parent": parent_full,
            "detail": f"CHƯA KIỂM ĐƯỢC (G10) — Không đọc được danh sách PR trên {parent_full} (HTTP {status}).",
        }, [], False

    pulls = json.loads(body.decode("utf-8", "replace"))
    matched_prs = []
    flags = []
    expected_full = f"{owner}/{repo}".lower()
    for pr in pulls if isinstance(pulls, list) else []:
        head = pr.get("head") or {}
        head_user = str((head.get("user") or {}).get("login") or "").lower()
        head_repo_full = str((head.get("repo") or {}).get("full_name") or "").lower()
        if head_user == owner.lower() or head_repo_full == expected_full:
            num = pr.get("number")
            matched_prs.append({"number": num, "title": pr.get("title", ""), "url": pr.get("html_url", "")})
            flags.append({
                "rule_id": "GIT-FORK-PR",
                "severity": "rat_cao",
                "file": "TEAMS.md",
                "line": 1,
                "detail": (
                    f"Phát hiện PR #{num} đang mở nhầm từ `{owner}/{repo}` lên repo gốc `{parent_full}` "
                    "— nguy cơ lộ bài, cần đóng PR trên repo gốc ngay."
                ),
            })

    return {
        "status": "fail" if flags else "pass",
        "is_fork": True,
        "parent": parent_full,
        "open_prs": matched_prs,
    }, flags, False


def _patch_touches_spec_s7(patch: str) -> bool:
    """Chỉ coi là sửa chuẩn CP2 nếu dòng bị xoá/sửa (-) nằm trong mục §7 / Chuẩn đạt."""
    in_s7 = False
    for ln in (patch or "").splitlines():
        clean = ln[1:] if ln[:1] in ("+", "-", " ") else ln
        if re.search(r"##\s*§7\b|Chuẩn\s*\"đạt\"", clean, re.IGNORECASE):
            in_s7 = True
        elif re.match(r"^\s*##\s*§(?:8|9|10)\b", clean):
            in_s7 = False
        if in_s7 and ln.startswith("-") and not ln.startswith("---"):
            return True
    return False


def _patch_deletes_old_benchmark_rows(patch: str) -> bool:
    """Chỉ coi là gian lận nếu dòng xoá (-) là dòng dữ liệu câu thử cũ trong benchmark.csv."""
    for ln in (patch or "").splitlines():
        if not ln.startswith("-") or ln.startswith("---"):
            continue
        body = ln[1:].strip()
        if not body or body.lower().startswith("id,input,expected"):
            continue
        if "," in body:
            return True
    return False


def _check_post_cp2_tamper(
    owner: str,
    repo: str,
    headers: dict[str, str],
    timeout: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    """Lớp 3: Kiểm tra commit sau mốc chốt CP2 (19:30 27/11) trên 3 file chuẩn."""
    watched = ("eval/metric_spec.yaml", "spec.md", "eval/benchmark.csv")
    flags: list[dict[str, Any]] = []
    tampered_commits: list[dict[str, Any]] = []

    for path in watched:
        q_path = urllib.parse.quote(path, safe="")
        url = (
            f"https://api.github.com/repos/{owner}/{repo}/commits"
            f"?since={CP2_CUTOFF_ISO}&per_page=15&path={q_path}"
        )
        status, resp_headers, body = _http_get_bytes(url, headers, timeout=timeout)
        if _is_rate_limited(status, resp_headers, body):
            return {
                "status": "unknown_g10",
                "detail": "CHƯA KIỂM ĐƯỢC (G10) — Hết hạn mức GitHub API khi kiểm tra lịch sử commit sau CP2.",
            }, [], True
        if status != 200:
            continue
        commits = json.loads(body.decode("utf-8", "replace"))
        if not isinstance(commits, list) or not commits:
            continue

        for c in commits:
            sha = str(c.get("sha") or "")[:7]
            full_sha = str(c.get("sha") or "")
            c_date = str(((c.get("commit") or {}).get("committer") or {}).get("date") or "")
            if path == "eval/metric_spec.yaml":
                tampered_commits.append({"path": path, "sha": sha, "date": c_date})
                flags.append({
                    "rule_id": "PENALTY-STANDARD",
                    "severity": "rat_cao",
                    "file": path,
                    "line": 1,
                    "detail": (
                        f"Phát hiện commit `{sha}` ({c_date}) chỉnh sửa `{path}` sau mốc chốt CP2 (19:30) — 0 điểm khối R4."
                    ),
                })
                break

            # Với spec.md và eval/benchmark.csv, kiểm chi tiết patch của commit
            commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{full_sha}"
            c_status, c_headers, c_body = _http_get_bytes(commit_url, headers, timeout=timeout)
            if _is_rate_limited(c_status, c_headers, c_body):
                return {
                    "status": "unknown_g10",
                    "detail": "CHƯA KIỂM ĐƯỢC (G10) — Hết hạn mức GitHub API khi đọc patch commit sau CP2.",
                }, flags, True
            if c_status != 200:
                continue
            detail_json = json.loads(c_body.decode("utf-8", "replace"))
            for fobj in detail_json.get("files") or []:
                if fobj.get("filename") != path:
                    continue
                patch = str(fobj.get("patch") or "")
                violated = (
                    _patch_touches_spec_s7(patch)
                    if path == "spec.md"
                    else _patch_deletes_old_benchmark_rows(patch)
                )
                if violated:
                    tampered_commits.append({"path": path, "sha": sha, "date": c_date})
                    flags.append({
                        "rule_id": "PENALTY-STANDARD",
                        "severity": "rat_cao",
                        "file": path,
                        "line": 1,
                        "detail": (
                            f"Commit `{sha}` ({c_date}) đã sửa chuẩn đạt / xoá câu thử cũ ở `{path}` sau mốc chốt CP2 — 0 điểm khối R4."
                        ),
                    })
                    break

    return {
        "status": "fail" if flags else "pass",
        "since": CP2_CUTOFF_ISO,
        "tampered_commits": tampered_commits,
    }, flags, False


def _compute_missing_required(files_content: dict[str, str]) -> list[str]:
    keys = set(files_content.keys())
    missing: list[str] = []
    for req in ("TEAMS.md", "canvas.md", "spec.md"):
        if req not in keys:
            missing.append(req)
    if "evidence/summary.md" not in keys and "evidence_summary.md" not in keys:
        missing.append("evidence/summary.md")
    if "eval/benchmark.csv" not in keys and "benchmark.csv" not in keys:
        missing.append("eval/benchmark.csv")
    if "eval/metric_spec.yaml" not in keys and "metric_spec.yaml" not in keys:
        missing.append("eval/metric_spec.yaml")
    return missing


def _dedup_flags(flags: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, int, str]] = set()
    out: list[dict[str, Any]] = []
    for f in flags:
        sig = (
            str(f.get("rule_id") or ""),
            str(f.get("file") or ""),
            int(f.get("line") or 1),
            str(f.get("detail") or ""),
        )
        if sig not in seen:
            seen.add(sig)
            out.append(f)
    return out


def fetch_github_repo_snapshot(
    target_or_url: str | dict[str, str],
    *,
    token: str | None = None,
    force_refresh: bool = False,
    ttl_seconds: int = DEFAULT_CACHE_TTL_S,
    max_files: int = DEFAULT_MAX_FILES,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    timeout: int = DEFAULT_TIMEOUT_S,
    db: Any = None,
) -> dict[str, Any]:
    """Thực hiện 4 lớp kiểm tra GitHub hoàn toàn trong RAM, có cache TTL và fallback khi dính 403/429."""
    target = parse_github_target(target_or_url) if isinstance(target_or_url, str) else target_or_url
    if not target or not target.get("owner") or not target.get("repo"):
        return {
            "ok": False,
            "error_code": "INVALID_OR_BLOCKED_URL",
            "g10_message": "CHƯA KIỂM ĐƯỢC (G10) — URL GitHub không hợp lệ hoặc bị chặn bởi bộ lọc an toàn SSRF.",
            "degraded_mode": False,
            "hard_flags": [],
            "checks": {},
            "files_content": {},
            "line_counts": {},
            "missing_required": [],
            "present_files": [],
            "identity": {"mode": "personal", "default_user": "Người dùng cá nhân", "members": [], "member_names": []},
        }

    owner = target["owner"]
    repo = target["repo"]
    cache_key = f"{owner.lower()}/{repo.lower()}"

    now = time.time()
    if not force_refresh and cache_key in _RAM_CACHE:
        exp, cached_snap = _RAM_CACHE[cache_key]
        if now < exp:
            out = dict(cached_snap)
            out["from_cache"] = True
            return out

    headers = _api_headers(token)
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    status, resp_headers, body = _http_get_bytes(repo_url, headers, timeout=timeout)

    degraded_mode = False
    g10_warnings: list[str] = []
    checks: dict[str, Any] = {}
    api_flags: list[dict[str, Any]] = []
    oversized_files: list[str] = []
    default_branch = "main"
    commit_sha = ""
    files_content: dict[str, str] = {}

    if _is_rate_limited(status, resp_headers, body):
        degraded_mode = True
        retry_after = resp_headers.get("retry-after") or resp_headers.get("x-ratelimit-reset") or ""
        g10_warnings.append(
            f"CHƯA KIỂM ĐƯỢC (G10) — GitHub API chạm giới hạn (HTTP {status}"
            + (f", Retry-After/Reset: {retry_after}" if retry_after else "")
            + "); đã chuyển sang chế độ dự phòng đọc trực tiếp qua raw.githubusercontent.com."
        )
        checks["public_access"] = {"status": "unknown_g10", "http_status": status}
        checks["git_fork_pr"] = {
            "status": "unknown_g10",
            "detail": "Không kiểm tra được fork/PR upstream khi API rate-limit.",
        }
        checks["penalty_standard"] = {
            "status": "unknown_g10",
            "detail": "Không kiểm tra được lịch sử commit sau CP2 khi API rate-limit.",
        }

        for candidate_branch in ("HEAD", "main", "master"):
            probe_files, probe_oversized = _fetch_raw_files(
                owner,
                repo,
                candidate_branch,
                _CANDIDATE_RAW_PATHS,
                max_file_bytes=max_file_bytes,
                timeout=timeout,
            )
            if probe_files:
                files_content = probe_files
                oversized_files = probe_oversized
                default_branch = candidate_branch
                break

        if not files_content:
            return {
                "ok": False,
                "error_code": "RATE_LIMITED",
                "g10_message": g10_warnings[0],
                "target": target,
                "owner": owner,
                "repo": repo,
                "full_name": f"{owner}/{repo}",
                "degraded_mode": True,
                "from_cache": False,
                "g10_warnings": g10_warnings,
                "checks": checks,
                "hard_flags": [],
                "files_content": {},
                "line_counts": {},
                "missing_required": ["TEAMS.md", "canvas.md", "spec.md", "evidence/summary.md", "eval/benchmark.csv", "eval/metric_spec.yaml"],
                "present_files": [],
                "identity": extract_project_identity({}, github_owner=owner),
            }

    elif status in (403, 404):
        return {
            "ok": False,
            "error_code": "PRIVATE_OR_NOT_FOUND",
            "g10_message": (
                f"CHƯA KIỂM ĐƯỢC (G10) — Không truy cập được `{owner}/{repo}` ở chế độ công khai "
                f"(HTTP {status}: repo đang Private hoặc sai đường dẫn)."
            ),
            "target": target,
            "owner": owner,
            "repo": repo,
            "full_name": f"{owner}/{repo}",
            "degraded_mode": False,
            "from_cache": False,
            "g10_warnings": [],
            "checks": {"public_access": {"status": "fail", "http_status": status}},
            "hard_flags": [],
            "files_content": {},
            "line_counts": {},
            "missing_required": [],
            "present_files": [],
            "identity": extract_project_identity({}, github_owner=owner),
        }

    elif status != 200:
        return {
            "ok": False,
            "error_code": "GITHUB_API_ERROR",
            "g10_message": f"CHƯA KIỂM ĐƯỢC (G10) — GitHub API trả mã lỗi HTTP {status}.",
            "target": target,
            "owner": owner,
            "repo": repo,
            "full_name": f"{owner}/{repo}",
            "degraded_mode": False,
            "from_cache": False,
            "g10_warnings": [],
            "checks": {"public_access": {"status": "fail", "http_status": status}},
            "hard_flags": [],
            "files_content": {},
            "line_counts": {},
            "missing_required": [],
            "present_files": [],
            "identity": extract_project_identity({}, github_owner=owner),
        }

    else:
        repo_meta = json.loads(body.decode("utf-8", "replace"))
        if repo_meta.get("private") is True:
            return {
                "ok": False,
                "error_code": "PRIVATE_OR_NOT_FOUND",
                "g10_message": f"CHƯA KIỂM ĐƯỢC (G10) — Repo `{owner}/{repo}` đang ở chế độ Private.",
                "target": target,
                "owner": owner,
                "repo": repo,
                "full_name": f"{owner}/{repo}",
                "degraded_mode": False,
                "from_cache": False,
                "g10_warnings": [],
                "checks": {"public_access": {"status": "fail", "private": True}},
                "hard_flags": [],
                "files_content": {},
                "line_counts": {},
                "missing_required": [],
                "present_files": [],
                "identity": extract_project_identity({}, github_owner=owner),
            }

        default_branch = str(repo_meta.get("default_branch") or "main")
        checks["public_access"] = {"status": "pass", "private": False, "default_branch": default_branch}

        # Tầng A2: GIT-FORK-PR
        fork_check, fork_flags, fork_limited = _check_fork_open_prs(owner, repo, repo_meta, headers, timeout)
        checks["git_fork_pr"] = fork_check
        api_flags.extend(fork_flags)
        if fork_limited:
            degraded_mode = True
            g10_warnings.append(fork_check.get("detail", ""))

        # Tầng B1: PENALTY-STANDARD sau mốc chốt CP2
        tamper_check, tamper_flags, tamper_limited = _check_post_cp2_tamper(owner, repo, headers, timeout)
        checks["penalty_standard"] = tamper_check
        api_flags.extend(tamper_flags)
        if tamper_limited:
            degraded_mode = True
            g10_warnings.append(tamper_check.get("detail", ""))

        # Tầng B2 + C: Git Trees API + tải file trọng yếu qua raw vào RAM
        q_branch = urllib.parse.quote(default_branch, safe="")
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{q_branch}?recursive=1"
        t_status, t_headers, t_body = _http_get_bytes(tree_url, headers, timeout=timeout)
        selected_paths = list(_CANDIDATE_RAW_PATHS)
        sensitive_paths: list[str] = []

        if _is_rate_limited(t_status, t_headers, t_body):
            degraded_mode = True
            g10_warnings.append("CHƯA KIỂM ĐƯỢC (G10) — Hết hạn mức GitHub API khi đọc cây file; fallback sang raw.githubusercontent.com.")
            checks["tree_scan"] = {"status": "unknown_g10"}
        elif t_status == 200:
            tree_data = json.loads(t_body.decode("utf-8", "replace"))
            commit_sha = str(tree_data.get("sha") or "")
            selected_paths, sensitive_paths = _select_paths_from_tree(tree_data.get("tree") or [], max_files=max_files)
            for sp in sensitive_paths:
                api_flags.append({
                    "rule_id": "PENALTY-KEY",
                    "severity": "rat_cao",
                    "file": sp,
                    "line": 1,
                    "detail": f"Phát hiện file nhạy cảm `{sp}` trên repo công khai — vi phạm trừ 10 điểm.",
                })
            checks["tree_scan"] = {
                "status": "fail" if sensitive_paths else "pass",
                "sensitive_files": sensitive_paths,
                "selected_count": len(selected_paths),
            }
        else:
            checks["tree_scan"] = {"status": "unknown_g10", "http_status": t_status}

        files_content, oversized_files = _fetch_raw_files(
            owner,
            repo,
            default_branch,
            selected_paths,
            max_file_bytes=max_file_bytes,
            timeout=timeout,
        )

    # Tầng D: Quét luật cứng trên RAM + nhận diện danh tính Team/Cá nhân
    content_flags = scan_in_memory_submission(files_content)
    all_flags = _dedup_flags(api_flags + content_flags)
    line_counts = {fname: len(txt.splitlines()) for fname, txt in files_content.items()}
    missing_required = _compute_missing_required(files_content)
    identity = extract_project_identity(files_content, github_owner=owner)

    checks["penalty_key"] = {
        "status": "fail" if any(f.get("rule_id") == "PENALTY-KEY" for f in all_flags) else "pass",
    }

    snapshot: dict[str, Any] = {
        "ok": True,
        "error_code": "",
        "g10_message": "",
        "target": target,
        "owner": owner,
        "repo": repo,
        "full_name": f"{owner}/{repo}",
        "default_branch": default_branch,
        "commit_sha": commit_sha,
        "degraded_mode": degraded_mode,
        "from_cache": False,
        "g10_warnings": g10_warnings,
        "checks": checks,
        "hard_flags": all_flags,
        "missing_required": missing_required,
        "present_files": sorted(files_content.keys()),
        "line_counts": line_counts,
        "files_content": files_content,
        "oversized_files": oversized_files,
        "identity": identity,
    }

    _RAM_CACHE[cache_key] = (now + max(1, int(ttl_seconds)), snapshot)
    if db is not None and hasattr(db, "set_cached_github"):
        try:
            db.set_cached_github(cache_key, commit_sha, snapshot, ttl_seconds=ttl_seconds)
        except Exception:
            pass

    return snapshot
