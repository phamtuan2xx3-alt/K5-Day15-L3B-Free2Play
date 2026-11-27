# Data card — dữ liệu bản chạy thử dùng

> Điền ở guide bước 2.4 (bản đầu ở CP2, đủ ở CP3). Chấm ở rubric R4.
> Không commit nguyên tài liệu khoá, dữ liệu cá nhân thật, bài nộp thật của nhóm khác hay nguyên file data BTC cấp.

## Dataset 1 · Rubric chuẩn hoá (`data/rubric.json`)

| | |
|---|---|
| Dùng để làm gì | Nguồn cho công cụ `get_rubric(criteria_ids)` · căn cứ để AI đối chiếu bài nộp · căn cứ viết `expected` trong bộ câu thử |
| Từ đâu | Bộ đề hackathon AI20K khoá 5 (repo đề công khai: `03-rubric.md`, `README.md` mục Luật chung, `01-challenge-brief.md` mục 7 hạng mục). **Viết lại rút gọn**, không chép nguyên văn cả file |
| Xử lý những bước gì | Tách mỗi tiêu chí thành một mục JSON có mã (`R1.1`, `R2.1`, `R3.1`, `R4.1`, `PENALTY-KEY`, `PENALTY-STANDARD`, `GIT-FORK-PR`, `HAX-G10`…) gồm `id`, `title`, `check_type`, `rule`, `penalty` · người thứ hai đối chiếu từng mục với rubric gốc |
| Số dòng / số đoạn | `10–12` tiêu chí ở bản khung CP2 *(chốt số đếm chính xác ngay khi ghép `data/rubric.json` ở bước đồng bộ 19:00)* |
| Phiên bản / ngày lấy | Bộ đề bản commit `b568b95` trước khi tách starter-repo, đọc 27/11/2026 |
| Nhãn | thật (trích / viết lại từ tài liệu công khai) |
| Giới hạn | Chỉ phủ rubric hackathon AI20K K5. Rubric lab ngày thường có thể khác — ngoài phạm vi, công cụ phải báo `"chưa kiểm được"` |

## Dataset 2 · Hồ sơ bài nộp giả lập (`data/submissions/S01..S15/`)

| | |
|---|---|
| Dùng để làm gì | Đầu vào bản chạy thử và bộ câu thử: mỗi câu `S01`–`S15` trỏ tới một mini-repo giả lập tương ứng |
| Từ đâu | **Nhóm tự dựng** (mini-repo chỉ gồm `TEAMS.md`, `canvas.md`, `spec.md`, `evidence_summary.md` — tương ứng `evidence/summary.md` ở repo chuẩn, `benchmark.csv`, `meta.json` tuỳ ca), tên nhóm và tên người đều giả |
| Xử lý những bước gì | Bắt đầu từ một bài sạch đạt đủ tiêu chí (`S01`) → script `data/make_submissions.py` (`seed = 42`) tạo 15 biến thể cài đúng lỗi thật từ đào data & khảo sát: bài sạch khác mẫu (`S08`), lỗi `TEAMS.md` (`S02`), pain có chữ `"AI"` (`S03`), PR nhầm repo gốc (`S04`), thiếu file (`S05`), lộ key giả `sk-TEST…` (`S06`), lệch số (`S07`), đổi chuẩn đạt (`S09`), thiếu file/cột CSV (`S11`), đa lỗi (`S12`), thiếu G10/Không làm (`S13`), prompt injection (`S14`), ca xin vượt thẩm quyền (`S15`) |
| Số dòng / số đoạn | **15 hồ sơ mẫu `S01`–`S15` cho CP2** *(đang ghép từ nhánh code khung lúc 19:00; sẽ mở rộng 20–30 hồ sơ trước CP3)* |
| Phiên bản / ngày lấy | v1 (`seed = 42`, dựng 27/11/2026) |
| Nhãn | `synthetic` |
| Giới hạn | Lỗi cài sẵn sạch và rõ hơn lỗi ngoài đời; bài thật viết lộn xộn hơn. Key giả `sk-TEST…` không phải key thật — không bao giờ dùng key thật làm dữ liệu thử |

**Cách sinh:** script `data/make_submissions.py` · `seed = 42` · người kiểm: Cặp X (Tuấn & Vỹ) kiểm chéo trước khi chạy Lượt 1.
Data tự dựng **không phải bằng chứng pain**.

## Dataset 3 · Lời người dùng thật (khảo sát + phỏng vấn)

| | |
|---|---|
| Dùng để làm gì | Bằng chứng pain (R1, chi tiết ở `evidence/`) · nguồn câu thử có `source = nguoi_dung: …` (đảm bảo ≥1/3 bộ câu thử) |
| Từ đâu | Khảo sát Google Form học viên L3 (`evidence/survey/questions.md`, mở 27/11/2026 17:31) · phỏng vấn học viên ngoài nhóm và Lab Coach tại phòng C401 (`evidence/interviews/GUIDE.md`) |
| Xử lý những bước gì | Xoá hoàn toàn cột Câu 8 (liên hệ) và dấu thời gian nhận diện trước khi commit · ghi `P1`, `P2`… kèm vai, không tên · trích tối đa 1–2 câu · lỗi người dùng kể được viết lại thành biến thể hồ sơ giả lập (không chép bài nộp thật của ai) |
| Số dòng / số đoạn | **Đợt thử sơ bộ trước CP2:** `eval/benchmark.csv` hiện dẫn chiếu 4 phản hồi khảo sát ban đầu (`nguoi_dung: R01, R03, R05, R06` — chưa tính là đủ ngưỡng R1). Bản log đầy đủ đã ẩn danh (`evidence/survey/results.csv`, mục tiêu `≥ 20` phiếu, đã xoá cột Câu 8) và `evidence/interviews/P*.md` (`≥ 3` HV ngoài nhóm + `1–2` Lab Coach) đang thu thập và chốt commit trước CP3 |
| Phiên bản / ngày lấy | 27–28/11/2026 |
| Nhãn | thật |
| Giới hạn | Mẫu chủ yếu học viên L3B cùng lớp, trẻ và rành công cụ; người trả lời khảo sát thường là người quan tâm hơn mức trung bình |

## Dataset 4 · Thống kê tổng hợp repo CP1 công khai (`evidence/data-mining.md`)

| | |
|---|---|
| Dùng để làm gì | Bằng chứng hành vi thật (R1) về tỉ lệ sót/lỗi format khi nộp bài và nguồn lỗi thực tế cho câu thử `data_that` (`S02`, `S03`) |
| Từ đâu | Kết quả quét tự động (`evidence/mine_repos.py`) trên 135 repo GitHub công khai (`73` L3B, `62` L3A) lúc 17:20 27/11/2026 |
| Xử lý những bước gì | Chỉ lưu số tổng hợp (`x/N`, `%`) và phân loại nhóm lỗi (`TEAMS.md`, `canvas.md`, chữ `"AI"` trong pain); **không lưu tên repo, tên nhóm hay nội dung repo của nhóm khác** |
| Số dòng / số đoạn | Tổng hợp từ `N = 135` repo công khai |
| Phiên bản / ngày lấy | Chụp lần 1 lúc 17:20 27/11/2026 |
| Nhãn | thật (tổng hợp ẩn danh) |
| Giới hạn | Ảnh chụp tại một thời điểm sau CP1 20 phút; chỉ đo được lỗi hình thức/cấu trúc bước đầu, chưa đo được lỗi số liệu sâu ở CP2–CP4 |
