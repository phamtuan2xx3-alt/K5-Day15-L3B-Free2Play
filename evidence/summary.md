# Tổng hợp bằng chứng pain

> Điền ở guide bước 1.2, xong trước **CP3 10:00 Thứ Bảy 28/11**. Chấm ở rubric R1.
> Ba nguồn ngang nhau — tối thiểu **≥1 nguồn đạt ngưỡng**. Mạnh nhất: đào data ra insight → hỏi người dùng để kiểm lại (hoặc ngược lại).

## 1. Nguồn đã dùng

| Nguồn | Đạt ngưỡng? | File |
|---|---|---|
| Đào data (x/N, %, cách đếm chạy lại được, ≥5 ví dụ) | ☑ | `evidence/data-mining.md` |
| Phỏng vấn (≥3 người ngoài nhóm, đúng người dùng) | ☐ | `evidence/interviews/P1.md`… |
| Khảo sát (≥20 người ngoài nhóm, đúng người dùng) | ☐ *(đang thu: 6/20)* | `evidence/survey/results.csv` |

## 2. Số chính

- **Đào data** (`evidence/data-mining.md`, N = 135 repo CP1 ngày 27/11/2026): **18/135 (13%)** repo thiếu hoặc chưa qua `check_teams()` của BTC; **15/135 (11%)** repo có `canvas.md` chưa đủ 7 dòng / trống / thiếu; **6/135 (4%)** repo có chữ "AI" trong dòng pain (lỗi mà `python run.py check` không bắt được).
- **Phỏng vấn:** __/3 học viên ngoài nhóm + __/2 lab coach *(đang triển khai chiều/tối 27/11)*.
- **Khảo sát** *(bản tạm tính lúc 18:10 ngày 27/11, n = 6 — chưa đủ ngưỡng ≥20, không ghi % theo quy tắc n nhỏ)*:
  - Đối tượng: 4/6 học viên L3B, 2/6 học viên L3A.
  - Tần suất nộp 14 ngày qua: 3/6 trên 12 lần, 2/6 (9–12 lần), 1/6 (4–8 lần).
  - Thời gian tự rà mỗi lần: **5/6 mất 5–15 phút**, 1/6 dưới 5 phút.
  - Cách soát hiện tại: 4/6 tự đọc bằng mắt, **4/6 dán vào AI bên ngoài**, 3/6 chạy script check, 1/6 nhờ bạn đọc chéo.
  - Sự cố đã gặp & phát hiện sát giờ/sau nộp (**4/6 người gặp ≥1 lỗi** — trong đó 3/6 gặp 2–3 lần, 1/6 gặp 1 lần): **3/6** fork bài về nhưng tạo PR/push nhầm lên repo gốc; **3/6** nộp sót file / thiếu mục / sai format; **1/6** số liệu lệch / thiếu nguồn giữa các file; **1/6** lúng túng khi bị hỏi vặn. Đáng chú ý: **2/4** người đã dán bài vào AI bên ngoài (`R01`, `R05`) vẫn gặp lỗi lệch nguồn / PR nhầm repo gốc / lúng túng khi bị hỏi vặn.

Phỏng vấn nhiều vai thì đếm theo từng vai, không cộng chung.

| | Vai | Gặp pain? | Số lần / 1 tháng qua | Lần gần nhất mất | Đang xoay xở bằng |
|---|---|---|---|---|---|
| P1 | | | | | |
| P2 | | | | | |
| P3 | | | | | |

## 3. ≥5 trích dẫn hoặc ví dụ nguyên văn (có nguồn, bỏ tên)

*(Hiện có 3/5 trích dẫn từ khảo sát — tiếp tục bổ sung từ phỏng vấn và các phiếu khảo sát mới trước CP3)*

1. `"phải xem lại xem đủ bài chưa"` — phiếu khảo sát `R03` (Học viên lớp L3A)
2. `"kiểm tra xem có ghi API không"` — phiếu khảo sát `R05` (Học viên lớp L3B)
3. `"thiếu một số file của thành viên nên cần liên hệ để vổ sung"` — phiếu khảo sát `R06` (Học viên lớp L3B)
4.
5.

## 4. Các nguồn có khớp nhau không

- **Khớp:** Đào data trên 135 repo cho thấy **18/135 (13%)** repo vẫn lỗi/thiếu `TEAMS.md` dù khung đã có sẵn lệnh `python run.py check`; khảo sát tạm tính cũng ghi nhận **3/6** người gặp lỗi nộp sót file / sai format dù **3/6** có chạy script check và **4/6** tự rà mắt/dán AI ngoài.
- **Bổ sung insight mới từ khảo sát:** Nỗi đau lớn ngoài phạm vi của `run.py check` là **3/6** người từng **fork bài về nhưng tạo PR / push nhầm lên repo gốc** của khoá, cùng với lo ngại rà lộ API key (`R05`), thiếu file thành viên (`R06`), lệch số liệu giữa các file (`R01`) và lúng túng khi bị hỏi vặn (`R05`).

## 5. Kết luận

Giả thuyết ở `evidence/hypothesis.md`: **đang đi đúng hướng (chưa chốt đến khi khảo sát n ≥ 20 và phỏng vấn ≥3)**. Ghi nhận thêm: lỗi đặc thù *fork/PR nhầm repo gốc* xuất hiện tới 3/6 người trong lô phản hồi đầu; cần phỏng vấn trực tiếp Lab Coach và đủ ≥20 phiếu khảo sát để chốt ngưỡng giả thuyết ở CP3.

## Tiến độ (dùng cho CP2)

| Nguồn | Kế hoạch | Đã làm đến đâu |
|---|---|---|
| Đào data (đạt ngưỡng) | Kiểm repo GitHub công khai `K5-Day15-L3*` sau CP1 | **Đã xong lần 1 (17:20):** N = 135 repo · chi tiết ở `evidence/data-mining.md` và `evidence/mine_repos.py` |
| Khảo sát (nguồn kiểm chéo chính) | ≥20 học viên L3 ngoài nhóm · bộ câu `evidence/survey/questions.md` | Đã mở lúc 17:31 qua link `https://forms.gle/amwVjGJB1xXrezYFA` · **đang có 6/20 phiếu** (`R01`–`R06`) |
| Phỏng vấn (nguồn kiểm lại) | ≥3 học viên ngoài nhóm + 1–2 lab coach · kịch bản `evidence/interviews/GUIDE.md` | Đang tiến hành (0/3 HV · có 1 người trả lời `R05` đồng ý hẹn) |

## Lịch hẹn (dùng cho CP2 — chỉ ghi vai và giờ, không tên)

| Vai | Giờ hẹn | Đã xong? |
|---|---|---|
| Học viên L3B ngoài nhóm (`R05` — P1) | Tối 27/11 (liên hệ qua thông tin Câu 8 giữ ngoại tuyến) | ☐ |
| Học viên L3B ngoài nhóm (P2) | __ | ☐ |
| Học viên L3 ngoài nhóm (P3) | __ | ☐ |
| Lab coach (P4) | trước 19:30 hôm nay tại C401 | ☐ |
