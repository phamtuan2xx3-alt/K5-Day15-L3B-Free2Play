# Đào data — cách đếm và kết quả

> Điền ở guide bước 1.2. Script: `evidence/mine_repos.py` — chạy lại bằng `python evidence/mine_repos.py` (cần `gh` đã đăng nhập).
> Repo chỉ chứa số đã tổng hợp — không lưu tên repo, tên nhóm, tên người; không trích nội dung repo của nhóm khác.

## 1. Cách đếm — viết TRƯỚC khi chạy

- **Data dùng:** repo GitHub công khai của các nhóm hackathon AI20K K5 Day15 (đề bắt buộc repo công khai, tên dạng `K5-Day15-<lớp>-<tên nhóm>`). Tìm bằng GitHub search từ khoá `K5-Day15`, giữ repo có tên bắt đầu bằng `K5-Day15-L3A-` hoặc `K5-Day15-L3B-`.
- **Đếm gì:**
  1. `TEAMS.md` có qua hàm kiểm `check_teams()` của khung BTC (`eval/run_eval.py`, chính là phần "Kiểm TEAMS.md" của `python run.py check`) không — tức đúng format để BTC quét ghép điểm. Không tự đặt luật riêng.
  2. `canvas.md` có đủ 7 dòng đã điền không (ô "Nhóm điền" dòng 1–7 không trống, không còn `____`).
  3. Dòng 3 của canvas (pain) có chữ "AI" đứng riêng không — đề yêu cầu bài toán "không viết chữ AI".
- **Mẫu số:** N = số repo tìm được tại thời điểm chạy, kể cả repo trống hoặc chưa sửa gì.
- **Thời điểm:** chạy lần 1 lúc 17:20 27/11/2026 (giờ Việt Nam), 20 phút sau hạn CP1 (17:00).

## 2. Đọc trước, đếm sau

Đã đọc cấu trúc `TEAMS.md`, `canvas.md` trong khung starter-repo và hàm kiểm của BTC trước khi viết script. Kiểu lỗi có thể gặp: còn ô `____` · sai tiêu đề bảng · đội trưởng không ở dòng 1 · số thành viên ngoài 3–5 · Lớp / Track ghi sai chữ · thiếu file.

## 3. Kết quả — lần 1 (17:20 27/11/2026, N = 135: 73 repo L3B, 62 repo L3A)

| Đếm gì | x / N | % | Ghi chú |
|---|---|---|---|
| `TEAMS.md` qua hàm kiểm của BTC | 117/135 | 87% | |
| `TEAMS.md` có nhưng chưa qua | 14/135 | 10% | Một repo có thể dính nhiều nhóm lỗi |
| — còn ô chưa điền (`____`) | 8/135 | 6% | |
| — số thành viên ngoài 3–5 | 4/135 | 3% | |
| — sai dòng / số Đội trưởng | 3/135 | 2% | |
| — Lớp / Track ghi sai chữ | 1/135 | 1% | |
| — khác | 1/135 | 1% | |
| Không có `TEAMS.md` | 4/135 | 3% | |
| `canvas.md` đủ 7 dòng | 120/135 | 89% | |
| `canvas.md` điền một phần | 3/135 | 2% | |
| `canvas.md` còn trống hoàn toàn | 8/135 | 6% | |
| Không có `canvas.md` | 4/135 | 3% | |
| Dòng 3 (pain) có chữ "AI" | 6/135 | 4% | Hàm kiểm của BTC **không** bắt lỗi này |

**Tóm tắt:** sau hạn CP1, **18/135 repo (13%)** có `TEAMS.md` thiếu hoặc chưa qua hàm kiểm của BTC — dù khung đã có sẵn lệnh `python run.py check` để tự kiểm.

## 4. Ví dụ cụ thể

Không trích nội dung hay nêu nhóm nào (repo của bạn cùng khoá). Ví dụ được mô tả theo **dạng lỗi**, đếm ở bảng trên: ô họ tên / mã học viên còn `____` · bảng 2 hoặc 6 thành viên · đội trưởng ghi ở dòng 2 · Track ghi tên track thay vì một chữ cái · canvas dòng pain có chữ "AI".

## 5. Giới hạn — và điều data này nói NGƯỢC giả thuyết

- **Phần lớn lỗi đếm được là lỗi format mà `run.py check` đã bắt được.** Data này ủng hộ "cách giải thích khác" ghi trong `evidence/hypothesis.md`: script có sẵn đã bắt được loại lỗi này — vấn đề có thể là học viên **không chạy** script hoặc làm sát giờ, không phải thiếu công cụ.
- Lỗi mà nhóm muốn AI bắt (số không có nguồn, mâu thuẫn giữa các file, chỗ yếu khi bị hỏi vặn) **chưa đo được ở CP1** — chỉ xuất hiện từ CP2–CP4. Cần chạy lại sau CP3 / CP4 và kiểm bằng phỏng vấn lab coach.
- GitHub search có thể sót repo; có nhóm có thể có 2 repo; nhóm có thể đã nộp form CP1 rồi mới sửa repo. Chỉ là ảnh chụp tại một thời điểm.
- Data cho biết repo **trông thế nào**, không cho biết **vì sao** → kiểm lại bằng khảo sát câu 3–6 (`evidence/survey/questions.md`) và phỏng vấn (`evidence/interviews/GUIDE.md`).
