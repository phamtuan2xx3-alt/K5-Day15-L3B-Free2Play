# Tóm tắt mô phỏng simulate-1@20261128-144417

Do `python run.py simulate` sinh ra — không sửa tay. Chép bảng sang `cost/cost-estimate.md`.

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên | Gọi công cụ / phiên |
|---|---:|---:|---:|---:|---:|---:|
| nop_it | 8 | 1 | 3905 | 1856 | 0.8 | 7.4 |
| nop_vua | 13 | 2 | 9353 | 4079 | 1.8 | 17.6 |
| nop_nhieu | 29 | 2 | 10195 | 4556 | 1.9 | 19.1 |

Tỉ lệ đạt dùng để tính: 29/30 (97%) — lượt run-2@20261128-110603

- Tỉ lệ đạt lấy từ lượt nhóm chọn: eval/run-2.csv (--rate-from).

| Model (giá) | Chi phí / phiên | Chi phí / task thành công | Chi phí / câu hỏi đạt | Chi phí / tháng — thấp (300 người) | Chi phí / tháng — cơ sở (700 người) | Chi phí / tháng — cao (1.000 người) | Chi phí / người / tháng (cơ sở) |
|---|---:|---:|---:|---:|---:|---:|---:|
| deepseek-flash (vào 0.3 · ra 1.2 $/1M) | $0.0075 | $0.0077 | $0.0042 | $53.70 | $125.29 | $178.99 | $0.1790 |
| gpt-6.2-sol (vào 2.0 · ra 10.0 $/1M) | $0.0579 | $0.0599 | $0.0326 | $415.33 | $969.09 | $1,384.42 | $1.38 |

- Chi phí / task thành công = chi phí / phiên ÷ tỉ lệ đạt. Chi phí / câu hỏi đạt = chi phí / phiên ÷ số lượt hỏi trung bình mỗi phiên (1.8) ÷ tỉ lệ đạt — tỉ lệ đạt đo theo từng câu thử.
- Token đo trên model: chib/deepseek-v4.1-flash. Giá tính theo từng model trong bảng — model khác bộ tách token thì số token thật có thể lệch; ghi rõ "đo trên model X, tính giá model Y" trong cost/cost-estimate.md.
- Phiên lỗi (không tính vào trung bình): 0/50.
