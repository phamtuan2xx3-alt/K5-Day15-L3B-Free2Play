# AI SPEC — Giám khảo ảo soát lỗi bài nộp & hỏi vặn phản biện theo Rubric · Nhóm Free2Play · Phòng C401 · Zone L3B

> Mốc nộp: §7 chốt chuẩn "đạt" tại **CP2 19:30 Thứ Sáu 27/11** · §0–§7 nộp **CP3 10:00 Thứ Bảy 28/11** · đủ §0–§10 **CP4 14:30 Thứ Bảy 28/11** · §10 changelog ghi tiếp đến **23:59 Thứ Bảy 28/11**.
> Đầu mỗi mục ghi bước guide (`02-guide.md` trong repo đề) chỉ cách điền. Mỗi mục ngắn, có số và nguồn; chi tiết để ở file được trỏ tới. Xoá dòng hướng dẫn trong ngoặc vuông khi điền xong.

Track: [x] A · [ ] B · [ ] C · [ ] D · [ ] E — bài toán: A6 · Giám khảo ảo soát lỗi bài nộp & hỏi vặn phản biện theo Rubric (hướng khác trong khoá AI20K)
Data BTC cấp đã dùng (nếu có — không commit nguyên file): Không dùng `data/preclass` hay `data/training-ops` làm bằng chứng; chỉ đối chiếu cấu trúc đề/rubric chính thức của khoá AI20K. Nhóm tự thu bằng chứng khảo sát/phỏng vấn và tự dựng dữ liệu bài nộp mẫu (`synthetic`).

## §0. Hiện tại việc này diễn ra thế nào *(guide 1.1)*
- Luồng hiện tại của việc này, trong khoá hoặc trên app thật (3–5 bước; ảnh chụp từ tài khoản của mình, đã che thông tin):
  1. Học viên làm bài lab (GĐ1 15 ngày) hoặc đồ án/hackathon trên GitHub gồm nhiều file (`TEAMS.md`, `spec.md`, `evidence/`, `eval/`, `cost/`, slide…).
  2. Gần sát hạn nộp, học viên mở `03-rubric.md` / `02-guide.md` để tự rà bằng mắt từng hạng mục, tự kiểm tra nguồn số liệu và rà soát lộ API key/thông tin cá nhân.
  3. Nhóm chạy lệnh `python run.py check` (nếu là khung repo hackathon) để kiểm cú pháp CSV/YAML/TEAMS trước khi push GitHub.
  4. Khi demo hoặc chấm bài, Lab Coach / giám khảo hỏi vặn trực tiếp từng thành viên về phần việc mang tên mình.
- Công cụ / AI đang được dùng cho việc này (nếu có) + nguồn. Không kiểm được thì ghi "chưa kiểm":
  - `python run.py check` trong bộ khung BTC phát (chỉ kiểm tra cấu trúc cột `eval/benchmark.csv`, `eval/metric_spec.yaml`, `TEAMS.md`; không đối chiếu chéo bằng chứng giữa các file, không quét lộ key/PII và không sinh câu hỏi phản biện — nguồn: `eval/run_eval.py` của bộ khung).
  - Một số học viên tự dán từng đoạn vào ChatGPT/Claude để nhờ đọc thử nhưng thiếu ngữ cảnh chéo toàn bộ hồ sơ và rubric khoá.

## §1. Người dùng & bằng chứng *(guide 1.1, 1.2)*
- Người dùng chính (một vai cụ thể): Học viên L3 (và nhóm làm đồ án/hackathon AI20K) đang rà soát bài lab/repo trong 1–2 giờ cuối trước hạn nộp và trước buổi demo.
- Việc họ cố làm xong (`động từ + đối tượng + bối cảnh`, không có chữ AI): Kiểm tra đầy đủ tiêu chí rubric, tính nhất quán số liệu giữa các file và chuẩn bị trả lời phản biện cho bài lab/repo trước hạn nộp của khoá AI20K.
- Hôm nay họ giải bằng gì, hỏng ở đâu, vì sao chưa bỏ: Họ tự rà thủ công qua nhiều file + chạy `python run.py check` + hỏi chéo bạn cùng nhóm. Cách này hỏng ở chỗ: dễ sót mục rải rác nhiều file, không phát hiện số liệu lệch/không có nguồn giữa `spec`–`evidence`–`eval`–`slide`, dễ lọt thông tin nhạy cảm/API key (−10đ), và không biết trước giám khảo sẽ hỏi vặn chỗ nào yếu nhất. Chưa bỏ vì chưa có công cụ tự kiểm chéo theo đúng rubric và luật trừ điểm của khoá.
- Pain (KHÔNG chữ AI): Học viên L3 khi rà soát bài lab/repo trước hạn nộp phải tự đối chiếu thủ công hàng chục tiêu chí rubric rải rác nhiều file, nên dễ nộp sót bằng chứng, lệch số liệu, lộ thông tin nhạy cảm hoặc không lường trước chỗ yếu khi bị hỏi phản biện → mất thời gian dò tay và bị trừ điểm oan hoặc nhận 0 điểm phần không giải thích được.
- Bằng chứng — số chính + kết luận (chi tiết: `evidence/summary.md`): Đang thu thập theo giả thuyết tại `evidence/hypothesis.md` (Khảo sát ≥20 học viên L3 ngoài nhóm + Phỏng vấn ≥3 học viên L3 và 1–2 Lab Coach tại phòng C401 — cập nhật kết quả ở CP2–CP3).

## §2. Impact & quyết định chọn *(guide 1.3)*

| Hướng | Bao nhiêu người gặp | Bao nhiêu lần / tháng | Mỗi lần tốn gì | Impact / tháng | Làm kịp không | Chọn? |
|---|---|---|---|---|---|---|
| 1. Soát lỗi bài nộp & hỏi vặn phản biện theo rubric (A6) | >700 HV L3 / >1.000 HV cả khoá (README đề) | *(đang thu từ khảo sát & phỏng vấn — cập nhật ở CP2–CP3)* | Thời gian tự dò rubric + rủi ro trừ 10đ / 0đ khối | *(cập nhật CP2–CP3)* | Kịp (workflow 3 bước, code tool + 1 lượt model) | **Chọn** |
| 2. Khách hàng ảo tập phỏng vấn Mom Test (A6) | >700 HV L3 (README đề) | *(ước tính 1–2 lần/khoá trước ngày khảo sát)* | Lỗi hỏi dẫn dắt khi phỏng vấn | Thấp hơn (tần suất ít hơn nộp lab) | Kịp | Loại |
| 3. Ghép nhóm / ghép mentor theo giờ rảnh (A6) | >700 HV L3 (README đề) | *(ước tính 1 lần/đợt ghép nhóm)* | Thời gian tìm nhóm lệch giờ | Thấp (chỉ dùng 1 lần/đợt; bài toán tối ưu hoá hợp code thuần) | Kịp | Loại |

- **Impact / tháng** của hướng chọn = __ người × __ lần × __ phút = __ — nguồn từng thừa số: *(đang thu số lần/tháng và số phút/lần từ khảo sát ≥20 HV & phỏng vấn ≥3 HV/Lab Coach — cập nhật ở CP2–CP3)*
- Hướng ĐÃ LOẠI + vì sao (giữ lại, đừng xoá):
  - **Khách hàng ảo tập phỏng vấn Mom Test:** Chỉ dùng 1–2 lần trong cả khoá (trước ngày phỏng vấn), trong khi nộp bài lab & đồ án diễn ra liên tục suốt 15 ngày + hackathon; khó chứng minh giá trị tiết kiệm lặp lại hàng tháng bằng bài toán soát bài nộp.
  - **Ghép nhóm / ghép mentor theo giờ rảnh:** Tần suất chỉ 1 lần đầu đợt, và việc khớp lịch rảnh/kỹ năng là bài toán ràng buộc dùng thuật toán/code thuần xử lý tốt hơn, không cần AI làm quyết định trung tâm.
- Số lần / tháng của từng kiểu người dùng (dùng cho persona ở §8): *(đang thu từ khảo sát & phỏng vấn — cập nhật ở CP2–CP3)*

## §3. Giải pháp tương tự *(guide 2.1)*
- [sản phẩm / tính năng gần giống]: một điều đáng học · một điều đáng né · mình khác gì

## §4. Thiết kế *(guide 2.2, 3.2)*
- **Lát cắt MỘT CÂU** (1 người dùng · 1 việc · 1 quyết định AI · 1 kết quả):
- Không làm (≥3 điều):
- **Sơ đồ** (ảnh / Mermaid / draw.io): [chèn ở đây]
- **Hình dạng:** [ ] workflow cố định · [ ] một agent · [ ] nhiều agent — 2 dòng lý do, và vì sao **không** chọn hình dạng phức tạp hơn:
- **AI dựa vào đâu** — mỗi công cụ (khớp `codebase/tools.py`):

  | Công cụ | Input | Output | Tác động ra ngoài? |
  |---|---|---|---|
  |  |  |  |  |

- **Mức tự động:** [ ] AI gợi ý, người quyết · [ ] AI tự làm khi chắc, chuyển người khi không · [ ] AI tự làm — lý do (sai thì ai chịu gì, sửa đắt hay rẻ):
- **Chỗ chặn rủi ro** (rủi ro lớn nhất của lát cắt bị chặn ở đâu, bằng gì):
- **Chỗ người duyệt** (việc AI không được tự làm):
- **Nguyên tắc thiết kế** (≥3, bắt buộc G10):

  | Nguyên tắc | Chỗ cụ thể trên sơ đồ / trong bản chạy thử |
  |---|---|
  | G10 — thu hẹp phạm vi khi không chắc |  |
  |  |  |
  |  |  |

- Phần nào còn giả (công cụ trả dữ liệu giả, model chế độ giả…) — ghi rõ, không giả làm thật:

## §5. Chỗ khó — 4 lớp + ≥6 kịch bản + 2 tấn công *(guide 2.3)*

| Kịch bản | Lớp (1–4) | Hành vi mong muốn (nói gì, hiện gì, cho làm gì tiếp) | Câu thử |
|---|---|---|---|
|  |  |  |  |
| *(tấn công)* |  |  |  |
| *(tấn công)* |  |  |  |

(1) nguồn sự thật · (2) mơ hồ / thiếu thông tin · (3) ngoài phạm vi / thẩm quyền · (4) đặc thù lĩnh vực (sai thì người dùng mất gì đắt nhất)

## §6. Bốn đường đi của trải nghiệm
- Mọi thứ suôn sẻ: · Không chắc (lớp 2): · Không có căn cứ (lớp 1): · Người dùng sửa:
- Bị đòi ngoài phạm vi (lớp 3): · Trường hợp đặc thù lĩnh vực (lớp 4):

## §7. Đánh giá & chuẩn "đạt" *(guide 2.4, 4.1)*
- Data card: `data/DATA_CARD.md` · bộ câu thử: `eval/benchmark.csv` — __ câu (thuong __ · kho __ · tu_choi __) · metric: `eval/metric_spec.yaml` (__ metric)
- **Chuẩn "đạt"** (chốt **trước 19:30 Thứ Sáu 27/11**, giữ nguyên đến 23:59 Thứ Bảy 28/11): "Đạt khi ≥ __% câu qua, và __"
- Kết quả: lượt 1 __/__ (__%) · lượt 2 __/__ (__%) — run ID: __ / __ → chi tiết `eval/report.md`, hồ sơ `eval/README.md`

## §8. Chi phí khi dùng thật *(guide 4.2)*
- Persona + giá: `cost/personas.yaml` · lượt mô phỏng: `cost/simulate-__.csv` (__ phiên)
- Chi phí / task thành công: __ (model __) · __ (model __)
- Chi phí / tháng ở quy mô thật: thấp __ · cơ sở __ · cao __ → chi tiết `cost/cost-estimate.md`
- So với impact / người / tháng (§2): đáng làm không, vì sao:

## §9. Rủi ro & an toàn
- Dữ liệu: đã ẩn danh gì, không thu gì, không đưa gì vào model gói miễn phí:
- AI **không được** làm gì kể cả khi người dùng yêu cầu:
- Ai có thể bị hại nếu AI sai, và nhóm chặn thế nào:

## §10. Phân công & changelog
- Phân công có tên (theo chặng, chia cặp — guide "Cách chia việc"): __
- Dùng AI vào việc gì (2–3 dòng; chi tiết `docs/ai-usage.md`):
- Nhật ký thay đổi — **mọi thay đổi sau CP2 19:30 Thứ Sáu 27/11 phải có dòng ở đây**:

**CP2 → CP4** (vd thu hẹp lát cắt, hỏi thêm người dùng, lần cải tiến trước lượt 2)

| Thời điểm | Đổi gì | Vì sao (trỏ về câu thử / lỗi / bằng chứng nào) |
|---|---|---|
|  |  |  |

**Sau CP4 (đến 23:59 Thứ Bảy 28/11)** (sửa theo góp ý — không sửa chuẩn "đạt", câu thử, số bằng chứng, kết quả các lượt đã chạy)

| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
|  |  |  |
