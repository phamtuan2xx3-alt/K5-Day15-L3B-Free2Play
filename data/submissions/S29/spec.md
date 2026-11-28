# AI SPEC — Đối chiếu chi phí định kỳ SME · Nhóm NhomMau29

Track: [x] C — bài toán: C1

## §1. Người dùng & bằng chứng
- Người dùng chính: Kế toán nội bộ cửa hàng SME xử lý chi phí vận hành hằng ngày.
- Bằng chứng (`evidence_summary.md`): 15/23 (65%) kế toán khảo sát tốn 35 phút/ngày dò lệch hoá đơn, khảo sát n=23.

## §2. Impact & quyết định chọn
- So sánh 3 hướng: (1) Đối chiếu dòng vượt định mức kèm mã chứng từ [Chọn]; (2) Tự động duyệt chi [Loại — rủi ro tài chính]; (3) Dashboard tổng hợp tháng [Loại — không cảnh báo theo ngày].
- Impact / tháng = 300 cửa hàng × 22 ngày × 25 phút tiết kiệm = 165.000 phút/tháng (nguồn: khảo sát n=23).

## §4. Thiết kế
- Lát cắt MỘT CÂU: Một kế toán SME · đưa bảng kê chi phí đã ẩn danh · AI đối chiếu quy chế bằng code và trích mã chứng từ vượt mức · kế toán kiểm rồi tự quyết định.
- Không làm: (1) Không tự duyệt chi hoặc gọi cổng thanh toán; (2) Không lưu số tài khoản hay MST thật; (3) Không đoán giá trị thiếu khi chứng từ mờ.
- Hình dạng: Workflow cố định 2 bước — kiểm quy tắc định mức bằng code rồi mới tóm tắt, tránh sai số tính toán.
- Nguyên tắc thiết kế: G10 (báo chưa kiểm được khi thiếu bảng định mức) · G1 (nêu rõ giới hạn không thay kế toán trưởng) · G11 (trích đúng mã dòng chứng từ).

## §7. Đánh giá & chuẩn đạt
- Chuẩn "đạt": "Đạt khi >= 80% câu thử qua, 100% ca vượt định mức được bắt bằng code và 100% câu thiếu chứng từ trả lời G10."
