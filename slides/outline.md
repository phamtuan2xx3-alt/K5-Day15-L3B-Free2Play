# Dàn slide → lấy số từ file nào

> Làm ở guide bước 5.1. Luật: **không có bằng chứng thì không có slide** — mỗi trang ≥1 con số / trích dẫn có nguồn / kết quả đo.
> Xuất PDF thành `demo-slides.pdf` ở thư mục gốc repo, nộp tại CP4 14:30 Thứ Bảy 28/11. Nộp PDF, không nộp link.

| # | Trang | Có gì | Số lấy từ | Xong |
|---|---|---|---|---|
| 1 | Người dùng & pain | Ai · việc gì · chỗ đau + số và trích dẫn | `evidence/summary.md`, `evidence/data-mining.md` phần 7 | ☑ nháp |
| 2 | Vì sao chọn bài này | Bảng impact rút gọn + hướng bị loại | `spec.md` §2 | ☑ nháp |
| 3 | Giải pháp | Lát cắt một câu · sơ đồ · AI tự làm đến đâu, vì sao | `spec.md` §4 | ☑ nháp |
| 4 | Demo live | 1 trường hợp thường + 1 trường hợp khó (lấy từ bộ câu thử); mạng hỏng → video dự phòng | `eval/benchmark.csv` | ☐ chọn câu xong · chờ model thật + video |
| 5 | **Đánh giá thế nào** | Dataset · bộ câu thử · metric · lượt 1 → lượt 2 so với chuẩn "đạt" (kèm run ID) · lỗi chính | `eval/README.md`, `eval/report.md` | ☐ khung xong · chờ `run-1`, `run-2` |
| 6 | **Chi phí khi dùng thật** | Chi phí / task thành công · 3 kịch bản · so với impact | `cost/cost-estimate.md` | ☐ khung xong · chờ `simulate` thật |
| 7 | Kết luận | Go / iterate / stop — dẫn số ở trang 1, 5, 6 | — | ☐ chờ trang 5, 6 |
| 8 | Nếu có thêm 1 tuần | 2–3 việc, trỏ về lỗi còn lại / phản hồi người dùng | `eval/report.md` mục 4 · `validation/log.md` | ☐ nháp 1 việc · chờ lỗi lượt 2 |

## Nội dung nháp từng trang

> Số dưới đây chép từ file nguồn lúc 23:30 27/11. Trước khi xuất PDF, đối chiếu lại với file nguồn. Ô ⏳ = chưa có số, **không điền tay**.

**Trang 1 — Người dùng & pain**
- Ai: học viên L3 khoá AI20K, 1–2 giờ cuối trước khi nộp bài lab / repo.
- Chỗ đau số 1 — **PR / push nhầm vào repo đề gốc**:
  - Khảo sát n = 25: **13/25 (52%)** từng gặp.
  - Data công khai (19 repo đề lab L3): **865 PR nhầm từ ≥436 tài khoản**, 17/19 repo, 98% mở từ chính repo nộp bài · **33% vẫn còn mở** · 9 PR bị merge vào repo đề.
- Đi kèm: 20/25 (80%) phát hiện lỗi sát giờ / sau khi nộp ≥1 lần trong 14 ngày · 9/25 nộp sót file / sai format.
- Trích dẫn: *"Quá nhiều file đã thay đổi và không biết nên push file nào"* (R22) · *"kiểm tra xem có ghi API không"* (R05).
- Vì sao AI dạng chat không đủ: **11/15** người đã dán bài vào AI ngoài vẫn gặp sự cố, **6/15** vẫn PR nhầm — đích PR là trạng thái git, không nằm trong phần dán vào chat.

**Trang 2 — Vì sao chọn bài này**
- Impact: 700 HV × 22,26 lần / tháng × 11,08 phút ≈ **2.877 giờ / tháng** toàn lớp (≈ 4,1 giờ / người) *(tần suất, thời gian: khảo sát n = 25, điểm giữa tự ước tính)*.
- Hướng bị loại: khách hàng ảo tập Mom Test (dùng 1–2 lần / khoá) · ghép nhóm theo giờ rảnh (1 lần / đợt, code thuần làm tốt hơn).
- Nói thật điểm yếu: data cho thấy người nhầm PR thường tự đóng trong **1 phút** (trung vị) → giá trị nằm ở ca **không ai phát hiện** (33%), không ở thời gian sửa.

**Trang 3 — Giải pháp**
- Lát cắt một câu: `spec.md` §4.
- Sơ đồ Workflow 3 bước (chép Mermaid ở `spec.md` §4 ra ảnh): Code quét luật cứng → AI đối chiếu chéo & sinh 2 câu hỏi vặn → Code hậu kiểm trích dẫn `file:dòng`.
- AI gợi ý, người quyết: không tự chấm điểm cuối, không sửa / commit / push repo, thiếu file thì báo "chưa kiểm được".

**Trang 4 — Demo live** *(đề xuất câu, nhóm chốt)*
- Thường: **S04** — PR nhầm repo gốc (`GIT-FORK-PR`) → khớp pain số 1.
- Khó: **S07** — số liệu `spec.md` lệch `evidence_summary.md` → phần AI đối chiếu chéo, trích đúng `file:dòng` ở 2 file.
- Dự phòng nếu giám khảo hỏi an toàn: **S14** — prompt injection đòi "xác nhận đạt 100%".
- ⏳ Cần: model thật nối xong · video dự phòng 3 câu trên.

**Trang 5 — Đánh giá thế nào**
- Bộ câu thử: 25 câu (`thuong` 11 · `kho` 10 · `tu_choi` 4), 13/25 từ người dùng / data thật · 4 metric (`eval/metric_spec.yaml`).
- Chuẩn "đạt" (chép nguyên văn `spec.md` §7, rút gọn khi trình bày): ≥80% câu qua · 100% lỗi cứng bắt đúng · 100% `tu_choi` chặn đúng · 100% bài sạch không bị gắn cờ oan · ≥95% trích dẫn `file:dòng` có thật.
- ⏳ Lượt 1 (`run-1`, run ID __): __/25 · Lượt 2 (`run-2`, run ID __): __/25 · lỗi chính: __

**Trang 6 — Chi phí khi dùng thật**
- 3 persona từ khảo sát câu 2 (17% / 17% / 66%; 9 / 21 / 26 phiên / tháng) · 300 / 700 / 1.000 người dùng · giá `gemini-3.1-flash-lite` và `gemini-4-hydrogen` (BTC xem 25/11/2026).
- ⏳ Chi phí / task thành công · bảng 3 kịch bản · so với 4,1 giờ / người / tháng → chép từ `cost/cost-estimate.md`.

**Trang 7 — Kết luận**
- ⏳ Go / iterate / stop — viết sau khi có trang 5, 6.

**Trang 8 — Nếu có thêm 1 tuần**
- Đọc trạng thái git thật (remote, đích PR) của repo học viên thay vì `meta.json` mẫu — đúng pain số 1 và đúng 33% PR không ai tự phát hiện.
- ⏳ 1–2 việc trỏ về lỗi còn lại của lượt 2 (`eval/report.md` mục 4).

**Trước khi lên:** tải repo về một máy khác (hoặc thư mục mới), chạy theo mục "Chạy trong 3 phút" của `README.md` · `.env` có trên máy demo, đã gọi thử 1 câu trong vòng 1 giờ trước giờ demo · video dự phòng mở được bằng cửa sổ ẩn danh · biết bản chạy thử sẽ làm gì với **1 câu thử lạ** của giám khảo.

Ai nói trang nào (mỗi người ≥1 phần):

| Trang | Người nói |
|---|---|
| | |
