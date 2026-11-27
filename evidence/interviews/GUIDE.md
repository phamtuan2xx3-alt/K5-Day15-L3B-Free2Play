# Kịch bản phỏng vấn 10 phút — Theo chuẩn The Mom Test (Track A · A6)

> Dùng tại lớp C401 chiều 27/11 (lab coach chỉ gặp được 16:00–19:30). Mỗi người một file `P1.md`, `P2.md`… chép từ [TEMPLATE.md](TEMPLATE.md).
> **3 Quy tắc vàng (Mom Test):**
> 1. **Tuyệt đối không giới thiệu sản phẩm/ý tưởng** ("nhóm mình định làm giám khảo ảo…"). Nói về công việc nộp lab/repo của họ.
> 2. **Chỉ hỏi chuyện cụ thể đã xảy ra trong 14 ngày qua** ("lần gần nhất…"), **không** hỏi "bạn có muốn/sẽ dùng không?".
> 3. **Đi theo cặp 2 người:** 1 người hỏi, 1 người gõ chép nguyên văn. Không ghi họ tên, mã học viên, email, SĐT, điểm số cụ thể; chỉ ghi `P1`, `P2`, `P3` + vai. Không ghi âm nếu chưa được đồng ý.

---

## Phần A — Phỏng vấn Học viên L3 ngoài nhóm (≥3 người · 10–15 phút/người)

**Lời mở đầu (30 giây):**
> *"Chào bạn, nhóm mình đang tìm hiểu cách mọi người tự kiểm tra bài lab và repo GitHub trước hạn nộp trong khoá này. Bạn cho mình xin 10 phút hỏi về **lần nộp bài gần nhất** được không? Hoàn toàn ẩn danh, không ghi tên và không giới thiệu sản phẩm gì cả."*

| Thời gian | Câu hỏi chính (hỏi đúng thứ tự) | Mục đích lấy số liệu & insight |
|---|---|---|
| **Phút 1–2** | **1.** *"Trong 14 ngày lab qua, bạn (hoặc nhóm) nộp bài qua GitHub mấy lần? Kể lại **lần gần nhất** bạn rà bài trước khi nộp diễn ra thế nào?"* | Lấy tần suất/tháng (R2, R6) + neo vào 1 sự kiện thật |
| **Phút 3–4** | **2.** *"Lúc rà bài lần đó, bạn kiểm những gì, dùng công cụ hay cách gì, và mất khoảng bao nhiêu phút?"* | Lấy thừa số phút/lần + cách xoay xở hiện tại |
| **Phút 5–6** | **3.** *"Trong 2 tuần qua, có lần nào bạn nộp rồi mới phát hiện sót mục, sai format, lệch số liệu, suýt lộ key/`.env`, tạo PR nhầm repo gốc, hoặc tới lúc bị hỏi lại mới thấy chưa nắm rõ phần đó không? Kể chi tiết lần nặng nhất."* | Lấy lỗi thật + trích dẫn nguyên văn (R1) + nguồn cho `benchmark.csv` |
| **Phút 7** | **4.** *"Bạn từng nhờ ChatGPT / Claude / AI khác soát bài theo rubric chưa? Lần gần nhất kết quả thế nào — nó bắt được gì, bỏ sót gì?"* | Trả lời bằng chứng thực tế câu *"vì sao không dùng ChatGPT/Claude?"* |
| **Phút 8** | **5.** *"Chuyện thiếu sót đó gây hậu quả gì cho bạn (sửa gấp mất bao lâu, mất điểm, bị hỏi vặn câu gì mà lúng túng…)? Vì sao cách tự rà hiện tại vẫn chưa chặn được lỗi đó?"* | Đào chỗ hỏng & vì sao chưa bỏ cách cũ (JTBD) |
| **Phút 9–10** | **6. (Chốt cam kết — Bonus +5đ):** *"Cảm ơn bạn rất nhiều. Sáng mai (Thứ Bảy 28/11) trước 13:00 nhóm mình có bản thử liên quan tới việc rà bài nộp này, bạn có sẵn lòng dành 5–10 phút dùng thử rồi góp ý giúp nhóm không?"* | Lấy cam kết người dùng thử cho `validation/log.md` (Bonus +5đ) |

### 3 Phản xạ xử lý tình huống khi phỏng vấn
- **Nếu họ nói chung chung** (*"Mình thường kiểm kỹ lắm"* / *"Cũng hay bị sót"*) → Neo lại ngay: *"Lần gần nhất bị sót là bài nào, hôm nào, lúc đó sót đúng cái gì?"*
- **Nếu họ hỏi ngược** (*"Các bạn định làm app gì à?"*) → Hoãn khéo: *"Tụi mình đang tìm hiểu xem vấn đề nào thật sự mất công nhất trước đã, xong câu này mình kể bạn nghe liền!"*
- **Nếu họ tự gợi ý giải pháp** (*"Ước gì có tool check hết trước khi push"*) → Đào động cơ: *"Cái đó giúp bạn làm được gì? Nếu kiểm được thì chỗ nào bạn sợ sót nhất mà script thường không thấy?"*

---

## Phần B — Phỏng vấn Lab Coach / Key Coach tại C401 (1–2 người · 5–10 phút)

*Dùng để làm nguồn đối chứng (R1) xem góc nhìn người chấm/soát bài có khớp với góc nhìn học viên hay không.*

**Lời mở đầu:**
> *"Chào anh/chị coach, nhóm em đang tìm hiểu các lỗi phổ biến học viên hay gặp khi nộp lab/repo trong 2 tuần qua để làm bài hackathon. Anh/chị cho em xin 5–7 phút hỏi vài câu thực tế lúc anh/chị chấm hoặc hỗ trợ lớp được không ạ?"*

1. *"Lần gần nhất anh/chị chấm hoặc soát bài nộp là khi nào? Bao nhiêu bài, mất bao lâu?"*
2. *"Trong 2 tuần lab qua, lỗi nào học viên hay dính nhất khi nộp? Kể lại một bài cụ thể gần đây (không cần tên)."*
3. *"Lỗi nào anh/chị thấy đắt nhất với học viên (mất nhiều điểm nhất hoặc làm anh/chị mất thời gian nhắc lại nhất)?"*
4. *"Có lỗi nào script kiểm format (như `python run.py check`) không bắt được mà anh/chị phải đọc mới thấy không?"*
5. *"Khi hỏi vặn học viên lúc demo, câu nào hoặc biểu hiện nào làm học viên lúng túng nhất về phần có dùng AI hỗ trợ?"*
6. *"Anh/chị có soát nháp trước cho nhóm nào không? Nếu không, vì sao?"*

---

## Sau mỗi buổi (5 phút)
1. Mở [TEMPLATE.md](TEMPLATE.md), lưu thành `P1.md`, `P2.md`, `P3.md`… (Lab Coach ghi `P4_LabCoach.md`…).
2. Điền đủ: câu đã hỏi · ghi chép · **số nghe được** (số lần/tháng, số phút, đang xoay xở bằng gì) + **1–2 câu trích nguyên văn** (đã bỏ tên riêng) + kết luận 1 dòng (có gì **ngược** với giả thuyết của nhóm không?).
3. Mỗi **lỗi cụ thể** người dùng kể → ghi thêm 1 dòng vào cuối file `P_.md` dạng: `Lỗi: … | phát hiện lúc: … | hậu quả: …` để chuyển thẳng thành câu thử (`source = nguoi_dung: P_`).
4. Cập nhật bảng số liệu ở `evidence/summary.md` mục 2.
