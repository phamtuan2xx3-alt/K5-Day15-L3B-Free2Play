# Reflection — Bùi Phan Thanh Phúc

> Mã học viên: `2A202603981` · Vai trò: Thành viên (Nhóm Free2Play · L3B · Track A).

1. **Vai trò + phần mình làm (trỏ tới file / commit):**
   - Phụ trách thu thập, làm sạch và tổng hợp bằng chứng pain tại [evidence/summary.md](evidence/summary.md): chốt bộ khảo sát ẩn danh `n = 25` học viên + 2 Lab Coach (`evidence/survey/results.csv`, script `evidence/survey/tally.py`), phỏng vấn `P4` Lab Coach (`b255941`), ghi nhận trung thực 3 trao đổi ngắn `P1–P3` không tính nguồn đạt ngưỡng riêng (`bed55c3`, `b492179`).
   - Dựng cấu hình mô phỏng chi phí thực tế [cost/personas.yaml](cost/personas.yaml) từ phân bố câu 2 khảo sát (`nop_it` 17%, `nop_vua` 17%, `nop_nhieu` 66%, quy mô 300/700/1.000 học viên) và chạy thử khung `simulate --try` trước CP3 (`5b22662`, PR #3 `016d1aa`).
   - Đồng hoàn thiện phần số liệu pain, impact và chi phí dùng thật (`cost/cost-estimate.md`, slide Trang 1, 2, 6, 8) khớp kết quả `cost/simulate-1-summary.md`.

2. **AI hỗ trợ mình thế nào (việc gì, công cụ gì, chỗ nào phải sửa lại output AI):**
   - Dùng trợ lý AI viết script Python thống kê `evidence/survey/tally.py` và rà lại câu hỏi khảo sát theo nguyên tắc Mom Test để không hỏi dẫn dắt người trả lời.
   - Phải kiểm tay và sửa trực tiếp những điểm AI dễ làm sai hoặc dễ hiểu nhầm là "làm đẹp số": xoá sạch cột thông tin liên hệ Câu 8/C5 khỏi CSV trước khi commit để bảo vệ ẩn danh; tách riêng 3 trao đổi ngắn `P1–P3` khỏi nhóm nguồn đạt ngưỡng vì học viên chỉ lặp lại ý form; sửa lại giả thuyết ở `evidence/summary.md` để ghi rõ số `15/25 (60%)` đúng chữ giả thuyết vs `21/25 (84%)` tính cả PR nhầm/lộ key.
   - Mọi bảng chi phí đều chạy qua `python run.py simulate` từ trace thật, không tự nhân ước lượng trên giấy khi nộp bản cuối.

3. **Một câu thử trượt của nhóm và mình học được gì từ nó:**
   - Khi theo dõi từ **Lượt 1 (`S12` trượt)** sang **mô phỏng chi phí 50 phiên**, mình thấy mối liên hệ trực tiếp giữa chất lượng prompt, độ dài câu trả lời và bài toán kinh tế: lúc đầu model bật chế độ suy nghĩ tốn trung bình `9.430` token ra/lượt (`~$0.0131`/task tạm tính), nhưng khi tắt `enable_thinking=False` trong `simulate-1` thì tụt xuống `2.174` token ra/lượt và chỉ còn **`$0.0077 / task thành công`** (**`$0.1790 / người / tháng`** ở lớp 700 học viên) mà Lượt 2 vẫn giữ `97%` đạt chuẩn.
   - Một lỗi nhỏ như `S12` (để sót thứ tự lỗi thiếu file) nhắc mình rằng giá trị tiết kiệm `~4,1 giờ/người/tháng` chỉ có ý nghĩa khi AI giúp người dùng né đúng lỗi đắt điểm nhất (như 52% từng PR nhầm repo gốc và 36% sót file) với chi phí đủ rẻ để học viên dùng lặp lại suốt 15 ngày lab.
