# Reflection — Chu Văn Nhật

> Mã học viên: `2A202603848` · Vai trò: Thành viên (Nhóm Free2Play · L3B · Track A).

1. **Vai trò + phần mình làm (trỏ tới file / commit):**
   - Tham gia rà bộ câu hỏi khảo sát/phỏng vấn và đối chiếu chéo kiểm thử benchmark; trực tiếp mở rộng bộ câu thử [eval/benchmark.csv](eval/benchmark.csv) và bộ sinh hồ sơ [data/make_submissions.py](data/make_submissions.py) từ 15 câu CP2 lên 25 câu cho CP3 (`S16–S25`), bổ sung các ca lỗi thật từ khảo sát (`CANVAS-7ROWS`, `R1-EVIDENCE`, lộ `AIza...`/email, `R2-IMPACT`, `TEAMS-FORMAT`, `S99`, 2 ca tấn công mới) và cập nhật [data/DATA_CARD.md](data/DATA_CARD.md), [spec.md](spec.md) §7/§10 tại `e17a851` (PR #4 `0edbd65`).
   - Dựng bộ slide thuyết trình 8 trang [demo-slides.html](demo-slides.html) và xuất bản PDF [demo-slides.pdf](demo-slides.pdf) chuẩn theo [slides/outline.md](slides/outline.md) ở commit `cb49b7c` (`7002e94`), phụ trách trình bày phần Đánh giá & Kiểm thử (Trang 5).

2. **AI hỗ trợ mình thế nào (việc gì, công cụ gì, chỗ nào phải sửa lại output AI):**
   - Dùng trợ lý AI rà độ phủ 4 chiều của bộ câu thử `benchmark.csv` (loại lỗi, nguồn gốc code vs AI, độ đủ ngữ cảnh, mức độ đắt khi sai), gợi ý cấu trúc các mini-repo `S16–S25` khớp dữ liệu khảo sát và hỗ trợ dựng HTML trình chiếu `demo-slides.html`.
   - Phải tự kiểm tra bằng `python run.py check`, sửa lại nguồn `source` đúng quy ước (`nguoi_dung`, `data_that`, `tu_viet`, `sinh_seed`) để đảm bảo tỉ lệ ≥1/3 từ người dùng/data thật, đồng thời tự đối chiếu từng con số từ `eval/run-1.csv`, `evidence/summary.md` và `cost/simulate-1-summary.md` đưa lên slide thay cho các ô giữ chỗ ban đầu.
   - Khi thiết kế câu `S21` (bài sạch Track D) và `S23` (`S99`), phải tự đọc kỹ đầu ra AI để đảm bảo câu hỏi không dính từ khoá gài lộ hay sửa chuẩn đạt `spec.md` §7 đã chốt ở CP2.

3. **Một câu thử trượt của nhóm và mình học được gì từ nó:**
   - Ở Lượt 2 (`eval/run-2.csv`), nhóm mở rộng thêm câu **`S17`** (lỗi `R1-EVIDENCE` thiếu bằng chứng) đã sửa được `S12` nhưng lại làm **`S17`** bị trượt metric `trich_dan_dung_file_dong`: model phân tích đúng toàn bộ lỗi nhưng viết nhầm tên file thành `evidence/summary.md:Lxx` thay vì `evidence_summary.md:Lxx` như trong gói dữ liệu.
   - Cùng với lỗi nhỏ ở **`S23`** Lượt 1 (chuỗi gợi ý ID còn in cũ `S01–S15` dù bộ câu đã mở lên `S30`), mình rút ra rằng bộ benchmark mở rộng càng sát dữ liệu thật thì càng dễ lộ các giả định ngầm về tên file và ranh giới dữ liệu trong prompt.
   - Nhờ gắn metric `trich_dan_dung_file_dong` kiểm chứng bằng code (không chấm cảm tính), nhóm phát hiện ngay sai lệch nhỏ đó để xử lý có cơ sở.
