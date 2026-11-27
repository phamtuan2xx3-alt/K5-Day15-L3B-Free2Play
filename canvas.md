# Canvas — Free2Play · Track A

> Điền ở guide bước 1.4. CP1 17:00 Thứ Sáu 27/11: nộp bản đầu, đủ 7 dòng (dòng 4 được ghi giả thuyết + nguồn sẽ kiểm).
> CP2 19:30 Thứ Sáu 27/11: cập nhật (số bằng chứng đầu, lát cắt đã chốt) và điền dòng "Đã đổi gì so với CP1".
> Track F: chép thêm thẻ đề của nhóm (khung trong file track F) xuống dưới bảng này.

| # | Dòng | Nhóm điền |
|---|---|---|
| 1 | Track + lát cắt dự kiến | Track A (A6 · Hướng khác trong khoá AI20K) — Giám khảo ảo soát lỗi bài nộp & hỏi vặn phản biện theo Rubric |
| 2 | Người dùng chính (một vai cụ thể — không phải "học viên nói chung") | Học viên L3 (và nhóm làm đồ án/hackathon AI20K) đang rà soát bài lab/repo trong 1–2 giờ cuối trước hạn nộp và trước buổi demo |
| 3 | Pain một câu: ai — đang làm gì — vướng đâu — hậu quả | Học viên L3 khi rà soát bài lab/repo trước hạn nộp phải tự đối chiếu thủ công hàng chục tiêu chí rubric rải rác nhiều file, nên dễ nộp sót bằng chứng, lệch số liệu, lộ thông tin nhạy cảm hoặc không lường trước chỗ yếu khi bị hỏi phản biện → mất thời gian dò tay và bị trừ điểm oan hoặc nhận 0 điểm phần không giải thích được. |
| 4 | Bằng chứng đầu — CP1: giả thuyết + nguồn sẽ kiểm · CP2: số đầu tiên + 1 trích dẫn | Đào data `evidence/data-mining.md` (N = 135 repo CP1 lúc 17:20 27/11): **18/135 (13%)** `TEAMS.md` thiếu hoặc chưa qua hàm kiểm BTC; **15/135 (11%)** `canvas.md` thiếu/chưa đủ 7 dòng; **6/135 (4%)** pain có chữ `"AI"` mà `run.py check` không bắt được. Khảo sát (`evidence/survey/questions.md`, mở 17:31) & phỏng vấn L3/Lab Coach (`evidence/interviews/GUIDE.md`) đang thu thập để kiểm chứng lý do & các lỗi nội dung sâu (chốt đủ trước CP3). |
| 5 | **Lát cắt MỘT CÂU** (1 người dùng · 1 việc · 1 quyết định AI · 1 kết quả) | Một học viên L3 sắp nộp bài lab/repo · đưa hồ sơ bài nộp cùng rubric vào kiểm tra · AI kết hợp công cụ quét bằng code để quyết định hạng mục nào đạt, thiếu căn cứ, mâu thuẫn hay vi phạm luật (trích đúng `file:dòng`), báo "chưa kiểm được" nếu thiếu file và sinh 2 câu hỏi vặn đúng chỗ yếu nhất · học viên kịp sửa lỗi và luyện trả lời phản biện trước khi nộp mà không nhận điểm cuối tự động từ AI. |
| 6 | AI tự làm đến đâu + 1 dòng lý do: sai thì ai chịu gì | AI gợi ý, người quyết — vì nếu AI sai sẽ khiến học viên sửa nhầm hoặc tin nhầm bài đã đạt và mất điểm thật; AI chỉ gắn cờ kèm trích dẫn `file:dòng` và câu hỏi vặn, học viên tự kiểm tra và tự sửa, không tự chấm điểm cuối hay sửa repo. |
| 7 | Phân công có tên | Cả nhóm làm chung khảo sát/phỏng vấn & tổng hợp pain; Cặp X (Phạm Quang Tuấn, Đỗ Hồng Vỹ): thiết kế giải pháp, công cụ kiểm luật cứng, nối model & luồng agent; Cặp Y (Chu Văn Nhật, Bùi Phan Thanh Phúc): bộ câu thử/metric, mô phỏng chi phí, slide & demo. |
| — | *(CP2)* Đã đổi gì so với CP1 | Bổ sung kết quả đào data 135 repo CP1 (`evidence/data-mining.md`), mở rộng phạm vi lỗi cứng thêm lỗi fork/PR nhầm repo gốc (`GIT-FORK-PR`), và chốt kiến trúc Workflow cố định 3 bước (code quét cứng → AI đối chiếu & hỏi vặn → code hậu kiểm) kèm chuẩn "đạt" định lượng. |
