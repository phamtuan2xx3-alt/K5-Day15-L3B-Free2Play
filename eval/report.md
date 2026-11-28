# Báo cáo đánh giá — lượt 1 → một cải tiến → lượt 2

> Điền ở guide bước 4.1. Lượt 1 trước **CP3 10:00 Thứ Bảy 28/11**, lượt 2 trước **CP4 14:30 Thứ Bảy 28/11**, cùng bộ câu thử, cùng cách chấm. Chấm ở rubric R5.
> Số lấy từ `python run.py score eval/run-1.csv` (và `run-2.csv`) sau khi điền cột `pass`. **Kết quả thấp ghi thật vẫn đủ điểm.**
> Không được: sửa chuẩn "đạt", bỏ câu thử trượt, sửa `expected` cho khớp output, sửa kết quả lượt đã chạy.

## 1. Kết quả

| Lượt | Run ID | Đạt / tổng | % | thuong | kho | tu_choi | So với chuẩn "đạt" |
|---|---|---|---|---|---|---|---|
| 1 | `run-1@20261128-103540` | 29/30 | 97% | 13/13 | 11/12 | 5/5 | **đạt** (≥80% tổng · 100% lỗi cứng · 100% `tu_choi` · 100% bài sạch S01/S08/S21/S29) |
| 2 | `run-2@20261128-110603` | 29/30 | 97% | 12/13 | 12/12 | 5/5 | **đạt** (≥80% tổng · 100% lỗi cứng · 100% `tu_choi` · 100% bài sạch S01/S08/S21/S29 · trích dẫn hợp lệ 1.116/1.134 = 98,4% ≥ 95%) |

Model: `chib/deepseek-v4.1-flash` (`deepseek-v4.1-flash` qua Vilao API, OpenAI-compatible). Kết quả từng câu: `eval/run-1.csv`, `eval/run-2.csv`. Trace: `traces/run-1.jsonl`, `traces/run-2.jsonl`. Số chạy lại được bằng `python run.py score eval/run-1.csv` và `python run.py score eval/run-2.csv`.

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
- Kết quả: nhóm lỗi đó **0/1 → 1/1 (`S12` đạt; `kho`: 11/12 → 12/12 = 100%)**, đồng thời 2 khiếm khuyết `S21` (NO-AUTO-GRADE bắt nhầm `'42/100 review'`) và `S23` (gợi ý ID `S01–S30`) đều được sửa sạch · tổng **97% (29/30) → 97% (29/30)**.
- Câu nào **tệ đi** sau khi sửa: **`S17` (`thuong`, đạt → trượt):** vẫn phát hiện đúng mọi lỗi thiếu bằng chứng `R1-EVIDENCE` (khảo sát `12 < 20`, phỏng vấn `1 < 3`, chỉ `3 < 5` trích dẫn), nhưng do nội dung `S17` đề cập cấu trúc repo chuẩn nên model ghi nhầm tên file trích dẫn thành `evidence/summary.md:Lxx` thay vì tên file phẳng trong gói nộp `evidence_summary.md:Lxx` (bị `[HẬU KIỂM TRÍCH DẪN]` tự động cảnh báo ở 9 vị trí) → chấm trượt theo metric `trich_dan_dung_file_dong`.

## 4. Còn lại

- Lỗi chưa sửa + nguy hiểm thế nào: (1) ở `S17`, model đôi lúc viết nhầm tên đường dẫn chuẩn `evidence/summary.md` thay vì `evidence_summary.md` khi hai biến thể tên file cùng được nhắc trong prompt (tuy nhiên `verify_audit_output` đã tự gắn `[HẬU KIỂM TRÍCH DẪN]` cảnh báo ngay ở cuối báo cáo để học viên không bị dẫn nhầm); (2) mỗi câu mới chạy **1 lần** nên chưa biết thứ tự mức nghiêm trọng có ổn định tuyệt đối qua nhiều lần gọi không; (3) chưa có phần held-out và bộ câu là hồ sơ giả lập (seed 42) — PR nhầm repo gốc mới kiểm qua `meta.json` giả lập (bản Web RepoKSV đã bổ sung bước kiểm GitHub thật qua `codebase/github_guard.py`).
- Nếu có thêm 1 tuần: chạy ≥3 lần mỗi câu + tách ~20% held-out; ép chỉ trích đúng tên file xuất hiện trong `present_files` để dứt điểm lỗi `S17`; người dùng thử 2–3 nhóm thật (`validation/log.md`); kiểm `GIT-FORK-PR` trên dữ liệu PR thật của khoá.
