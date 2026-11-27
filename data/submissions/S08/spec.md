# Hồ sơ sản phẩm — Nhóm NhomMau08

Lĩnh vực: Track A (A1)

## Nỗi đau & Bằng chứng thực địa
Khảo sát n=22 ngoài nhóm và phỏng vấn P1-P3 ghi nhận 14/22 (64%) học viên khảo sát mất 12 phút/lần khi tìm lại đoạn video.

## Lựa chọn hướng & Tác động tháng
So sánh 3 phương án: (1) Trợ giảng trích mã đoạn [Chọn]; (2) Bot nhắc lịch [Loại]; (3) Tóm tắt slide [Loại].
Ước tính tác động: 400 học viên × 6 lần × 12 phút = 28.800 phút/tháng (nguồn: khảo sát n=22).

## Kiến trúc hệ thống & Giới hạn
Lát cắt: Một học viên L3 · hỏi khái niệm bài học · hệ thống tra đoạn và trích mã đoạn · học viên tự kiểm chứng.
Phạm vi không làm: Không giải hộ lab, không tự bịa ngoài bài, không chấm điểm cuối.
Kiến trúc Workflow 2 bước — không dùng multi-agent để tránh tốn token và sai lệch vai.
Nguyên tắc áp dụng: G10 (hỏi lại khi thiếu thông tin), G1 (nêu rõ giới hạn), G11 (trích nguồn kiểm được).

## Tiêu chí nghiệm thu (chốt CP2)
Đạt khi >= 80% câu thử qua và 100% câu ngoài bài từ chối đúng.
