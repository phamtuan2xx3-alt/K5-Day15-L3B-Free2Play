# Data card — dữ liệu bản chạy thử dùng

> Điền ở guide bước 2.4 (bản đầu ở CP2, đủ ở CP3). Chấm ở rubric R4.
> **Bản đầu (CP2):** dataset 2 và 3 mới là kế hoạch — cột "Số dòng" và "Phiên bản" điền khi đã sinh / đã thu xong.
> Không commit nguyên tài liệu khoá, dữ liệu cá nhân thật, bài nộp thật của nhóm khác hay nguyên file data BTC cấp.

## Dataset 1 · Rubric chuẩn hoá (`data/rubric.yaml` — dự kiến)

| | |
|---|---|
| Dùng để làm gì | Nguồn cho công cụ `get_rubric(criteria_ids)` · căn cứ để AI đối chiếu bài nộp · căn cứ viết `expected` trong bộ câu thử |
| Từ đâu | Bộ đề hackathon AI20K khoá 5 (repo đề công khai: `03-rubric.md`, `README.md` mục Luật chung, `01-challenge-brief.md` mục 7 hạng mục). **Viết lại rút gọn**, không chép nguyên văn cả file |
| Xử lý những bước gì | Tách mỗi tiêu chí thành một mục có mã (`R1.1`, `R4.2`, `PENALTY-KEY`, `PENALTY-STANDARD`…) · mỗi mục ghi: mô tả 1–2 câu, file cần kiểm, cách kiểm (code / AI), ngưỡng · người thứ hai đối chiếu từng mục với rubric gốc |
| Số dòng / số đoạn | __ tiêu chí *(điền khi xong)* |
| Phiên bản / ngày lấy | Bộ đề bản commit `a873fad` của repo nhóm, đọc 27/11/2026 |
| Nhãn | thật (trích / viết lại từ tài liệu công khai) |
| Giới hạn | Chỉ phủ rubric hackathon K5. Rubric lab ngày thường có thể khác — ngoài phạm vi, công cụ phải báo "chưa kiểm được" |

## Dataset 2 · Hồ sơ bài nộp giả lập (`data/submissions/` — dự kiến)

| | |
|---|---|
| Dùng để làm gì | Đầu vào bản chạy thử và bộ câu thử: mỗi câu thử trỏ tới một hồ sơ bài nộp |
| Từ đâu | **Nhóm tự dựng** (mini-repo chỉ gồm file Markdown / CSV / YAML), tên nhóm và người đều giả |
| Xử lý những bước gì | Bắt đầu từ một bài sạch đạt đủ tiêu chí → script cài lỗi có seed (`data/make_submissions.py`, seed = 42) tạo biến thể. Dạng lỗi lấy từ lỗi thật thu được ở phỏng vấn / khảo sát (ghi nguồn từng dạng lỗi). Gồm: bài sạch 100% (đo báo nhầm) · thiếu file · số không có nguồn · số lệch giữa các file · lộ key giả dạng `sk-TEST…` · chuẩn "đạt" bị đổi · 2 bài cài prompt injection |
| Số dòng / số đoạn | __ hồ sơ *(mục tiêu 20–30)* |
| Phiên bản / ngày lấy | __ |
| Nhãn | `synthetic` |
| Giới hạn | Lỗi cài sẵn sạch và rõ hơn lỗi ngoài đời; bài thật viết lộn xộn hơn. Key giả không phải key thật — không bao giờ dùng key thật làm dữ liệu thử |

**Cách sinh:** script `data/make_submissions.py` · seed 42 · người kiểm: __ · số hồ sơ đã kiểm tay: __/__.
Data tự dựng **không phải bằng chứng pain**.

## Dataset 3 · Lời người dùng thật (khảo sát + phỏng vấn)

| | |
|---|---|
| Dùng để làm gì | Bằng chứng pain (R1, chi tiết ở `evidence/`) · nguồn câu thử có `source` = `nguoi_dung: …` (mục tiêu ≥1/3 bộ câu thử) |
| Từ đâu | Khảo sát Google Form học viên L3 (`evidence/survey/questions.md`) · phỏng vấn học viên ngoài nhóm và lab coach tại phòng C401 (`evidence/interviews/`) |
| Xử lý những bước gì | Xoá mọi cột nhận ra người trả lời trước khi commit · ghi P1, P2… kèm vai, không tên · trích tối đa 1–2 câu · lỗi người dùng kể được viết lại thành câu thử (không chép bài nộp thật) |
| Số dòng / số đoạn | Khảo sát n = __ · phỏng vấn __ người |
| Phiên bản / ngày lấy | 27–28/11/2026 |
| Nhãn | thật |
| Giới hạn | Mẫu toàn học viên L3B cùng lớp, trẻ và rành công cụ; người trả lời khảo sát thường là người quan tâm hơn mức trung bình |
