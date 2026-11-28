"""Smoke check sau deploy cho RepoKSV (100% Python stdlib)."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def _request(
    url: str,
    method: str = "GET",
    payload: dict | None = None,
    timeout: float = 10.0,
) -> tuple[int, dict[str, str], str]:
    data = None
    headers = {"User-Agent": "RepoKSV-SmokeCheck/1.0"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, resp_headers, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        resp_headers = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        return exc.code, resp_headers, body


def check_health(base_url: str) -> tuple[bool, str]:
    status, _, body = _request(f"{base_url}/health")
    if status != 200:
        return False, f"GET /health tra ve {status}"
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return False, "GET /health khong tra ve JSON hop le"
    return True, f"/health OK ({data.get('status', 'ok')})"


def check_security_headers(base_url: str, strict: bool) -> tuple[bool, str]:
    status, headers, _ = _request(f"{base_url}/")
    if status not in (200, 302, 307):
        return False, f"GET / tra ve {status}"
    required = ["x-content-type-options", "x-frame-options", "content-security-policy"]
    if base_url.startswith("https://") or strict:
        required.append("strict-transport-security")
    missing = [h for h in required if h not in headers]
    if missing:
        if strict:
            return False, f"Thieu security headers: {', '.join(missing)}"
        return True, f"Canh bao (direct uvicorn): thieu Caddy headers {', '.join(missing)}"
    return True, "Security headers day du (CSP, nosniff, X-Frame-Options)"


def check_url_hack_route(base_url: str) -> tuple[bool, str]:
    route = "/phamtuan2xx3-alt/K5-Day15-L3B-Free2Play"
    status, headers, body = _request(f"{base_url}{route}")
    ctype = headers.get("content-type", "")
    if status != 200 or "html" not in ctype.lower():
        return False, f"URL-hack {route} tra ve status={status}, content-type={ctype}"
    if "RepoKSV" not in body and 'id="root"' not in body:
        return False, f"URL-hack {route} khong tra ve SPA HTML RepoKSV"
    return True, f"URL-hack {route} -> 200 SPA HTML"


def check_ssrf_reject(base_url: str) -> tuple[bool, str]:
    bad_targets = [
        "http://169.254.169.254/latest/meta-data/",
        "http://127.0.0.1:8000/health",
        "file:///etc/passwd",
    ]
    for target in bad_targets:
        status, _, body = _request(
            f"{base_url}/api/scan",
            method="POST",
            payload={"target": target},
        )
        if status == 200 or status >= 500:
            return False, f"SSRF payload {target} khong bi chan dung (status={status}, body={body[:120]})"
    return True, "SSRF reject 3/3 payload an toan"


def check_rate_limit(base_url: str) -> tuple[bool, str]:
    statuses: list[int] = []
    for _ in range(7):
        status, _, _ = _request(
            f"{base_url}/api/scan",
            method="POST",
            payload={"target": "S01"},
        )
        statuses.append(status)
        if status == 429:
            return True, f"Rate-limit 429 kich hoat sau {len(statuses)} luot"
        if status == 401:
            return True, "Bo qua rate-limit 429 vi /api/scan dang yeu cau OAuth (401)"
    return False, f"Khong thay HTTP 429 sau 7 luot scan: {statuses}"


def main() -> int:
    parser = argparse.ArgumentParser(description="RepoKSV post-deploy smoke check")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base URL cua server")
    parser.add_argument("--strict-headers", action="store_true", help="Bat buoc du Caddy security headers")
    parser.add_argument("--check-rate-limit", action="store_true", help="Gui burst /api/scan de kiem 429")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    checks = [
        ("Health", lambda: check_health(base_url)),
        ("Security Headers", lambda: check_security_headers(base_url, args.strict_headers)),
        ("URL-Hack Route", lambda: check_url_hack_route(base_url)),
        ("SSRF Guard", lambda: check_ssrf_reject(base_url)),
    ]
    if args.check_rate_limit:
        checks.append(("Rate Limit 429", lambda: check_rate_limit(base_url)))

    failed = 0
    for name, fn in checks:
        try:
            ok, msg = fn()
        except Exception as exc:  # noqa: BLE001
            ok, msg = False, f"Exception: {exc}"
        tag = "PASS" if ok else "FAIL"
        print(f"[{tag}] {name}: {msg}")
        if not ok:
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
