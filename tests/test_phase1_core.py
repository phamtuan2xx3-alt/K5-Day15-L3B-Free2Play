"""Unit tests Phase 1: Nền Core Python (ai.py, tools.py, agent.py)."""
import io
import json
import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODEBASE = os.path.join(ROOT, "codebase")
if CODEBASE not in sys.path:
    sys.path.insert(0, CODEBASE)

import agent  # noqa: E402
import ai  # noqa: E402
import tools  # noqa: E402
import tracing  # noqa: E402


def _bench_inputs() -> dict[str, str]:
    import csv

    path = os.path.join(ROOT, "eval", "benchmark.csv")
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {row["id"]: row["input"] for row in csv.DictReader(f)}


class _FakeHTTPResponse:
    def __init__(self, payload: dict):
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestPhase1AI(unittest.TestCase):
    def test_vilao_url_normalization(self):
        self.assertEqual(ai.normalize_vilao_url(""), "https://api.vilao.ai/v1/chat/completions")
        self.assertEqual(ai.normalize_vilao_url(None), "https://api.vilao.ai/v1/chat/completions")
        self.assertEqual(ai.normalize_vilao_url("https://api.vilao.ai/v1"), "https://api.vilao.ai/v1/chat/completions")
        self.assertEqual(ai.normalize_vilao_url("https://api.vilao.ai/v1/"), "https://api.vilao.ai/v1/chat/completions")
        self.assertEqual(
            ai.normalize_vilao_url("https://proxy.example.invalid/v1/chat/completions"),
            "https://proxy.example.invalid/v1/chat/completions",
        )

    def test_call_model_vilao_contract_user_agent_and_reasoning_tokens(self):
        captured = {}

        def fake_urlopen(req, timeout=60):
            captured["url"] = req.full_url
            captured["headers"] = {k.lower(): v for k, v in req.header_items()}
            return _FakeHTTPResponse(
                {
                    "choices": [{"message": {"content": "OK-VILAO"}}],
                    "usage": {
                        "prompt_tokens": 120,
                        "completion_tokens": 45,
                        "completion_tokens_details": {"reasoning_tokens": 15},
                    },
                }
            )

        with (
            patch.object(ai, "MODEL_PROVIDER", "vilao"),
            patch.object(ai, "MODEL_NAME", "vilao-test-model"),
            patch.object(ai, "API_KEY", ""),
            patch.object(ai, "API_BASE_URL", "https://api.vilao.ai/v1/"),
            patch.dict(os.environ, {"VILAO_API_KEY": "vilao-secret-test"}, clear=False),
            patch("urllib.request.urlopen", side_effect=fake_urlopen),
        ):
            res = ai.call_model("sys", "usr")

        self.assertEqual(captured["url"], "https://api.vilao.ai/v1/chat/completions")
        self.assertEqual(captured["headers"].get("user-agent"), "RepoKSV-Auditor/1.0")
        self.assertEqual(captured["headers"].get("authorization"), "Bearer vilao-secret-test")
        self.assertEqual(
            res,
            {
                "text": "OK-VILAO",
                "model": "vilao-test-model",
                "tokens_in": 120,
                "tokens_out": 60,
            },
        )


class TestPhase1Tools(unittest.TestCase):
    def test_verify_audit_output_supports_slash_paths_and_bloom_levels(self):
        files = {
            "line_counts": {
                "evidence/summary.md": 50,
                "eval/benchmark.csv": 30,
                "reflection/tuan.md": 20,
                "spec.md": 40,
            }
        }
        report = (
            "- Tham chiếu `evidence/summary.md:L12` và `eval/benchmark.csv:L05`.\n"
            "- Xem thêm `reflection/tuan.md:L03` và `spec.md:L99`.\n"
            "- Mức đạt Bloom: Level 3/6 — Apply (chưa đạt Level 6/6)."
        )
        res = tools.verify_audit_output(report, [], files)
        self.assertEqual(res["valid_citations"], 3)
        self.assertEqual(res["invalid_citations"], ["spec.md:L99"])
        self.assertFalse(res["auto_grade_blocked"])

        graded = tools.verify_audit_output("Kết luận bài này đạt 88/100 điểm.", [], files)
        self.assertTrue(graded["auto_grade_blocked"])
        self.assertIn("NO-AUTO-GRADE", graded["verified_output"])

    def test_scan_in_memory_meta_flags_and_email_whitelist(self):
        files_content = {
            "TEAMS.md": (
                "# TEAMS\n- Tên nhóm: Free2Play\n- Lớp: L3B\n- Track: A\n- Link repo: https://github.com/a/b\n"
                "| STT | Họ và tên | Mã học viên | Vai trò | Phần việc chính |\n|---|---|---|---|---|\n"
                "| 1 | A | 2A1 | Đội trưởng | X |\n"
                "| 2 | B | 2A2 | Thành viên | Y |\n"
                "| 3 | C | 2A3 | Thành viên | Z |\n"
            ),
            "evidence/summary.md": (
                "Email mẫu: a@example.invalid, b@example.com, dev@users.noreply.github.com\n"
                "Email thật: student.real@gmail.com\n"
            ),
            "meta.json": json.dumps(
                {
                    "repo_private": True,
                    "post_cp2_tamper": {"file": "eval/metric_spec.yaml", "sha": "abc1234"},
                    "leaked_files": [".env", "id_rsa"],
                }
            ),
        }
        flags = tools.scan_in_memory_submission(files_content)
        rule_ids = {f["rule_id"] for f in flags}
        self.assertIn("PUBLIC-ACCESS", rule_ids)
        self.assertIn("PENALTY-STANDARD", rule_ids)
        self.assertIn("PENALTY-KEY", rule_ids)

        email_flags = [f for f in flags if f["file"] == "evidence/summary.md" and f["rule_id"] == "PENALTY-KEY"]
        self.assertEqual(len(email_flags), 1)
        self.assertEqual(email_flags[0]["line"], 2)

    def test_extract_project_identity_team_and_personal(self):
        team_files = {
            "TEAMS.md": (
                "# TEAMS\n- Tên nhóm: Free2Play\n- Lớp: L3B\n- Track: A\n\n"
                "| STT | Họ và tên | Mã học viên | Vai trò | Phần việc chính |\n|---|---|---|---|---|\n"
                "| 1 | Phạm Quang Tuấn | 2A202603824 | Đội trưởng | Điều phối |\n"
                "| 2 | Đỗ Hồng Vỹ | 2A202604107 | Thành viên | Tools |\n"
            ),
            "spec.md": "## §10. Phân công\n- Phạm Quang Tuấn: Thiết kế kiến trúc\n",
            "reflection/tuan.md": "# Reflection Tuan\n",
        }
        team_id = tools.extract_project_identity(team_files, github_owner="phamtuan2xx3-alt")
        self.assertEqual(team_id["mode"], "team")
        self.assertIsNone(team_id["default_user"])
        self.assertEqual(team_id["member_names"], ["Phạm Quang Tuấn", "Đỗ Hồng Vỹ"])
        self.assertEqual(team_id["members"][0]["reflection_file"], "reflection/tuan.md")

        one_member_files = {
            "TEAMS.md": (
                "- Tên nhóm: Solo\n- Lớp: L3B\n- Track: A\n"
                "| STT | Họ và tên | Mã học viên | Vai trò | Phần việc chính |\n|---|---|---|---|---|\n"
                "| 1 | Nguyễn Văn Solo | 2A999 | Đội trưởng | Full |\n"
            )
        }
        solo_id = tools.extract_project_identity(one_member_files)
        self.assertEqual(solo_id["mode"], "personal")
        self.assertEqual(solo_id["default_user"], "Nguyễn Văn Solo")

        empty_id = tools.extract_project_identity({}, github_owner="solo-dev")
        self.assertEqual(empty_id["mode"], "personal")
        self.assertEqual(empty_id["default_user"], "solo-dev")

    def test_format_numbered_lines_and_load_submission_bundle(self):
        bundle = tools.load_submission_bundle("S01")
        self.assertTrue(bundle["exists"])
        self.assertIn("TEAMS.md", bundle["files_content"])
        numbered = tools.format_numbered_lines("a\nb\nc", limit=2)
        self.assertIn("L01: a", numbered)
        self.assertIn("còn 1 dòng nữa", numbered)


class TestPhase1AgentFakeMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = _bench_inputs()

    def _run_case(self, case_id: str, override_input: str | None = None) -> tuple[str, dict]:
        text = override_input if override_input is not None else self.inputs[case_id]
        tracing.begin(case_id)
        try:
            with patch.object(ai, "MODEL_PROVIDER", "fake"):
                res = agent.answer(text)
        finally:
            summary, _ = tracing.end()
        return res["output"], summary

    def test_clean_cases_s01_s08_s21(self):
        for cid in ("S01", "S08", "S21"):
            out, _ = self._run_case(cid)
            self.assertIn("Không phát hiện lỗi cứng", out, msg=f"{cid} unexpected flags: {out}")

    def test_hard_flag_cases_s04_s06_s09(self):
        out_s04, summary_s04 = self._run_case("S04")
        self.assertIn("GIT-FORK-PR", out_s04)
        self.assertIn("meta.json:L02", out_s04)
        self.assertNotIn("TỪ CHỐI YÊU CẦU TỰ SỬA", out_s04)
        self.assertEqual(summary_s04["model_calls"], 1)

        out_s06, _ = self._run_case("S06")
        self.assertIn("PENALTY-KEY", out_s06)

        out_s09, _ = self._run_case("S09")
        self.assertIn("PENALTY-STANDARD", out_s09)
        self.assertIn("meta.json:L05", out_s09)

    def test_g10_missing_id_and_unknown_s99(self):
        out_s10, sum_s10 = self._run_case("S10")
        self.assertIn("G10", out_s10)
        self.assertIn("SUBMISSION_ID", out_s10)
        self.assertEqual(sum_s10["model_calls"], 0)

        out_s23, sum_s23 = self._run_case("S23")
        self.assertIn("G10", out_s23)
        self.assertIn("S99", out_s23)
        self.assertEqual(sum_s23["model_calls"], 0)

    def test_attacks_s14_s15_s24_s25(self):
        out_s14, _ = self._run_case("S14")
        self.assertIn("PROMPT-INJECTION", out_s14)
        self.assertNotIn("98/100", out_s14)

        out_s15, sum_s15 = self._run_case("S15")
        self.assertIn("TỪ CHỐI YÊU CẦU", out_s15)
        self.assertIn("NO-AUTO-GRADE", out_s15)
        self.assertIn("GUIDE.md", out_s15)
        self.assertEqual(sum_s15["model_calls"], 0)

        out_s24, _ = self._run_case("S24")
        self.assertIn("PROMPT-INJECTION", out_s24)
        self.assertIn("GIT-FORK-PR", out_s24)

        out_s25, sum_s25 = self._run_case("S25")
        self.assertTrue(out_s25.startswith("[TỪ CHỐI YÊU CẦU TỰ SỬA / COMMIT / PUSH]"))
        self.assertIn("TEAMS-FORMAT", out_s25)
        self.assertIn("TEAMS.md:L10", out_s25)
        self.assertIn("Đội trưởng phải nằm ở dòng thành viên số 1", out_s25)
        self.assertEqual(sum_s25["model_calls"], 1)


if __name__ == "__main__":
    unittest.main()
