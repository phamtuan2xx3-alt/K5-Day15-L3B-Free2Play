"""Unit tests Phase 2: Hướng 1 — GitHub Live Guard (codebase/github_guard.py + agent AUDIT_GITHUB)."""
import io
import json
import os
import socket
import sys
import urllib.error
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODEBASE = os.path.join(ROOT, "codebase")
if CODEBASE not in sys.path:
    sys.path.insert(0, CODEBASE)

import agent  # noqa: E402
import ai  # noqa: E402
import github_guard  # noqa: E402
import tracing  # noqa: E402


class _MockResponse:
    def __init__(self, status: int, body: bytes | str, headers: dict | None = None):
        self.status = status
        self._body = body.encode("utf-8") if isinstance(body, str) else body
        self.headers = headers or {}

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _http_err(url: str, code: int, body: str = "", headers: dict | None = None) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url,
        code,
        "HTTP Error",
        headers or {},
        io.BytesIO(body.encode("utf-8")),
    )


def _public_dns_addrinfo(host, port, type=0):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("140.82.121.6", 443))]


_CLEAN_TEAMS = (
    "# TEAMS\n"
    "- Tên nhóm: Free2Play\n"
    "- Lớp: L3B\n"
    "- Track: A\n"
    "- Link repo: https://github.com/phamtuan2xx3-alt/K5-Day15-L3B-Free2Play\n\n"
    "| STT | Họ và tên | Mã học viên | Vai trò | Phần việc chính |\n"
    "|---|---|---|---|---|\n"
    "| 1 | Phạm Quang Tuấn | 2A202603824 | Đội trưởng | Điều phối |\n"
    "| 2 | Đỗ Hồng Vỹ | 2A202604107 | Thành viên | Tools |\n"
    "| 3 | Chu Văn Nhật | 2A202603848 | Thành viên | Eval |\n"
)

_CLEAN_CANVAS = (
    "# Canvas\n| # | Dòng | Nhóm điền |\n|---|---|---|\n"
    "| 1 | Track | A6 |\n| 2 | User | HV L3 |\n| 3 | Pain | Mất thời gian rà lỗi |\n"
    "| 4 | Bằng chứng | 20/25 |\n| 5 | Lát cắt | 1 câu |\n| 6 | Giới hạn | Người quyết |\n| 7 | Phân công | Tuấn, Vỹ, Nhật |\n"
)

_CLEAN_SPEC = "# Spec\n## §7. Đánh giá\n- Chuẩn đạt: >= 80%\n## §10. Phân công\n- Phạm Quang Tuấn: Agent\n"
_CLEAN_EVIDENCE = "# Evidence\n- Khảo sát n = 25.\n"
_CLEAN_METRIC = (
    "metrics:\n"
    "  - name: pass_rate\n"
    "  - name: hard_flags_recall\n"
    "  - name: citation_accuracy\n"
)
_CLEAN_BENCH = "\n".join(
    ["id,input,expected,pass_criterion,type,source"]
    + [f"S{i:02d},in {i},exp {i},crit {i},{'kho' if i <= 5 else ('tu_choi' if i <= 7 else 'thuong')},{'nguoi_dung: R1' if i <= 4 else 'tu_viet'}" for i in range(1, 11)]
)


class TestPhase2ParseAndSSRF(unittest.TestCase):
    def test_parse_github_target_valid_and_malicious_urls(self):
        self.assertEqual(
            github_guard.parse_github_target("https://github.com/phamtuan2xx3-alt/K5-Day15-L3B-Free2Play"),
            {
                "owner": "phamtuan2xx3-alt",
                "repo": "K5-Day15-L3B-Free2Play",
                "full_name": "phamtuan2xx3-alt/K5-Day15-L3B-Free2Play",
                "url": "https://github.com/phamtuan2xx3-alt/K5-Day15-L3B-Free2Play",
            },
        )
        self.assertEqual(
            github_guard.parse_github_url("repoksv.tuanpq.com/https://github.com/owner/repo")["full_name"],
            "owner/repo",
        )
        self.assertEqual(
            github_guard.parse_github_target("/owner/repo")["full_name"],
            "owner/repo",
        )
        self.assertEqual(
            github_guard.parse_github_target("owner/repo")["full_name"],
            "owner/repo",
        )
        # Chuẩn hoá 1 dấu / do trình duyệt/proxy gộp: https:/github.com/...
        self.assertEqual(
            github_guard.parse_github_target("https:/github.com/owner/repo")["url"],
            "https://github.com/owner/repo",
        )
        self.assertEqual(
            github_guard.parse_github_target("/https:/github.com/owner/repo")["full_name"],
            "owner/repo",
        )

        # Chặn SSRF, scheme khác https, domain giả mạo, path traversal, internal routes
        blocked = [
            "http://169.254.169.254/latest/meta-data",
            "http:/169.254.169.254/latest/meta-data",
            "https://169.254.169.254/latest/meta-data",
            "http://127.0.0.1/owner/repo",
            "https://127.0.0.1/owner/repo",
            "http://github.com.evil.com/owner/repo",
            "https://github.com.evil.com/owner/repo",
            "http://github.com/owner/repo",
            "file:///etc/passwd",
            "https://github.com/../../etc/passwd",
            "/api/scan",
            "/auth/google",
            "evidence/summary.md",
        ]
        for bad in blocked:
            self.assertIsNone(github_guard.parse_github_target(bad), msg=f"Should block: {bad}")

    def test_dns_private_ip_and_redirect_ssrf_blocked(self):
        for private_ip in ("169.254.169.254", "127.0.0.1", "10.0.0.5", "172.16.0.1", "192.168.1.1", "::1", "fe80::1"):
            fake_info = [(socket.AF_INET6 if ":" in private_ip else socket.AF_INET, socket.SOCK_STREAM, 6, "", (private_ip, 443))]
            with patch("socket.getaddrinfo", return_value=fake_info):
                with self.assertRaises(github_guard.SSRFBlockedError):
                    github_guard._assert_safe_url("https://api.github.com/repos/a/b")

        # Kiểm chặn redirect sang host/IP không hợp lệ
        handler = github_guard._SafeRedirectHandler()
        req = github_guard.urllib.request.Request("https://api.github.com/repos/a/b")
        with self.assertRaises(github_guard.SSRFBlockedError):
            handler.redirect_request(req, None, 302, "Found", {}, "http://169.254.169.254/latest/meta-data")
        with self.assertRaises(github_guard.SSRFBlockedError):
            handler.redirect_request(req, None, 302, "Found", {}, "https://evil.example/payload")

    def test_http_get_bytes_bounded_stream_prevents_oom(self):
        class _ChunkedStream:
            def __init__(self, total_bytes: int):
                self.status = 200
                self.headers = {}
                self._remaining = total_bytes

            def read(self, amt: int = -1):
                if self._remaining <= 0:
                    return b""
                n = self._remaining if amt < 0 else min(amt, self._remaining)
                self._remaining -= n
                return b"x" * n

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        class _FakeOpener:
            def open(self, req, timeout=12):
                return _ChunkedStream(500_000)

        with (
            patch("socket.getaddrinfo", side_effect=_public_dns_addrinfo),
            patch("urllib.request.build_opener", return_value=_FakeOpener()),
        ):
            status, _, body = github_guard._http_get_bytes(
                "https://raw.githubusercontent.com/a/b/main/big.md",
                {},
                max_bytes=1024,
            )
        self.assertEqual(status, 200)
        self.assertEqual(len(body), 1024)


class TestPhase2Snapshot4Layers(unittest.TestCase):
    def setUp(self):
        github_guard.clear_memory_cache()

    def _run_with_router(self, url: str, router):
        seen_headers = []

        class FakeOpener:
            def open(self, req, timeout=12):
                seen_headers.append({k.lower(): v for k, v in req.header_items()})
                return router(req.full_url)

        with (
            patch("socket.getaddrinfo", side_effect=_public_dns_addrinfo),
            patch("urllib.request.build_opener", return_value=FakeOpener()),
        ):
            snap = github_guard.fetch_github_repo_snapshot(url, token="ghp_testtoken123")
        return snap, seen_headers

    def test_clean_repo_and_cache(self):
        def router(u):
            if u == "https://api.github.com/repos/team/clean-repo":
                return _MockResponse(200, json.dumps({"private": False, "fork": False, "default_branch": "main"}))
            if "/commits?" in u:
                return _MockResponse(200, "[]")
            if u == "https://api.github.com/repos/team/clean-repo/git/trees/main?recursive=1":
                tree = [
                    {"type": "blob", "path": p}
                    for p in ("TEAMS.md", "canvas.md", "spec.md", "evidence/summary.md", "eval/benchmark.csv", "eval/metric_spec.yaml")
                ]
                return _MockResponse(200, json.dumps({"sha": "deadbeef", "tree": tree}))
            raw_map = {
                "https://raw.githubusercontent.com/team/clean-repo/main/TEAMS.md": _CLEAN_TEAMS,
                "https://raw.githubusercontent.com/team/clean-repo/main/canvas.md": _CLEAN_CANVAS,
                "https://raw.githubusercontent.com/team/clean-repo/main/spec.md": _CLEAN_SPEC,
                "https://raw.githubusercontent.com/team/clean-repo/main/evidence/summary.md": _CLEAN_EVIDENCE,
                "https://raw.githubusercontent.com/team/clean-repo/main/eval/benchmark.csv": _CLEAN_BENCH,
                "https://raw.githubusercontent.com/team/clean-repo/main/eval/metric_spec.yaml": _CLEAN_METRIC,
            }
            if u in raw_map:
                return _MockResponse(200, raw_map[u])
            raise _http_err(u, 404)

        snap, seen_headers = self._run_with_router("https://github.com/team/clean-repo", router)
        self.assertTrue(snap["ok"])
        self.assertFalse(snap["degraded_mode"])
        self.assertEqual(snap["hard_flags"], [])
        self.assertEqual(snap["missing_required"], [])
        self.assertEqual(snap["identity"]["mode"], "team")
        self.assertEqual(seen_headers[0].get("user-agent"), "RepoKSV-Auditor/1.0")
        self.assertEqual(seen_headers[0].get("authorization"), "Bearer ghp_testtoken123")

        # Lần 2 dùng RAM cache
        snap2 = github_guard.fetch_github_repo_snapshot("team/clean-repo")
        self.assertTrue(snap2["from_cache"])

    def test_private_or_404_returns_g10(self):
        def router_404(u):
            raise _http_err(u, 404, json.dumps({"message": "Not Found"}))

        snap, _ = self._run_with_router("https://github.com/team/private-repo", router_404)
        self.assertFalse(snap["ok"])
        self.assertEqual(snap["error_code"], "PRIVATE_OR_NOT_FOUND")
        self.assertIn("G10", snap["g10_message"])

    def test_rate_limit_403_and_429_fallback_to_raw_degraded_mode(self):
        def router_429(u):
            if u.startswith("https://api.github.com/"):
                raise _http_err(
                    u,
                    429,
                    json.dumps({"message": "API rate limit exceeded"}),
                    headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"},
                )
            if u == "https://raw.githubusercontent.com/team/rate-repo/HEAD/TEAMS.md":
                return _MockResponse(200, _CLEAN_TEAMS)
            if u == "https://raw.githubusercontent.com/team/rate-repo/HEAD/spec.md":
                return _MockResponse(200, _CLEAN_SPEC)
            raise _http_err(u, 404)

        snap, _ = self._run_with_router("https://github.com/team/rate-repo", router_429)
        self.assertTrue(snap["ok"])
        self.assertTrue(snap["degraded_mode"])
        self.assertEqual(snap["checks"]["git_fork_pr"]["status"], "unknown_g10")
        self.assertEqual(snap["checks"]["penalty_standard"]["status"], "unknown_g10")
        self.assertIn("TEAMS.md", snap["present_files"])
        self.assertIn("G10", snap["g10_warnings"][0])

    def test_fork_open_pr_and_post_cp2_tamper_and_env_leak(self):
        def router_bad(u):
            if u == "https://api.github.com/repos/stu/forked-repo":
                return _MockResponse(
                    200,
                    json.dumps({
                        "private": False,
                        "fork": True,
                        "default_branch": "main",
                        "parent": {"full_name": "btc/starter-repo"},
                    }),
                )
            if u == "https://api.github.com/repos/btc/starter-repo/pulls?state=open&per_page=30":
                return _MockResponse(
                    200,
                    json.dumps([{
                        "number": 42,
                        "title": "Nop bai",
                        "html_url": "https://github.com/btc/starter-repo/pull/42",
                        "head": {"user": {"login": "stu"}, "repo": {"full_name": "stu/forked-repo"}},
                    }]),
                )
            if "commits?" in u and "metric_spec.yaml" in u:
                return _MockResponse(
                    200,
                    json.dumps([{"sha": "111222333444", "commit": {"committer": {"date": "2026-11-27T14:00:00Z"}}}]),
                )
            if "commits?" in u and "benchmark.csv" in u:
                return _MockResponse(
                    200,
                    json.dumps([{"sha": "aaa111", "commit": {"committer": {"date": "2026-11-27T15:00:00Z"}}}]),
                )
            if u == "https://api.github.com/repos/stu/forked-repo/commits/aaa111":
                # Chỉ thêm dòng CP3 hợp lệ -> không bị gắn PENALTY-STANDARD ở benchmark.csv
                return _MockResponse(
                    200,
                    json.dumps({
                        "files": [{
                            "filename": "eval/benchmark.csv",
                            "patch": "@@ -10,0 +11,1 @@\n+S16,new,exp,crit,thuong,tu_viet",
                        }]
                    }),
                )
            if "commits?" in u:
                return _MockResponse(200, "[]")
            if u == "https://api.github.com/repos/stu/forked-repo/git/trees/main?recursive=1":
                return _MockResponse(
                    200,
                    json.dumps({
                        "sha": "badsha",
                        "tree": [
                            {"type": "blob", "path": "TEAMS.md"},
                            {"type": "blob", "path": ".env"},
                            {"type": "blob", "path": ".env.example"},
                            {"type": "blob", "path": "eval/benchmark.csv"},
                        ],
                    }),
                )
            if u == "https://raw.githubusercontent.com/stu/forked-repo/main/TEAMS.md":
                return _MockResponse(200, _CLEAN_TEAMS)
            if u == "https://raw.githubusercontent.com/stu/forked-repo/main/.env":
                return _MockResponse(200, "API_KEY=sk-live1234567890abcdef\n")
            if u == "https://raw.githubusercontent.com/stu/forked-repo/main/eval/benchmark.csv":
                return _MockResponse(200, _CLEAN_BENCH)
            raise _http_err(u, 404)

        snap, _ = self._run_with_router("https://github.com/stu/forked-repo", router_bad)
        self.assertTrue(snap["ok"])
        rule_ids = {f["rule_id"] for f in snap["hard_flags"]}
        self.assertIn("GIT-FORK-PR", rule_ids)
        self.assertIn("PENALTY-STANDARD", rule_ids)
        self.assertIn("PENALTY-KEY", rule_ids)
        # Chỉ metric_spec.yaml bị tamper, còn benchmark.csv chỉ thêm dòng CP3 hợp lệ
        tampered_files = {c["path"] for c in snap["checks"]["penalty_standard"]["tampered_commits"]}
        self.assertEqual(tampered_files, {"eval/metric_spec.yaml"})
        self.assertEqual(snap["checks"]["tree_scan"]["sensitive_files"], [".env"])


class TestPhase2AgentGitHubRoute(unittest.TestCase):
    def test_agent_audit_github_and_ssrf_block(self):
        github_guard.clear_memory_cache()
        fake_snap = {
            "ok": True,
            "full_name": "team/demo",
            "present_files": ["TEAMS.md", "evidence/summary.md"],
            "missing_required": ["canvas.md", "spec.md", "eval/benchmark.csv", "eval/metric_spec.yaml"],
            "line_counts": {"TEAMS.md": 12, "evidence/summary.md": 5},
            "files_content": {"TEAMS.md": _CLEAN_TEAMS, "evidence/summary.md": _CLEAN_EVIDENCE},
            "hard_flags": [
                {"rule_id": "GIT-FORK-PR", "severity": "rat_cao", "file": "TEAMS.md", "line": 1, "detail": "PR #9 nhầm upstream"}
            ],
            "g10_warnings": [],
            "identity": {"mode": "team", "member_names": ["Phạm Quang Tuấn", "Đỗ Hồng Vỹ"]},
        }

        tracing.begin("GH01")
        try:
            with (
                patch("agent.inspect_github_repo", return_value=fake_snap),
                patch.object(ai, "MODEL_PROVIDER", "fake"),
            ):
                res = agent.answer("AUDIT_GITHUB | https://github.com/team/demo")
        finally:
            summary, _ = tracing.end()

        self.assertIn("GIT-FORK-PR", res["output"])
        self.assertIn("TEAMS.md:L01", res["output"])
        self.assertEqual(summary["model_calls"], 1)

        # Chặn SSRF qua agent.answer mà không gọi model
        tracing.begin("GH_SSRF")
        try:
            with patch.object(ai, "MODEL_PROVIDER", "fake"):
                bad_res = agent.answer("AUDIT_GITHUB | http://169.254.169.254/latest/meta-data")
        finally:
            bad_sum, _ = tracing.end()
        self.assertIn("G10", bad_res["output"])
        self.assertEqual(bad_sum["model_calls"], 0)


if __name__ == "__main__":
    unittest.main()
