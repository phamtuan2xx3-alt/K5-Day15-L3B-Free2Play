# Reflection — Đỗ Hồng Vỹ

> Mã học viên: `2A202604107` · Vai trò: Thành viên (Nhóm Free2Play · L3B · Track A).

1. **Vai trò + phần mình làm (trỏ tới file / commit):**
   - Khởi tạo khung công cụ và dữ liệu nền từ CP2: chuẩn hoá 12 tiêu chí từ rubric khoá (`data/rubric.json`), bộ sinh 15 hồ sơ mẫu synthetic `seed = 42` (`data/make_submissions.py`), 5 hàm `@tool` (`scan_hard_rules`, `read_file_lines`, `verify_audit_output`...) và workflow cố định 3 bước tại `b5f42a4`, sau đó vá regex từ chối `S15` và dò dòng `meta.json` (`a8676bd`).
   - Đồng bộ bộ tài liệu CP2 (`README.md`, `canvas.md`, `data/DATA_CARD.md`, `eval/README.md`, `docs/ai-usage.md`, `AGENTS.md`, `spec.md` §1–§3/§8–§10) sau khi gộp khảo sát `n = 25` (`6cf8135`, `d47e7b5`, `ea0706b`).
   - Tổng hợp báo cáo CP4 (`eval/report.md`, `cost/cost-estimate.md`, `spec.md` §7/§8/§10) tại `2016cff`, chấm chéo Lượt 2, sửa lỗi báo nhầm thiếu `TEAM.md` cho repo cá nhân trong `codebase/github_guard.py` (`f1bf2af`) và quay video demo dự phòng.

2. **AI hỗ trợ mình thế nào (việc gì, công cụ gì, chỗ nào phải sửa lại output AI):**
   - Dùng trợ lý AI (coding agent) để gợi ý cấu trúc 5 `@tool`, khung parser regex bắt API key/PII/prompt injection và rà bố cục các file tài liệu theo `02-guide.md`.
   - Phải tự kiểm chứng và sửa lại trực tiếp output AI ở những chỗ rule biên bị quá tay hoặc thiếu hụt: sửa regex `S15` để vừa từ chối chấm `/100` vừa vẫn giữ đủ ngữ cảnh hướng dẫn (`a8676bd`), vá điều kiện `TEAM.md` trong `codebase/github_guard.py` sau khi thử trên repo cá nhân Day 14 bị báo nhầm thiếu file nhóm (`f1bf2af`).
   - Thực hiện kiểm chéo thủ công 5/5 output khung `fake` ở CP2 (`S01, S04, S05, S06, S14`) và chấm tay đối chiếu `eval/run-1.csv`, `eval/run-2.csv` mà không dùng LLM chấm hộ.

3. **Một câu thử trượt của nhóm và mình học được gì từ nó:**
   - Câu **`S12`** ở Lượt 1 (`eval/run-1.csv`) và hiện tượng báo động giả nhỏ ở **`S21`** (bộ lọc hậu kiểm `NO-AUTO-GRADE` bắt nhầm cụm `'42/100 review'`) cho thấy cùng một bài học: quy tắc chỉ đúng "về mặt có xuất hiện thông tin" vẫn không đủ nếu đặt sai chỗ hoặc viết regex quá rộng.
   - Với người dùng sát hạn nộp, một lỗi nghiêm trọng như thiếu `metric_spec.yaml` bị giấu dưới cuối mục (3) nguy hiểm gần bằng việc không phát hiện lỗi; còn cảnh báo giả trên bài sạch `S21` làm học viên mất niềm tin vào công cụ.
   - Vì vậy khi viết công cụ `@tool` và hậu kiểm, mỗi regex và thứ tự trình bày phải kiểm kỹ cả hai chiều: bắt đủ lỗi thật (recall cao) nhưng cũng không làm nhiễu bài sạch.
