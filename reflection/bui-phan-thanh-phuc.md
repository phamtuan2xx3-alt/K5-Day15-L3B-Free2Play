# Reflection — Bùi Phan Thanh Phúc

> Làm ở guide bước 5.3. Mỗi người một file: chép file này thành `reflection/<ten-khong-dau>.md` (viết thường, không dấu). Hạn: **23:59 Thứ Bảy 28/11**. Mỗi câu 3–6 dòng.

1. Vai trò + phần mình làm (trỏ tới file / commit):
   Thành viên Cặp Y, phụ trách bằng chứng pain, mô phỏng chi phí, slide & demo (`TEAMS.md`, `spec.md` §10).
   - Khảo sát: soạn 9 câu hỏi hành vi (`ee29e98`), chốt n = 25 học viên + 2 lab coach, đã ẩn danh, đếm lại bằng `evidence/survey/tally.py` (`b255941`). Ghi đúng thực tế P1–P4 chưa đạt ngưỡng phỏng vấn (`bed55c3`, `b492179`).
   - Đào data: quét 135 repo sau CP1 (`evidence/mine_repos.py`, `cc246bf`) và đếm PR nhầm vào repo đề gốc: 865 PR, ít nhất 436 tài khoản (`evidence/mine_prs.py`, `evidence/data-mining.md` phần 6–8, `79f08fb`).
   - Chi phí: `cost/personas.yaml` lấy tỉ lệ và tần suất từ câu 2 khảo sát (`5b22662`), điền đầu vào có nguồn trong `cost/cost-estimate.md`. Slide: `slides/outline.md` và bộ slide → `demo-slides.pdf`.

2. AI hỗ trợ mình thế nào (việc gì, công cụ gì, chỗ nào phải sửa lại output AI):
   Dùng Claude Code (coding agent trong VS Code) để viết script đếm (`mine_repos.py`, `mine_prs.py`, `tally.py`), soạn khung personas, dàn slide và dựng slide.
   - Phải kiểm thêm: lần chạy đầu `mine_prs.py` ra trung vị thời gian đóng PR ≈ 0 giờ. Kiểm thêm ai đóng PR thì thấy 98% do chính người mở tự đóng, nghĩa là giả thuyết "mất thời gian sửa" bị ngược, phải ghi rõ trong `data-mining.md` phần 8. Hai phép đếm thêm sau lần chạy đầu được ghi rõ là "bổ sung", không trộn với cách đếm viết trước.
   - Phải sửa: AI ghi nhầm ngày chạy (28/11 thay vì 27/11) và đánh số trang slide lệch với số trang thật — mình đọc lại rồi sửa.
   - Phải hỏi lại: AI làm việc trước rồi mới kiểm có phải phần mình được giao không; từ đó mình hỏi "có phải việc của tôi không" trước khi giao việc.
   *(Phúc thêm 1–2 ý của riêng mình nếu có, vd lúc soạn câu hỏi khảo sát hoặc personas.)*

3. Một câu thử trượt của nhóm và mình học được gì từ nó:
   *(Chờ eval lượt 1 / lượt 2 — chọn 1 câu trượt trong `eval/run-*.csv`, mở trace, ghi: câu nào, vì sao trượt, nhóm sửa gì, mình học được gì. Không viết trước khi có kết quả thật.)*
