# Khảo sát ẩn danh — Rà soát & kiểm tra bài lab / repo trước hạn nộp (Track A · A6)

> **Hướng dẫn lưu & ẩn danh (guide bước 1.2):**
> - Link khảo sát công khai: https://forms.gle/amwVjGJB1xXrezYFA
> - Kênh gửi: __ *(điền khi gửi: Discord lớp L3B / L3A / nhóm Lab Coach...)*
> - Giờ mở: 27/11/2026 17:31 · Giờ chốt: __ *(mục tiêu ≥20 phản hồi ngoài nhóm, đúng người dùng)*
> - **Cài đặt Google Form:** Tắt *"Thu thập địa chỉ email"* (Do not collect) · Tắt *"Giới hạn ở 1 câu trả lời"* · Bật *"Hiển thị thanh tiến độ"* · Không hỏi tên, email, mã học viên.
> - **Khi xuất kết quả:** Chép thành `evidence/survey/results.csv`, **xoá hoàn toàn cột liên hệ (Câu 8 / C5)** và cột dấu thời gian chi tiết nếu có thể nhận diện trước khi commit. Bản thô giữ cục bộ theo rule `evidence/**/raw-*` (đã `.gitignore`).

---

## Tiêu đề & Phần mở đầu Form

**Tiêu đề Form:**
> **KHẢO SÁT ẨN DANH: CÁCH RÀ SOÁT BÀI LAB / REPO TRƯỚC HẠN NỘP TRONG KHOÁ AI20K**

**Mô tả Form (Lời chào mở đầu):**
> Chào bạn! Nhóm mình (Free2Play — lớp L3B, AI20K khoá 5) đang thực hiện một khảo sát nhỏ để tìm hiểu cách mọi người tự kiểm tra và rà soát bài lab / repo GitHub trước hạn nộp hoặc trước buổi demo: bạn thường kiểm gì, tốn bao nhiêu thời gian, và hay vướng lỗi gì nhất.
>
> • Thời gian điền: khoảng **2 phút** (8 câu ngắn, chủ yếu chọn đáp án).
> • Nội dung: hỏi về chuyện đã xảy ra trong 14 ngày lab qua hoặc lần nộp gần nhất — không có đúng / sai, không nhớ thì cứ chọn *"Không nhớ"*.
> • Bảo mật & ẩn danh: hoàn toàn ẩn danh, không thu email, họ tên hay mã học viên. Kết quả chỉ dùng cho bài mini hackathon và chỉ báo cáo ở dạng tổng hợp (vd *"14/25 người"*).
>
> Cảm ơn bạn đã dành chút thời gian quý báu hỗ trợ nhóm!

---

## Cấu trúc rẽ nhánh theo vai trò — Mỗi người chỉ điền đúng 2 trang (`Trang 1/2` → `Trang 2/2`)

### Phần 1 · Thông tin vai trò *(Trang 1 — Rẽ nhánh thông minh)*

**Câu 1. Bạn đang là:** *(Trắc nghiệm — Chọn một · Bắt buộc · Có rẽ nhánh)*
- `Học viên lớp L3A` → **Chuyển đến Phần 2 (Dành cho Học viên)**
- `Học viên lớp L3B` → **Chuyển đến Phần 2 (Dành cho Học viên)**
- `Lab Coach` → **Chuyển đến Phần 3 (Dành cho Lab Coach)**
- `Khác` → **Chuyển đến Phần 2 (Dành cho Học viên)**

---

### Phần 2 · Dành cho Học viên — Rà soát & nộp bài *(Trang 2 · Sau phần 2: Gửi biểu mẫu)*
*Mô tả phần: "Nghĩ về 14 ngày lab qua và đúng lần nộp bài gần nhất của bạn — không có đúng / sai."*

**Câu 2. Trong 14 ngày lab gần đây, bạn (hoặc nhóm bạn) đã nộp bài lab / repo GitHub khoảng mấy lần?** *(Trắc nghiệm — Chọn một · Bắt buộc)*
- `0 lần — chưa từng nộp` · `1–3 lần` · `4–8 lần` · `9–12 lần` · `Trên 12 lần` · `Không nhớ`

**Câu 3. Ở lần nộp bài lab / repo gần nhất, trước khi bấm nộp bạn đã kiểm tra bài bằng những cách nào?** *(Hộp kiểm — Chọn nhiều · Bắt buộc)*
*Mô tả: Chọn tất cả những cách bạn đã làm.*
- `Tự đọc lướt lại các file và đối chiếu bằng mắt với đề / rubric`
- `Chạy lệnh hoặc script kiểm tra có sẵn (vd python run.py check hoặc test)`
- `Nhờ bạn cùng nhóm / người khác đọc chéo`
- `Dán một phần bài vào công cụ AI bên ngoài để nhờ soát`
- `Nộp thẳng vì sát giờ, không kịp rà`
- `Mục khác:` *(cho phép nhập text ngắn)*

**Câu 4. Ở lần gần nhất đó, bạn mất khoảng bao lâu cho bước tự rà tiêu chí, format, nguồn số liệu trước khi nộp?** *(Trắc nghiệm — Chọn một · Bắt buộc)*
- `Dưới 5 phút` · `5–15 phút` · `16–30 phút` · `Trên 30 phút` · `Không rà / Không nhớ`

> *Khối tiêu đề phụ (`Tt`):* **Sự cố thực tế đã gặp (14 ngày qua)** — *"Chọn đúng những gì đã thực sự xảy ra."*

**Câu 5. Trong 14 ngày lab gần đây, bạn đã từng gặp tình huống nào dưới đây khi nộp hoặc bảo vệ bài chưa?** *(Hộp kiểm — Chọn nhiều · Bắt buộc)*
*Mô tả: Chọn tất cả những gì thực sự đã xảy ra với bạn.*
- `Nộp sót file, thiếu mục bắt buộc hoặc sai format (vd TEAMS, CSV, YAML)`
- `Fork bài từ khoá về nhưng tạo PR / push nhầm lên repo gốc của chương trình thay vì repo fork của mình`
- `Số liệu hoặc khẳng định trong bài bị lệch / thiếu nguồn giữa các file`
- `Suýt hoặc lỡ đưa thông tin nhạy cảm / API key / file .env lên repo`
- `Khi bị hỏi vặn lại về phần mình làm (kể cả phần có nhờ AI hỗ trợ), bị lúng túng chưa giải thích rõ ngay`
- `Phải sửa gấp sát giờ hoặc bị trừ điểm / mất điểm phần vì lỗi rà soát`
- `Chưa gặp lỗi nào trong các mục trên`
- `Mục khác:` *(cho phép nhập text ngắn)*

**Câu 6. Trong 14 ngày lab gần đây, khoảng mấy lần bạn phát hiện lỗi hoặc thiếu tiêu chí ngay sát giờ nộp / sau khi đã nộp?** *(Trắc nghiệm — Chọn một · Bắt buộc)*
- `0 lần` · `1 lần` · `2–3 lần` · `4 lần trở lên` · `Không nhớ`

**Câu 7. Ở lần gần nhất gặp vướng hoặc phải rà bài sát giờ, lỗi hay bước kiểm tra nào khiến bạn khó chịu hoặc tốn công nhất?** *(Đoạn văn dài · Không bắt buộc)*
*Mô tả: Không bắt buộc. Vui lòng không ghi tên người hay tên nhóm; có thể kể ngắn lỗi cụ thể bạn gặp.*

> *Khối tiêu đề phụ (`Tt`):* **Lời kết & Cảm ơn** — *"Cảm ơn bạn rất nhiều vì đã hoàn thành phần khảo sát chính và chia sẻ trải nghiệm thực tế cho nhóm Free2Play! Câu cuối bên dưới là tuỳ chọn — bạn có thể bỏ trống và bấm 'Gửi' ngay. Chúc bạn học tốt và đạt kết quả thật cao trong khoá AI20K!"*

**Câu 8. Bạn có sẵn lòng cho nhóm hỏi thêm 10 phút (hoặc dùng thử bản demo sáng Thứ Bảy 28/11) không?** *(Trả lời ngắn · Không bắt buộc)*
*Mô tả: Không bắt buộc. Nếu có, để lại Discord / Zalo hoặc vị trí ngồi ở phòng học; không thì bỏ trống.*

---

### Phần 3 · Dành cho Lab Coach — Kiểm tra & chấm bài học viên *(Trang 2 nhánh Lab Coach · Sau phần 3: Gửi biểu mẫu)*
*Mô tả phần: "Cảm ơn anh/chị Lab Coach đã hỗ trợ nhóm! Các câu ngắn dưới đây hỏi về trải nghiệm thực tế khi kiểm tra / chấm bài nộp của học viên trong 14 ngày lab qua."*

**Câu C1. Trong 14 ngày lab gần đây, anh/chị đã kiểm tra hoặc hỗ trợ chấm khoảng bao nhiêu bài lab / repo của học viên?** *(Trắc nghiệm — Chọn một · Bắt buộc)*
- `Dưới 10 bài` · `10–30 bài` · `31–60 bài` · `Trên 60 bài` · `Không nhớ`

**Câu C2. Khi soát / chấm bài nộp của học viên gần đây, những lỗi nào anh/chị thấy lặp lại nhiều nhất?** *(Hộp kiểm — Chọn nhiều · Bắt buộc)*
*Mô tả: Chọn tất cả những lỗi thực tế hay gặp.*
- `Nộp sót file, thiếu mục bắt buộc hoặc sai format (vd TEAMS, CSV, YAML)`
- `Fork bài từ khoá về nhưng tạo PR / push nhầm lên repo gốc của chương trình thay vì repo fork`
- `Số liệu / nhận định lệch hoặc không truy được nguồn giữa các file`
- `Lộ thông tin nhạy cảm / API key / file .env trong repo công khai`
- `Dùng AI hỗ trợ build nhưng khi bị hỏi vặn lại thì lúng túng không giải thích được`
- `Vi phạm quy tắc làm bài (vd pain có chữ AI, lát cắt quá rộng, sửa chuẩn đạt)`
- `Mục khác:` *(cho phép nhập text ngắn)*

**Câu C3. Trung bình mỗi buổi / mỗi đợt chấm, anh/chị mất khoảng bao lâu chỉ để rà lỗi kỹ thuật/format hoặc nhắc học viên sửa lại bài nộp?** *(Trắc nghiệm — Chọn một · Bắt buộc)*
- `Dưới 15 phút` · `15–30 phút` · `31–60 phút` · `Trên 60 phút` · `Không nhớ`

**Câu C4. Có lỗi nào mà script kiểm format (như python run.py check) KHÔNG bắt được mà anh/chị phải tự đọc mới thấy, hoặc lỗi nào khiến học viên mất điểm oan nhất?** *(Đoạn văn dài · Không bắt buộc)*
*Mô tả: Không bắt buộc. Vui lòng không ghi tên học viên hay tên nhóm.*

> *Khối tiêu đề phụ (`Tt`):* **Lời kết & Cảm ơn** — *"Cảm ơn anh/chị Lab Coach rất nhiều vì những chia sẻ thực tế cho nhóm Free2Play (L3B)! Câu cuối bên dưới là tuỳ chọn — anh/chị có thể bỏ trống và bấm 'Gửi' ngay."*

**Câu C5. Anh/chị có sẵn lòng cho nhóm hỏi thêm 5–10 phút (hoặc xem thử bản demo sáng Thứ Bảy 28/11) không?** *(Trả lời ngắn · Không bắt buộc)*
*Mô tả: Không bắt buộc. Nếu có, để lại Discord / Zalo hoặc khu vực ngồi ở lớp; không thì bỏ trống.*

---

**Thông báo xác nhận sau khi gửi Form:**
> Cảm ơn bạn đã hoàn thành khảo sát của nhóm Free2Play (L3B)! Chúc bạn một kỳ học AI20K thật nhiều trải nghiệm vui và đạt kết quả xuất sắc. Nếu bạn có để lại liên hệ ở câu cuối, nhóm sẽ nhắn hẹn nhanh 10 phút hoặc mời bạn trải nghiệm bản thử sáng Thứ Bảy 28/11 nhé!
