# Chi phí khi dùng thật

> Điền ở guide bước 4.2, nộp ở CP4 14:30 Thứ Bảy 28/11. Ôn lại: ngày 13, ngày 1, ngày 14 · lab ngày 13, lab ngày 14. Chấm ở rubric R6.
> Số **không điền tay**: điền `cost/personas.yaml` → `python run.py simulate` → chép bảng trong `cost/simulate-N-summary.md` vào đây.
> Lúc build dùng gói miễn phí vẫn tính theo **giá gói trả phí** — đây là chi phí cho lúc đưa vào dùng thật.

## 1. Đầu vào

- **Persona** (`cost/personas.yaml`): ≥3 kiểu — tỉ lệ, số phiên / người / tháng, số lượt hỏi / phiên. Nguồn: khảo sát n = 25, câu 2 "nộp bao nhiêu lần / 14 ngày" (`evidence/survey/results.csv`, đếm bằng `evidence/survey/tally.py`); bỏ 1 phiếu "Không nhớ" → 24 người chia 3 nhóm:

  | Persona | Tỉ lệ | Phiên / người / tháng | Lượt hỏi / phiên | Nguồn |
  |---|---|---|---|---|
  | `nop_it` | 17% (4/24) | 9 | 1 | câu 2: nộp 1–8 lần / 14 ngày · điểm giữa × 2 *(tự ước tính)* · số lượt *(tự ước tính)* |
  | `nop_vua` | 17% (4/24) | 21 | 2 | câu 2: nộp 9–12 lần / 14 ngày · điểm giữa × 2 *(tự ước tính)* · số lượt *(tự ước tính)* |
  | `nop_nhieu` | 66% (16/24) | 26 | 2 | câu 2: nộp trên 12 lần / 14 ngày · cận dưới 13 × 2 *(tự ước tính)* · số lượt *(tự ước tính)* |

  Giả định 1 lần nộp = 1 phiên soát *(tự ước tính)*.
- **Số người dùng thật** 3 kịch bản: thấp **300** · cơ sở **700** · cao **1.000**. Nguồn: cơ sở = lớp L3 hơn 700 học viên, cao = cả khoá hơn 1.000 học viên (README và guide 4.2 của bộ đề hackathon K5) · thấp = chỉ khoảng 300 người dùng thường xuyên *(tự ước tính)*.
- **Giá** ≥2 mức model (từ `further-reading/model-prices.md` của repo đề, BTC xem trang giá chính thức ngày **25/11/2026**, USD / 1 triệu token):
  - Tầng Nhỏ — `gemini-3.1-flash-lite`: vào 0.25 · ra 1.50 — https://ai.google.dev/gemini-api/docs/pricing
  - Tầng Lớn — `gemini-4-hydrogen`: vào 1.50 · ra 7.50 — https://ai.google.dev/gemini-api/docs/pricing
  - ⏳ Nếu Cặp X nối model hãng khác thì đổi 2 dòng `prices` trong `cost/personas.yaml` sang model đó (cùng bảng BTC) để chi phí / task thành công dùng **cùng model** với tỉ lệ đạt lượt 2.
- **Tỉ lệ đạt** dùng để tính: ⏳ __/25 (__%) — lượt `run-__` (lượt 2) · *chờ eval lượt 2 trước CP4*
- Đo token trên model ⏳ __ *(model Cặp X nối ở `codebase/ai.py`, chưa có lúc 23:30 27/11)*, tính giá model `gemini-3.1-flash-lite` và `gemini-4-hydrogen`

## 2. Kết quả mô phỏng

Lượt mô phỏng: ⏳ `cost/simulate-__.csv` · run ID __ · 50 phiên · seed 42 *(đã chốt trong `cost/personas.yaml`; chạy sau khi nối model thật — `cost/simulate-mock.csv` chạy chế độ giả, token = 0, không dùng để tính)*

*(dán bảng từ `cost/simulate-N-summary.md`)*

| Model | Chi phí / phiên | Chi phí / task thành công | / tháng — thấp | / tháng — cơ sở | / tháng — cao | / người / tháng (cơ sở) |
|---|---|---|---|---|---|---|
| | | | | | | |
| | | | | | | |

Chi phí / task thành công = chi phí trung bình mỗi phiên ÷ tỉ lệ đạt — **không coi như đạt 100%**.

## 3. So với impact

- Impact / người / tháng (`spec.md` §2): **≈ 4,1 giờ tự rà / người / tháng** (22,26 lần × 11,08 phút, từ khảo sát n = 25 câu 2 và câu 4, điểm giữa *(tự ước tính)*) + rủi ro lỗi cứng: 52% từng PR nhầm repo gốc (đào data: ≥436 tài khoản, 865 PR — `evidence/data-mining.md` phần 7), 12% từng suýt / lỡ lộ key
- Chi phí / người / tháng (cơ sở, model __): ⏳ *chép từ `cost/simulate-N-summary.md` sau khi chạy `python run.py simulate` với model thật*
- **Kết luận một dòng — đáng làm không:** ⏳ *viết sau khi có chi phí thật — không viết trước*

## 4. *(Muốn sâu hơn, không bắt buộc)*

- Bảng độ nhạy: model rẻ hơn · cache · cắt ngữ cảnh · giới hạn bước — mỗi cần gạt đổi chi phí bao nhiêu
- Chi phí ngoài model: hosting, lưu trữ, giờ công người duyệt
- Quy mô nào thì bài toán còn đáng làm
