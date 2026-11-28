# Chi phí khi dùng thật

> Điền ở guide bước 4.2, nộp ở CP4 14:30 Thứ Bảy 28/11. Ôn lại: ngày 13, ngày 1, ngày 14 · lab ngày 13, lab ngày 14. Chấm ở rubric R6.
> Số **không điền tay**: điền `cost/personas.yaml` → `python run.py simulate` → chép bảng trong `cost/simulate-N-summary.md` vào đây.
> Lúc build dùng gói miễn phí vẫn tính theo **giá gói trả phí** — đây là chi phí cho lúc đưa vào dùng thật.

## 1. Đầu vào

- **Persona** (`cost/personas.yaml`): 3 kiểu — `nop_it` 17% · 9 phiên / tháng · 1 lượt; `nop_vua` 17% · 21 phiên · 2 lượt; `nop_nhieu` 66% · 26 phiên · 2 lượt. Nguồn: câu 2 khảo sát n = 25 (`evidence/survey/results.csv`, `tally.py`); số lượt / phiên *(tự ước tính)*.
- **Số người dùng thật** 3 kịch bản: thấp 300 *(tự ước tính)* · cơ sở 700 (lớp L3, README bộ đề) · cao 1.000 (cả khoá, README bộ đề).
- **Giá** 2 mức model (`data-btc/further-reading/model-prices.md`, BTC xem 25/11/2026): `deepseek-flash` $0,30 vào / $1,20 ra per 1M token (giờ cao điểm, https://api-docs.deepseek.com/quick_start/pricing) · `gpt-6.2-sol` $2,00 / $10,00 (OpenAI Standard).
- **Tỉ lệ đạt** dùng để tính: **29/30 (97%) — lượt `run-2@20261128-110603`** (`eval/run-2.csv`, chạy `--rate-from eval/run-2.csv`).
- Đo token trên model `chib/deepseek-v4.1-flash` (`Vilao API`, token lấy từ trường `usage`, đã tắt suy nghĩ `enable_thinking=False`), tính giá model `deepseek-flash` và `gpt-6.2-sol`.

## 2. Kết quả mô phỏng

Lượt mô phỏng: `cost/simulate-1.csv` · run ID **`simulate-1@20261128-144417`** · **50 phiên** (`0/50` phiên lỗi) · `seed 42` · `traces/simulate-1.jsonl`. Bảng dưới chép nguyên văn từ `cost/simulate-1-summary.md`:

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên | Gọi công cụ / phiên |
|---|---:|---:|---:|---:|---:|---:|
| nop_it | 8 | 1 | 3905 | 1856 | 0.8 | 7.4 |
| nop_vua | 13 | 2 | 9353 | 4079 | 1.8 | 17.6 |
| nop_nhieu | 29 | 2 | 10195 | 4556 | 1.9 | 19.1 |

| Model (giá) | Chi phí / phiên | Chi phí / task thành công | Chi phí / câu hỏi đạt | Chi phí / tháng — thấp (300 người) | Chi phí / tháng — cơ sở (700 người) | Chi phí / tháng — cao (1.000 người) | Chi phí / người / tháng (cơ sở) |
|---|---:|---:|---:|---:|---:|---:|---:|
| deepseek-flash (vào 0.3 · ra 1.2 $/1M) | $0.0075 | $0.0077 | $0.0042 | $53.70 | $125.29 | $178.99 | $0.1790 |
| gpt-6.2-sol (vào 2.0 · ra 10.0 $/1M) | $0.0579 | $0.0599 | $0.0326 | $415.33 | $969.09 | $1,384.42 | $1.38 |

Chi phí / task thành công = chi phí / phiên ÷ tỉ lệ đạt (`0,9667`) — **không coi như đạt 100%**. Chi phí / câu hỏi đạt = chi phí / phiên ÷ số lượt hỏi trung bình mỗi phiên (`1,8`) ÷ tỉ lệ đạt. Đo trên model `chib/deepseek-v4.1-flash`, tính giá model `deepseek-flash` và `gpt-6.2-sol` (tắt `enable_thinking=False` giúp giảm mạnh `reasoning_tokens` nên chi phí thực tế thấp hơn ~41% so với ước tính tạm khi bật suy nghĩ).

## 3. So với impact

- Impact / người / tháng (`spec.md` §2): ≈ 4,1 giờ tự rà tiết kiệm (22,26 lần × 11,08 phút).
- Chi phí / người / tháng (cơ sở, model `deepseek-flash`): **$0,1790** (**$1,38** nếu dùng `gpt-6.2-sol`).
- **Kết luận một dòng — đáng làm không:** Rất đáng làm — chỉ **$0,1790 / người / tháng** (**$0,0077 / task thành công**, toàn lớp 700 học viên chỉ **$125,29 / tháng**) đổi lấy ≈ 4,1 giờ tự rà và chặn lỗi trừ điểm nặng (−10đ / 0đ khối), trong khi bản Lượt 2 trên model rẻ đã đạt **97%** nên chưa cần nâng lên tầng model đắt gấp ~8 lần.

## 4. *(Muốn sâu hơn, không bắt buộc)*

- Bảng độ nhạy: model rẻ hơn · cache · cắt ngữ cảnh · giới hạn bước — mỗi cần gạt đổi chi phí bao nhiêu
- Chi phí ngoài model: hosting, lưu trữ, giờ công người duyệt
- Quy mô nào thì bài toán còn đáng làm
