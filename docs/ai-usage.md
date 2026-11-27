# Khai báo dùng AI

README của nhóm có mục "Dùng AI vào việc gì" (2–3 dòng, bắt buộc). Ghi chi tiết vào bảng dưới đây.

> Luật của đề: dùng AI để làm bài thoải mái, nhưng **ai không giải thích được phần có tên mình thì phần đó nhận 0 điểm**. Khai thiếu không bị trừ; giấu mới bị.

| Việc | Công cụ AI | AI làm gì | Người kiểm/sửa gì | Ai phụ trách |
|---|---|---|---|---|
| Code bản chạy thử | Trợ lý AI (coding agent) | Viết khung kết nối đa provider (`codebase/ai.py`), 5 công cụ `@tool` (`codebase/tools.py`), luồng workflow 3 bước (`codebase/agent.py`) | Đọc hiểu, tự chạy kiểm thử `python run.py`, `eval --fake`, 7 ca benchmark (sửa regex từ chối `S15`, chuẩn hoá trích dẫn `Lxx`, dò dòng `meta.json`) | Đỗ Hồng Vỹ, Phạm Quang Tuấn |
| Prompt / thiết kế lời gọi mô hình | Trợ lý AI | Soạn khung system prompt bọc `<submission_data_untrusted>` chống prompt injection và yêu cầu trích `file:dòng` | Rà khớp `spec.md` §4 & §9, khoá hậu kiểm bằng code `verify_audit_output` | Phạm Quang Tuấn, Đỗ Hồng Vỹ |
| Đào data (viết script đếm, gợi ý nhãn) | Trợ lý AI | Viết script `evidence/mine_repos.py` (quét 135 repo CP1) và `evidence/survey/tally.py` (đếm 25 phiếu khảo sát) | Kiểm tay cách đếm khớp hàm `check_teams()` của BTC và kiểm chéo số dòng `results.csv` (`26` dòng, bỏ `R14` còn `n = 25`), khớp 100% | Phạm Quang Tuấn, Bùi Phan Thanh Phúc |
| Rà câu hỏi phỏng vấn / khảo sát | Trợ lý AI | Chỉ rà câu dẫn dắt theo Mom Test, tách luồng học viên / Lab Coach trên Google Form (`evidence/survey/questions.md`, `evidence/interviews/GUIDE.md`) | Cả nhóm tự thu thập 28 phiếu thật và phỏng vấn thật; xoá sạch cột liên hệ Câu 8/C5 trước khi commit | Đỗ Hồng Vỹ, Chu Văn Nhật, Bùi Phan Thanh Phúc |
| Viết câu thử (benchmark) | Trợ lý AI | Gợi ý biến thể câu chữ và rà lưới độ phủ 4 chiều cho `eval/benchmark.csv` (15 câu CP2) | Mỗi câu có `source` rõ ràng (`7/15 = 46.7%` từ `nguoi_dung` / `data_that`, `3` `tu_viet`, `5` `sinh_seed: 42`); chạy `python run.py check` không lỗi | Phạm Quang Tuấn, Chu Văn Nhật |
| Sinh data `synthetic` (nếu có) | Trợ lý AI | Viết `data/make_submissions.py` sinh 14 mini-repo giả lập (`S01..S15`, trừ `S10`) từ các dạng lỗi thật | `Seed = 42` · kiểm tay 15/15 hồ sơ, dùng key giả `sk-test-dummy-...` (không dùng dữ liệu/key thật) | Đỗ Hồng Vỹ, Phạm Quang Tuấn |
| Chấm cột `pass` bằng LLM (nếu có) | Không dùng | Không dùng LLM chấm (`eval/metric_spec.yaml` dùng `code` + `nguoi` chấm) | Đã đối chiếu chéo `5/5` output khung `fake` tại CP2; sẽ chấm tay độc lập 2 người (khớp ≥ 4/5) ở Lượt 1 CP3 | Đỗ Hồng Vỹ, Chu Văn Nhật |
| Slide, văn bản | Trợ lý AI | Rà cấu trúc `spec.md`, `canvas.md`, `data/DATA_CARD.md`, `eval/README.md`, `README.md` theo `02-guide.md` và `03-rubric.md` | Đối chiếu từng số liệu với `evidence/summary.md`, `data-mining.md`, `tally.py` và rà PR trước khi merge | Cả nhóm (Phạm Quang Tuấn duyệt chốt) |

**Không dùng AI để:** tạo người được phỏng vấn, trích dẫn, câu trả lời khảo sát; sửa kết quả các lượt đã chạy (`eval/run-*.csv`, `cost/simulate-*.csv`, `traces/`).
