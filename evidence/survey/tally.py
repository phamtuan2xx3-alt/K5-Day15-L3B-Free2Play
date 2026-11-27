"""Đếm kết quả khảo sát — chạy lại được: python evidence/survey/tally.py

Đầu vào: evidence/survey/results.csv (đã ẩn danh: bỏ dấu thời gian, bỏ cột liên hệ câu 8 → chỉ còn Co/Khong).
Mẫu số: học viên đã nộp ≥1 lần trong 14 ngày (bỏ người chọn "0 lần — chưa từng nộp": không đúng người dùng).

Luật đếm giả thuyết (evidence/hypothesis.md): "từng ít nhất 1 lần nộp sót mục / thiếu nguồn / sai tiêu chí
hoặc mất ≥15 phút dò rubric trong 14 ngày".
  - Bản HẸP (đúng chữ giả thuyết): câu 5 có "Nộp sót file…" / "Số liệu… lệch / thiếu nguồn…" / "Phải sửa gấp… trừ điểm",
    HOẶC câu 4 là "16–30 phút" / "Trên 30 phút".
  - Bản RỘNG: như trên + mọi sự cố khác ở câu 5 (PR nhầm repo gốc, lộ key, lúng túng khi bị hỏi vặn).
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8")

rows = list(csv.DictReader(open(os.path.join(HERE, "results.csv"), encoding="utf-8")))
users = [r for r in rows if not r["so_lan_nop_14_ngay"].startswith("0 lần")]
n = len(users)

OPT = {
    "sot_file": "Nộp sót file",
    "lech_nguon": "Số liệu hoặc khẳng định",
    "pr_nham": "Fork bài từ khoá về",
    "lo_key": "Suýt hoặc lỡ đưa thông tin nhạy cảm",
    "hoi_van": "Khi bị hỏi vặn",
    "sua_gap": "Phải sửa gấp",
    "chua_gap": "Chưa gặp lỗi nào",
}
CACH = {
    "doc_mat": "Tự đọc lướt",
    "script": "Chạy lệnh hoặc script",
    "ai_ngoai": "Dán một phần bài vào công cụ AI",
    "doc_cheo": "Nhờ bạn cùng nhóm",
    "nop_thang": "Nộp thẳng vì sát giờ",
}
LONG = ("16–30 phút", "Trên 30 phút")


def has(r, col, key):
    return key in r[col]


def pct(x, d=None):
    d = n if d is None else d
    return "%d/%d (%.0f%%)" % (x, d, 100.0 * x / d) if d else "0/0"


def count(pred, pool=None):
    return sum(1 for r in (users if pool is None else pool) if pred(r))


print("Tổng phiếu học viên: %d · bỏ %d người chưa nộp lần nào · n = %d" % (len(rows), len(rows) - n, n))
print("Lớp:", ", ".join("%s %d" % (k, count(lambda r, k=k: r["vai_tro"].endswith(k))) for k in ("L3A", "L3B")))

print("\nCâu 2 — số lần nộp 14 ngày:")
for v in ("1–3 lần", "4–8 lần", "9–12 lần", "Trên 12 lần", "Không nhớ"):
    print("  %-12s %s" % (v, pct(count(lambda r, v=v: r["so_lan_nop_14_ngay"] == v))))

print("\nCâu 3 — cách kiểm tra (chọn nhiều):")
for k, key in CACH.items():
    print("  %-10s %s" % (k, pct(count(lambda r, key=key: has(r, "cach_kiem_tra", key)))))

print("\nCâu 4 — thời gian tự rà lần gần nhất:")
for v in ("Dưới 5 phút", "5–15 phút", "16–30 phút", "Trên 30 phút"):
    print("  %-12s %s" % (v, pct(count(lambda r, v=v: r["thoi_gian_ra"] == v))))

print("\nCâu 5 — sự cố đã gặp 14 ngày (chọn nhiều):")
for k, key in OPT.items():
    print("  %-10s %s" % (k, pct(count(lambda r, key=key: has(r, "su_co_da_gap", key)))))

print("\nCâu 6 — số lần phát hiện lỗi sát giờ / sau nộp:")
for v in ("0 lần", "1 lần", "2–3 lần", "4 lần trở lên", "Không nhớ"):
    print("  %-14s %s" % (v, pct(count(lambda r, v=v: r["so_lan_phat_hien_loi"] == v))))
print("  ≥1 lần        ", pct(count(lambda r: r["so_lan_phat_hien_loi"] in ("1 lần", "2–3 lần", "4 lần trở lên"))))

narrow = lambda r: (any(has(r, "su_co_da_gap", OPT[k]) for k in ("sot_file", "lech_nguon", "sua_gap"))
                    or r["thoi_gian_ra"] in LONG)
broad = lambda r: narrow(r) or any(has(r, "su_co_da_gap", OPT[k]) for k in ("pr_nham", "lo_key", "hoi_van"))
print("\nGiả thuyết (ngưỡng ≥60%):")
print("  Bản hẹp :", pct(count(narrow)))
print("  Bản rộng:", pct(count(broad)))

ai = [r for r in users if has(r, "cach_kiem_tra", CACH["ai_ngoai"])]
script = [r for r in users if has(r, "cach_kiem_tra", CACH["script"])]
any_err = lambda r: not has(r, "su_co_da_gap", OPT["chua_gap"]) and r["su_co_da_gap"].strip()
print("\nKiểm chéo — đã có công cụ mà vẫn gặp sự cố ở câu 5:")
print("  Có dán AI ngoài       :", pct(count(any_err, ai), len(ai)))
print("  Có chạy script check  :", pct(count(any_err, script), len(script)))
print("  Có dán AI ngoài, vẫn PR nhầm repo gốc:", pct(count(lambda r: has(r, "su_co_da_gap", OPT["pr_nham"]), ai), len(ai)))
print("  Có chạy script, vẫn PR nhầm repo gốc :", pct(count(lambda r: has(r, "su_co_da_gap", OPT["pr_nham"]), script), len(script)))

print("\nCâu 8 — đồng ý hỏi thêm / thử demo:", pct(count(lambda r: r["san_long_phong_van"] == "Co")))
