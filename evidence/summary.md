# Tổng hợp bằng chứng pain

> Điền ở guide bước 1.2, xong trước **CP3 10:00 Thứ Bảy 28/11**. Chấm ở rubric R1.
> Ba nguồn ngang nhau — tối thiểu **≥1 nguồn đạt ngưỡng**. Mạnh nhất: đào data ra insight → hỏi người dùng để kiểm lại (hoặc ngược lại).

## 1. Nguồn đã dùng

| Nguồn | Đạt ngưỡng? | File |
|---|---|---|
| Đào data (x/N, %, cách đếm chạy lại được, ≥5 ví dụ) | ☑ | `evidence/data-mining.md`, `evidence/mine_repos.py` |
| Khảo sát (≥20 người ngoài nhóm, đúng người dùng) | ☑ **n = 25** học viên đã nộp bài (chốt lúc 19:20 27/11) | `evidence/survey/results.csv`, `evidence/survey/tally.py` |
| Phỏng vấn (≥3 người ngoài nhóm, đúng người dùng) | ☐ 1 buổi lab coach (P4, không theo Mom Test) · 3 học viên chưa có ghi chép | `evidence/interviews/P4.md` |

## 2. Số chính

Chạy lại: `python evidence/survey/tally.py`. Khảo sát mở 17:31, 28 phiếu: 26 học viên + 2 lab coach. Bỏ 1 học viên chưa nộp lần nào → **n = 25** (L3B 20, L3A 5).

- **Đào data** (N = 135 repo sau CP1): **18/135 (13%)** repo thiếu hoặc chưa qua `check_teams()` của BTC · **6/135 (4%)** có chữ "AI" ở dòng pain, lỗi mà `run.py check` không bắt.
- **Khảo sát học viên** (n = 25):
  - Nộp nhiều: **16/25 (64%)** nộp trên 12 lần / 14 ngày.
  - Phát hiện lỗi sát giờ / sau khi nộp ≥1 lần trong 14 ngày: **20/25 (80%)**; 2–3 lần: 13/25 (52%).
  - Sự cố đã gặp (chọn nhiều): **PR / push nhầm repo gốc 13/25 (52%)** · nộp sót file / sai format 9/25 (36%) · lúng túng khi bị hỏi vặn 6/25 (24%) · lệch số / thiếu nguồn 3/25 (12%) · lộ key / .env 3/25 (12%) · sửa gấp / bị trừ điểm 2/25 (8%) · chưa gặp gì 6/25 (24%).
  - Thời gian tự rà lần gần nhất: dưới 5 phút 9/25 · 5–15 phút 10/25 · 16–30 phút 5/25 · trên 30 phút 1/25.
  - Cách soát: chạy script check 16/25 (64%) · **dán vào AI ngoài 15/25 (60%)** · đọc bằng mắt 10/25 (40%) · nhờ đọc chéo 6/25 (24%).
- **Khảo sát lab coach** (n = 2, không ghi %): cả 2 soát dưới 10 bài / 14 ngày, mất 15–30 phút mỗi đợt chỉ để rà lỗi format · lỗi lặp lại: 2/2 sót file / sai format, 1/2 PR nhầm repo gốc, 1/2 lộ API key · câu "lỗi script không bắt được": cả 2 bỏ trống.

| | Vai | Gặp pain? | Số lần / 1 tháng qua | Lần gần nhất mất | Đang xoay xở bằng |
|---|---|---|---|---|---|
| P1 | Học viên L3 | *chưa có ghi chép* | | | |
| P2 | Học viên L3 | *chưa có ghi chép* | | | |
| P3 | Học viên L3 | *chưa có ghi chép* | | | |
| P4 | Lab coach | Không hỏi theo Mom Test, xem `P4.md` | phiếu: dưới 10 bài / 14 ngày | phiếu: 15–30 phút / đợt | đọc tay |

## 3. ≥5 trích dẫn nguyên văn (câu 7 khảo sát, giữ nguyên chính tả, bỏ tên)

1. "phải xem lại xem đủ bài chưa" — phiếu `R03` (L3A)
2. "kiểm tra xem có ghi API không" — phiếu `R05` (L3B)
3. "thiếu một số file của thành viên nên cần liên hệ để vổ sung" — phiếu `R06` (L3B)
4. "Kiểm tra những file cần có trong repo github, nhất là các file báo cáo và bằng chứng" — phiếu `R18` (L3B)
5. "Quá nhiều file đã thay đổi và không biết nên push file nào" — phiếu `R22` (L3A)
6. "Không biết là tất cả đầu việc đã hoàn thành 100% chưa" — phiếu `R25` (L3A)
7. "Soát lại yêu cầu đề bài" — phiếu `R23` (L3B)

## 4. Các nguồn có khớp nhau không

- **Khớp:** đào data thấy 13% repo vẫn lỗi `TEAMS.md` dù có sẵn `run.py check`. Khảo sát thấy **13/16 người có chạy script check vẫn gặp ≥1 sự cố**, 9/25 nộp sót file / sai format, và 2/2 lab coach nêu lỗi này đầu tiên.
- **Chưa đủ để thay cho AI ngoài (trả lời câu hỏi "khác gì agent có sẵn?"):** trong 15 người đã dán bài vào AI ngoài, **11/15 vẫn gặp sự cố** và **6/15 vẫn PR / push nhầm repo gốc**. Lỗi PR nhầm nằm ở **trạng thái git / GitHub** (remote, đích của PR), không nằm trong phần bài được dán vào chat. Script check cũng không kiểm lỗi này.
- **Lệch:** đào data chỉ đo được lỗi format ở CP1, chưa đo được PR nhầm repo gốc. Có thể đếm thêm bằng cách đếm PR học viên mở nhầm vào repo gốc của khoá (cách đếm viết trước, chạy sau).

## 5. Kết luận

Giả thuyết ở `evidence/hypothesis.md` (≥60% n ≥ 20 từng nộp sót mục / thiếu nguồn / sai tiêu chí hoặc mất ≥15 phút dò):
- **Đúng chữ giả thuyết: 15/25 (60%), vừa chạm ngưỡng.** Tính cả các sự cố khác ở câu 5 (PR nhầm, lộ key, lúng túng khi bị hỏi vặn): 21/25 (84%). Luật đếm hai bản này được viết lúc tổng hợp (sau khi thu phiếu), ghi rõ trong `tally.py`.
- **Vế 2 (≥2/3 người phỏng vấn kể được lỗi script không bắt): chưa kiểm được.** Chưa có ghi chép phỏng vấn học viên; 2 lab coach bỏ trống câu C4.
- **Phải đổi trọng tâm:** pain lớn nhất là **PR / push nhầm repo gốc (52%)**, không phải dò rubric (chỉ 6/25 mất ≥16 phút). Trọng tâm nên là: kiểm trạng thái repo thật (đích PR, file .env, đủ file) bằng code, sau đó AI hỏi vặn.

**Điều vẫn chưa biết:**
- Có thành viên nhóm nào điền phiếu không (form ẩn danh).
- Học viên mất bao lâu để sửa sau khi PR nhầm.
- Hậu quả có phải mất điểm thật không: chỉ 2/25 nói bị trừ điểm hoặc phải sửa gấp.

## Tiến độ

| Nguồn | Kế hoạch | Đã làm đến đâu |
|---|---|---|
| Đào data | Repo `K5-Day15-L3*` sau CP1 | Xong lần 1 (17:20), N = 135 · chạy lại sau CP3 |
| Khảo sát | ≥20 học viên L3 ngoài nhóm | **Đạt: n = 25** (chốt 19:20 27/11) |
| Phỏng vấn | ≥3 học viên ngoài nhóm + 1–2 lab coach | 1 lab coach (P4) · 3 học viên đã hỏi nhưng chưa ghi chép |

## Lịch hẹn (chỉ ghi vai và giờ, không tên)

| Vai | Giờ hẹn | Đã xong? |
|---|---|---|
| Học viên L3 ngoài nhóm (P1) | chiều 27/11 | ☐ chưa có ghi chép |
| Học viên L3 ngoài nhóm (P2) | chiều 27/11 | ☐ chưa có ghi chép |
| Học viên L3 ngoài nhóm (P3) | chiều 27/11 | ☐ chưa có ghi chép |
| Lab coach (P4) | chiều 27/11 tại C401 | ☑ `P4.md` |
| Người trả lời phiếu đồng ý hỏi thêm | 3/25 phiếu đồng ý | ☐ |
