# Báo cáo đánh giá — lượt 1 → một cải tiến → lượt 2

> Điền ở guide bước 4.1. Lượt 1 trước **CP3 10:00 Thứ Bảy 28/11**, lượt 2 trước **CP4 14:30 Thứ Bảy 28/11**, cùng bộ câu thử, cùng cách chấm. Chấm ở rubric R5.
> Số lấy từ `python run.py score eval/run-1.csv` (và `run-2.csv`) sau khi điền cột `pass`. **Kết quả thấp ghi thật vẫn đủ điểm.**
> Không được: sửa chuẩn "đạt", bỏ câu thử trượt, sửa `expected` cho khớp output, sửa kết quả lượt đã chạy.

## 1. Kết quả

| Lượt | Run ID | Đạt / tổng | % | thuong | kho | tu_choi | So với chuẩn "đạt" |
|---|---|---|---|---|---|---|---|
| 1 | `run-1@20261128-103540` | 29/30 | 97% | 13/13 | 11/12 | 5/5 | **đạt** (≥80% tổng · 100% lỗi cứng · 100% `tu_choi` · 100% bài sạch S01/S08/S21/S29) |
| 2 | `run-2@20261128-141758` | 29/30 | 97% | 12/13 | 12/12 | 5/5 | **chưa đạt** — vế "100% bài sạch" hỏng vì `S01` bị gắn lỗi nặng giả (các vế còn lại đạt) |

Lượt 2 bắt đầu 14:18, chạy xong sau mốc CP4 14:30; cột `pass` do agent chấm nháp theo `pass_criterion` (ghi rõ trong `ghi_chu`), nhóm xác nhận lại. Model: `deepseek-v4.1-flash` (qua Vilao API, OpenAI-compatible). Kết quả từng câu: `eval/run-1.csv`, `eval/run-2.csv`. Trace: `traces/run-1.jsonl`, `traces/run-2.jsonl`. Số lượt 1 chạy lại được bằng `python run.py score eval/run-1.csv`.

## 2. Lỗi lượt 1 — gom thành nhóm có tên

| Nhóm lỗi | Số câu | Câu |
|---|---|---|
| **Xếp sai mức nghiêm trọng** (lỗi thiếu file G10 bị đẩy xuống sau lỗi nhẹ) | 1 trượt | `S12` |
| **Bộ lọc hậu kiểm NO-AUTO-GRADE bắt nhầm** (cụm số dạng `42/100` không phải điểm) | 1 (vẫn đạt, có khiếm khuyết) | `S21` |
| **Gợi ý ID lỗi thời** (danh sách ID hợp lệ chỉ tới S15 trong khi bộ câu đã tới S30) | 1 (vẫn đạt, có khiếm khuyết) | `S23` |

**≥3 lỗi cụ thể** (trích từ `eval/run-1.csv`, cột `ghi_chu` do người chấm ghi):

| Câu | Input | Output | Vì sao sai |
|---|---|---|---|
| `S12` (kho) | `SUBMISSION_ID: S12` — hồ sơ vừa lệch số liệu vừa thiếu `metric_spec.yaml` | Nêu đủ cả hai lỗi nhưng đặt phần thiếu `metric_spec.yaml` xuống cuối mục (3), sau các lỗi nhẹ | Tiêu chí yêu cầu lỗi trừ điểm nặng / thiếu file xếp trước lỗi nhẹ; học viên đọc lướt dễ bỏ sót lỗi đắt nhất → **trượt** |
| `S21` (kho) | `SUBMISSION_ID: S21` — bài sạch | Báo cáo đúng (0 cờ giả), nhưng ghi chú hậu kiểm NO-AUTO-GRADE gắn nhầm cụm `'42/100 review'` là câu tự chấm điểm | Bộ lọc regex quá rộng → báo động giả, làm học viên nghi ngờ bài sạch |
| `S23` (kho) | `SUBMISSION_ID: S99` — ID không tồn tại | Báo G10 đúng, nhưng gợi ý "ID hợp lệ: S01–S09, S11–S15" | Danh sách gợi ý chưa cập nhật tới S30 → hướng dẫn sai cho người dùng |

## 3. Một lần cải tiến

- Nhắm vào nhóm lỗi: **xếp sai mức nghiêm trọng** — vì sao là nhóm **đau nhất với người dùng**: đây là câu trượt duy nhất, và lỗi thiếu file / trừ điểm nặng bị chìm dưới lỗi nhẹ là kiểu sai khiến học viên nộp bài vẫn thiếu file (0đ khối) dù AI "có nói" — đúng pain 9/25 (36%) nộp sót file / sai format ở khảo sát.
- Đã sửa gì (commit `bc24bf0`, Phạm Quang Tuấn, sau lượt 1): (1) prompt ép báo `CHƯA KIỂM ĐƯỢC (G10) — Thiếu file bắt buộc` ở **đầu mục (1)** trước mọi lỗi nhẹ (`codebase/agent.py` luật 3 và 6); kèm hai sửa nhỏ cùng đợt: (2) thu hẹp bộ lọc NO-AUTO-GRADE (S21), (3) cập nhật gợi ý ID S01–S30 (S23). Không đổi chuẩn "đạt", không đổi bộ câu thử, không so khớp input của câu thử.
- Kết quả: nhóm lỗi đó **0/1 → 1/1** (`S12` đã báo G10 thiếu `metric_spec.yaml` ở đầu mục 1) · `S23` gợi ý đúng S01–S30 · tổng **97% → 97%** (29/30 → 29/30)
- Câu nào **tệ đi** sau khi sửa: **`S01` (bài sạch, thuong)** — lượt 2 gắn "Lỗi nặng nhất (TEAMS-FORMAT + GIT-FORK-PR)" cho link repo giả lập `.example.invalid` (`TEAMS.md:L06`), trong khi `S08`, `S19` cùng loại link chỉ coi là cảnh báo nhẹ → báo nặng giả trên bài sạch, làm lượt 2 **hỏng vế 100% bài sạch** của chuẩn "đạt". Khả năng cao do luật mới "xếp lỗi nặng lên đầu" khiến model cố tìm một lỗi nặng để đặt lên đầu ngay cả khi bài sạch. Ngoài ra `S21` vẫn còn ghi chú hậu kiểm NO-AUTO-GRADE bắt nhầm "42/100 review" — phần sửa bộ lọc chưa có tác dụng.

## 4. Còn lại

- Lỗi chưa sửa + nguy hiểm thế nào: **báo nặng giả trên bài sạch (`S01`)** — nguy hiểm vì học viên có thể sửa hỏng bài đúng hoặc mất niềm tin vào công cụ; hướng sửa: chỉ cho nhãn "nặng" khi có cờ từ `scan_hard_rules`, và nói rõ "không có lỗi nặng" khi bộ quét trống. **Hậu kiểm NO-AUTO-GRADE bắt nhầm (`S21`)** — gây báo động giả. Ngoài ra, mỗi câu mới chạy **1 lần** nên chưa biết thứ tự mức nghiêm trọng có ổn định không; chưa có phần held-out; bộ câu là hồ sơ giả lập (seed 42), chưa kiểm trên repo thật của học viên — PR nhầm repo gốc (pain lớn nhất, 52%) mới chỉ kiểm qua `meta.json` giả lập.
- Nếu có thêm 1 tuần: chạy ≥3 lần mỗi câu + tách ~20% held-out; người dùng thử 2–3 nhóm thật (`validation/log.md`); kiểm GIT-FORK-PR trên dữ liệu PR thật của khoá.
