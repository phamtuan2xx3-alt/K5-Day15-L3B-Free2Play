# Chi phí khi dùng thật

> Điền ở guide bước 4.2, nộp ở CP4 14:30 Thứ Bảy 28/11. Ôn lại: ngày 13, ngày 1, ngày 14 · lab ngày 13, lab ngày 14. Chấm ở rubric R6.
> Số **không điền tay**: điền `cost/personas.yaml` → `python run.py simulate` → chép bảng trong `cost/simulate-N-summary.md` vào đây.
> Lúc build dùng gói miễn phí vẫn tính theo **giá gói trả phí** — đây là chi phí cho lúc đưa vào dùng thật.

## 1. Đầu vào

- **Persona** (`cost/personas.yaml`): 3 kiểu — `nop_it` 17% · 9 phiên / tháng · 1 lượt; `nop_vua` 17% · 21 phiên · 2 lượt; `nop_nhieu` 66% · 26 phiên · 2 lượt. Nguồn: câu 2 khảo sát n = 25 (`evidence/survey/results.csv`, `tally.py`); số lượt / phiên *(tự ước tính)*.
- **Số người dùng thật** 3 kịch bản: thấp 300 *(tự ước tính)* · cơ sở 700 (lớp L3, README bộ đề) · cao 1.000 (cả khoá, README bộ đề).
- **Giá** 2 mức model (`data-btc/further-reading/model-prices.md`, BTC xem 25/11/2026): `deepseek-flash` $0,30 vào / $1,20 ra per 1M token (giờ cao điểm, https://api-docs.deepseek.com/quick_start/pricing) · `gpt-6.2-sol` $2,00 / $10,00 (OpenAI Standard).
- **Tỉ lệ đạt** dùng để tính: **tạm 29/30 (97%) — lượt `run-1`** vì lượt 2 chưa xong lúc CP4; thay bằng tỉ lệ `run-2` khi có (`python run.py simulate --rate-from eval/run-2.csv`).
- Đo token trên model `deepseek-v4.1-flash` (Vilao API, token lấy từ `usage`), tính giá model `deepseek-flash` và `gpt-6.2-sol`.

## 2. Kết quả mô phỏng

**Trạng thái tại CP4 14:30:** `python run.py simulate` (50 phiên, seed 42) **đang chạy**, chưa có `cost/simulate-N.csv`. Bảng dưới là **ước tính tạm** từ token đo thật ở `eval/run-1.csv` (30 câu, mỗi câu = 1 lượt soát): trung bình **4.517 token vào + 9.430 token ra / lượt** (135.501 / 282.888 ÷ 30). Khi mô phỏng xong sẽ thay bằng bảng trong `cost/simulate-N-summary.md` và ghi `spec.md` §10.

| Model | Chi phí / lượt | Chi phí / task thành công (÷ 0,97) | / tháng — thấp (300) | / tháng — cơ sở (700) | / tháng — cao (1.000) | / người / tháng (cơ sở) |
|---|---|---|---|---|---|---|
| `deepseek-flash` | $0,0127 | $0,0131 | ≈ $87 | ≈ $204 | ≈ $291 | ≈ $0,29 |
| `gpt-6.2-sol` | $0,1033 | $0,1065 | ≈ $711 | ≈ $1.660 | ≈ $2.371 | ≈ $2,37 |

Cách tính: chi phí / lượt = 4.517 × giá vào + 9.430 × giá ra (per token) · / người / tháng = chi phí / task thành công × 22,26 lượt (bình quân gia quyền persona: 0,17×9 + 0,17×21 + 0,66×26; chưa nhân số lượt / phiên — mô phỏng sẽ tính đủ) · / tháng = / người × số người. Chi phí / task thành công = chi phí trung bình mỗi lượt ÷ tỉ lệ đạt — **không coi như đạt 100%**. Token ra cao vì model tính cả token suy luận (`reasoning_tokens`).

## 3. So với impact

- Impact / người / tháng (`spec.md` §2): ≈ 4,1 giờ tự rà tiết kiệm (22,26 lần × 11,08 phút).
- Chi phí / người / tháng (cơ sở, model `deepseek-flash`): ≈ $0,29 (≈ $2,37 nếu dùng `gpt-6.2-sol`).
- **Kết luận một dòng — đáng làm không:** Đáng làm với model rẻ — chưa tới $0,30 / người / tháng đổi lấy ≈ 4 giờ tự rà; model mạnh đắt gấp ~8 lần mà Lượt 1 trên model rẻ đã đạt 97%, nên chưa cần nâng tầng.

## 4. *(Muốn sâu hơn, không bắt buộc)*

- Bảng độ nhạy: model rẻ hơn · cache · cắt ngữ cảnh · giới hạn bước — mỗi cần gạt đổi chi phí bao nhiêu
- Chi phí ngoài model: hosting, lưu trữ, giờ công người duyệt
- Quy mô nào thì bài toán còn đáng làm
