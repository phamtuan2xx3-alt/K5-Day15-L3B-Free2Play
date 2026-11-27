# AI SPEC — Xử lý khiếu nại giao đồ ăn · Nhóm NhomMau21

Track: [x] D — bài toán: D1

## §1. Người dùng & bằng chứng
- Người dùng chính: Khách đặt đồ ăn qua app gặp đơn thiếu món giờ trưa/tối.
- Bằng chứng (`evidence_summary.md`): 16/24 (67%) người khảo sát từng gặp thiếu/sai món, khảo sát n=24.

## §2. Impact & quyết định chọn
- So sánh 3 hướng: (1) Xử lý khiếu nại thiếu món [Chọn]; (2) Gợi ý quán ăn [Loại]; (3) Tóm tắt review quán [Loại].
- Impact / tháng = 1.000 đơn khiếu nại × 15 phút xử lý = 15.000 phút/tháng (tự ước tính từ khảo sát n=24).

## §4. Thiết kế
- Lát cắt MỘT CÂU: Một khách đặt đồ ăn · báo thiếu món · AI tra đơn và kiểm hạn mức bằng code để đề xuất hoàn phần thiếu hoặc chuyển người · khách nhận phương án đúng chính sách.
- Không làm: (1) Không hoàn vượt hạn mức chính sách; (2) Không tự xử lý ca nghi ngộ độc/dị vật; (3) Không lộ SĐT shipper/quán.
- Hình dạng: Workflow cố định 2 bước — không chọn multi-agent vì quy trình tra đơn → kiểm hạn mức tuần tự và dễ kiểm soát bằng code.
- Nguyên tắc thiết kế: G10 (hỏi mã đơn khi thiếu) · G1 (nêu rõ hạn mức chính sách) · G11 (trích chi tiết đơn hàng và mức hoàn).

## §7. Đánh giá & chuẩn đạt
- Chuẩn "đạt": "Đạt khi >= 80% câu thử qua, và 100% câu không bồi thường vượt hạn mức."
