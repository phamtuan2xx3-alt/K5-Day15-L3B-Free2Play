# Reflection — Phạm Quang Tuấn

> Mã học viên: `2A202603824` · Vai trò: Đội trưởng (Nhóm Free2Play · L3B · Track A).

1. **Vai trò + phần mình làm (trỏ tới file / commit):**
   - Làm Đội trưởng điều phối nhánh & nộp các mốc CP1–CP4; chốt [spec.md](spec.md) §3–§9, [canvas.md](canvas.md), [eval/metric_spec.yaml](eval/metric_spec.yaml) và 15 câu thử đầu tại `d3abc65`, sau đó mở rộng đủ 30 câu `S01–S30` ở [eval/benchmark.csv](eval/benchmark.csv) và [data/make_submissions.py](data/make_submissions.py) (`2c6956b`).
   - Thiết kế & xây toàn trình bản chạy thử + hệ thống Web RepoKSV: luồng agent, GitHub Live Guard đọc repo thật trong RAM, Vấn đáp Bloom L0–L6, SQLite/exporters, FastAPI streaming SSE, giao diện React/Tailwind và triển khai EC2/Cloudflare Tunnel + Vercel (`af8c8c1`..`899947d`).
   - Chạy và chấm Lượt 1 `run-1` (`4a03da5`), viết bản cải tiến sau Lượt 1 (`bc24bf0`), chấm Lượt 2 `run-2` (`c23c89c`), tắt `enable_thinking` cho DeepSeek trong `codebase/ai.py` và chạy đủ 50 phiên mô phỏng `cost/simulate-1.csv` (`05cad02`, `82d6445`).

2. **AI hỗ trợ mình thế nào (việc gì, công cụ gì, chỗ nào phải sửa lại output AI):**
   - Dùng coding agent hỗ trợ dựng khung `spec.md`, rà bộ câu thử theo lưới 4 chiều, viết khung script `evidence/mine_repos.py` (đào 135 repo CP1), xây codebase backend/frontend và rà bảo mật (SSRF, CSRF, CSP, prompt-injection sandbox).
   - Phải trực tiếp kiểm tay và sửa nhiều đầu ra do AI sinh ra: sửa logic nhận diện `TEAM.md` vs `TEAMS.md` và rubric động cho repo thật (`b40c482`), khoá ranh giới dữ liệu `<submission_data_untrusted>` và đọc giới hạn dung lượng HTTP (`29bfa7b`), ép kiểm `eval/run-2.csv` và `cost/simulate-1.csv` bằng số đo thật thay vì ước tính tạm (`05cad02`).
   - Tuyệt đối không dùng AI bịa người phỏng vấn, trích dẫn hay chấm điểm tự động: toàn bộ số liệu khảo sát (`n = 25`), đào data (`N = 135`) và kết quả chạy thử đều được đối chiếu lại bằng Python trước khi commit.

3. **Một câu thử trượt của nhóm và mình học được gì từ nó:**
   - Ở Lượt 1 (`eval/run-1.csv`), câu **`S12`** bị trượt dù AI nêu đủ cả lỗi lệch số liệu lẫn lỗi thiếu `metric_spec.yaml` — vì phần thiếu file bắt buộc (HAX G10) bị đẩy xuống tận cuối mục (3) sau các lỗi nhẹ, khiến người dùng dễ bỏ qua lỗi mất điểm nặng nhất.
   - Sau khi siết luật ưu tiên trong `codebase/agent.py` (`bc24bf0`), `S12` đạt lại ở Lượt 2 (`kho` 12/12 = 100%), nhưng lại lộ ra lỗi hồi quy ở **`S17`**: model trích nhầm `evidence/summary.md` thay vì tên file phẳng `evidence_summary.md` của gói nộp, may nhờ lớp hậu kiểm `[HẬU KIỂM TRÍCH DẪN]` tự động cảnh báo ngay.
   - Bài học lớn nhất là không thể giao toàn bộ độ tin cậy cho prompt: mọi quy tắc đắt giá (lỗi cứng, thứ tự G10, kiểm tra `file:dòng` tồn tại thật, chặn tự chấm điểm) phải được khoá chặt bằng code tất định trước và sau bước gọi LLM.
