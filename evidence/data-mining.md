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

---

# Lần 2 — PR học viên mở nhầm vào repo gốc của khoá

> Script: `evidence/mine_prs.py`, chạy lại bằng `python evidence/mine_prs.py` (cần `gh` đã đăng nhập). Viết phần 6 **trước** khi chạy (tối 27/11, sau CP2).
> Mục đích: đo bằng data công khai con số mà khảo sát chỉ đo bằng lời kể ("13/25 từng PR / push nhầm repo gốc"), và đo thứ mà đào data lần 1 chưa đo được (xem phần 5).

## 6. Cách đếm — viết TRƯỚC khi chạy

- **Data dùng:** pull request (mọi trạng thái: đang mở, đã đóng, đã merge) trong các repo đề **lab L3 khoá K5** của org GitHub `VinUni-AI20k`, tức repo có tên khớp `K5-L3…`, `K5_L3_…`, `K5-L34-…`, `K5-Day8-…`, `K5-Day9-…` (Day 8, Day 9 là lab L3 theo tên repo nộp `K5-L3A-DAY08…`). Không lấy repo L2 / L23 vì khảo sát chỉ hỏi học viên L3.
- **Vì sao PR vào các repo này là "nhầm":** đã đọc README của từng repo đề trước khi đếm. Mọi lab đều nộp bằng **fork / repo riêng + nộp link trên LMS** (hackathon: đội trưởng nộp link qua form). Day 9 ghi "mở PR **trong bản fork**". Không lab nào yêu cầu mở PR vào repo gốc.
- **Loại ra:** PR của tài khoản có quyền trong repo (GitHub ghi `author_association` là `OWNER` / `MEMBER` / `COLLABORATOR`, tức BTC / coach sửa đề) và tài khoản bot. Phần còn lại tính là PR nhầm của người học.
- **Đếm gì:**
  1. Số PR nhầm · số tài khoản khác nhau mở PR nhầm · số repo đề bị PR nhầm (x / số repo đề).
  2. Trạng thái: còn mở · đã đóng không merge · **bị merge vào repo gốc**.
  3. PR nhầm được đóng sau bao lâu (trung vị, tính từ lúc mở đến lúc đóng) — đo một phần "mất bao lâu để sửa" mà khảo sát chưa hỏi được.
  4. PR nhầm vào repo hackathon Day 15 riêng (gần với người dùng của lát cắt nhất).
- **Mẫu số:** số repo đề L3 tìm được lúc chạy. Không có mẫu số người học đáng tin (không biết ai đã từng mở PR rồi xoá tài khoản / repo), nên số tài khoản chỉ là **cận dưới**; so với quy mô lớp L3 hơn 700 học viên (README đề) chỉ để hình dung, không coi là tỉ lệ.
- **Quyền riêng tư:** chỉ in số tổng hợp. Không in, không lưu tên tài khoản, tiêu đề PR, nội dung PR. Tên repo đề là repo công khai của khoá, được ghi.
- **Bổ sung sau lần chạy đầu (23:27 27/11), ghi rõ để không lẫn với phần viết trước:** lần đầu thấy trung vị thời gian đóng ≈ 0 giờ, nên kiểm thêm (a) ai đóng PR — chính tác giả hay người khác (đọc `closed_by`; đã kiểm không repo đề nào có workflow tự đóng PR), và (b) nhánh nguồn của PR có nằm trong repo đã đổi tên khác repo đề không — đổi tên theo mẫu nộp bài (vd `K5-L3A-DAY08-TenNhom-…`) nghĩa là PR mở từ **repo nộp bài**, không phải PR góp ý sửa đề.

## 7. Kết quả — lần 2 (23:30 27/11/2026, 19 repo đề lab L3 K5)

| Đếm gì | Số | Ghi chú |
|---|---|---|
| PR của BTC / coach / bot (loại ra) | 24 | |
| **PR nhầm của người học** | **865** | |
| Tài khoản khác nhau mở PR nhầm | **436** (cận dưới) | 230 tài khoản mở nhầm hơn 1 lần. Lớp L3 hơn 700 học viên (README đề) — chỉ để hình dung, không phải tỉ lệ |
| Repo đề bị PR nhầm | 17/19 (89%) | |
| PR mở từ repo đã đổi tên (repo nộp bài) | 851/865 (98%) | → gần như toàn bộ là PR từ repo nộp bài, không phải góp ý sửa đề |
| Còn mở đến lúc chạy | 283/865 (33%) | không ai tự phát hiện / đóng |
| Đóng không merge | 573/865 (66%) | 573/573 do **chính người mở** tự đóng |
| **Bị merge vào repo đề gốc** | **9/865 (1%)** | 9/9 do người khác (BTC / coach) merge |
| Thời gian đến lúc đóng | trung vị **1 phút** · 545/582 (94%) trong 1 giờ · 567/582 (97%) trong 24 giờ | |
| Riêng repo hackathon Day 15 | 23 PR nhầm từ 18 tài khoản | lúc 23:30 27/11, giữa CP2 và CP3 |

PR nhầm theo repo đề (nhiều nhất): Day02 Discovery 181 · Day08 Workflows→Agents 160 · L3B Day12 AI-SDLC 134 · Day03 ResearchAgent 132 · Day09 Evaluation 90 · Day13 88. Các repo còn lại 0–23. Bản đầy đủ: chạy lại script.

**Tóm tắt:** khảo sát nói **13/25 (52%)** từng PR / push nhầm repo gốc — data công khai xác nhận lỗi này phổ biến: **ít nhất 436 tài khoản, 865 PR** mở nhầm vào 17/19 repo đề L3, **98% từ chính repo nộp bài**.

## 8. Đọc kết quả — ủng hộ và NGƯỢC giả thuyết

- **Ủng hộ:** lỗi PR nhầm có thật, lặp lại (230 tài khoản nhầm hơn 1 lần), xảy ra ở cả lab cuối khoá (Day 13, Day 15). 4 trong 6 repo nhiều PR nhầm nhất có README yêu cầu fork (Day02, Day08, Day12 L3B, Day13) — nhưng Day11 cũng yêu cầu fork mà chỉ có 8, nên fork không giải thích hết. Day 09 dặn "mở PR **trong bản fork**" vẫn có 90 PR vào repo gốc — trên GitHub, PR mở từ bản fork mặc định trỏ về repo gốc, đúng chỗ người học dễ bấm nhầm. Đây là trạng thái git / GitHub mà dán bài vào AI dạng chat không thấy được.
- **NGƯỢC giả thuyết "mất thời gian dò tay":** phần lớn người tự phát hiện rất nhanh (trung vị 1 phút, 94% trong 1 giờ). Mỗi lần nhầm **không tốn nhiều thời gian sửa**. Cái giá nằm ở chỗ khác: **33% PR không ai tự đóng** (bài nộp của nhóm nằm công khai trong repo đề) và **9 PR bị merge vào chính repo đề của khoá**.
- **Giới hạn:** (1) PR đã bị xoá cùng repo nguồn vẫn được đếm (4/865), nhưng PR mà GitHub đã ẩn do tài khoản bị xoá thì không thấy. (2) Một người có thể có nhiều tài khoản; một nhóm fork chung chỉ hiện tài khoản người mở PR — số tài khoản không quy ra được số học viên. (3) Không đọc tiêu đề / nội dung PR (quyền riêng tư), nên có thể lẫn vài PR cố ý; 98% từ repo nộp bài cho thấy phần này rất nhỏ. (4) Ảnh chụp tại một thời điểm.

