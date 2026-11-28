# Implementation Plan 6 Phase — RepoKSV (Hướng 1 + Hướng 2)

> **Trạng thái:** KẾ HOẠCH TRIỂN KHAI CHI TIẾT (CHƯA CODE) · **Nhánh:** `develop-tuan`  
> **Bám sát:** [docs/tech-spec-huong-1-2.md](tech-spec-huong-1-2.md) và [docs/spec-huong-1-2.md](spec-huong-1-2.md).  
> **Quy tắc chung:** Hoàn thành Phase nào kiểm chứng sạch Phase đó (`unittest` + `py run.py check`) rồi mới sang Phase tiếp theo; tuyệt đối không sửa 4 file khung BTC (`run.py`, `codebase/tracing.py`, `eval/run_eval.py`, `cost/simulate.py`), `spec.md` §7 và `eval/metric_spec.yaml`.

---

## Phase 1 — Nền Core Python & Cổng CP3 (`tools.py`, `agent.py`)

- **Mục tiêu:** Củng cố lớp lõi 100% Python stdlib, sửa triệt để ca `S25`, hỗ trợ trích dẫn đường dẫn có `/`, và thêm công cụ nhận diện Team vs Cá nhân — giữ 25/25 câu `eval` offline chạy ổn định.
- **File chạm:**
  - `codebase/tools.py`
  - `codebase/agent.py`
  - `tests/test_phase1_core.py` *(mới)*
- **Đầu việc chi tiết:**
  - [ ] Tách bộ quét `TEAMS.md`, `canvas.md`, `benchmark.csv`, `metric_spec.yaml`, secrets/injection trong `tools.py` thành hàm nhận list dòng dùng chung (`scan_in_memory_submission`) để cả chế độ file đĩa và GitHub RAM chạy 1 luật duy nhất.
  - [ ] Mở rộng `scan_hard_rules()` đọc thêm các cờ mô phỏng `repo_private`, `post_cp2_tamper`, `leaked_files` trong `meta.json` (tương thích 100% `S01..S25`).
  - [ ] Nâng cấp regex `verify_audit_output()` nhận diện chính xác đường dẫn có dấu `/` (`evidence/summary.md:L12`, `eval/benchmark.csv:L05`), vẫn giữ chặn `/100` (`NO-AUTO-GRADE`) và không chặn nhầm `Level X/6`.
  - [ ] Viết `@tool extract_project_identity(files_content, github_owner)` tự phân biệt `team` (`>=2` thành viên `TEAMS.md`) vs `personal` (`0–1` người).
  - [ ] Sửa `_classify_out_of_scope()` trong `agent.py`: tách `hard_refusals` (chấm `/100`, bịa phỏng vấn, đổi chuẩn CP2 → dừng ngay như `S15`) và `action_refusals` (*tự động sửa / commit / push* → in khung từ chối **và vẫn chạy quét 3 bước báo lỗi thật** để qua ngọt `S25`).
  - [ ] Cập nhật prompt mặc định `SYSTEM` để 2 câu hỏi vặn ở mục `(4)` gọi đích danh tên thành viên trong `TEAMS.md`.
- **Kiểm chứng bắt buộc:**
  - `py -m unittest tests/test_phase1_core.py -v` (cover `S01`, `S04`, `S06`, `S08`, `S09`, `S10`, `S14`, `S15`, `S21`, `S23`, `S24`, `S25`, path `/`, `extract_project_identity`).
  - `py run.py check; py run.py eval --fake` đều pass 100%.

---

## Phase 2 — Hướng 1: GitHub Live Guard (`github_guard.py`)

- **Mục tiêu:** Cài đặt bộ soi trạng thái thật trên GitHub (chỉ đọc trong RAM, chống SSRF, fallback thông minh khi rate-limit/Private).
- **File tạo / chạm:**
  - `codebase/github_guard.py` *(mới)*
  - `codebase/tools.py` *(thêm `@tool inspect_github_repo`)*
  - `codebase/agent.py` *(thêm nhánh `AUDIT_GITHUB` vào `answer()`)*
  - `tests/test_phase2_github.py` *(mới)*
- **Đầu việc chi tiết:**
  - [ ] Viết `parse_github_target()` nhận URL GitHub, `mydomain.com/owner/repo`, `/https://github.com/owner/repo`, `/owner/repo`; kiểm chặt regex `^[A-Za-z0-9_.-]{1,100}$`, chặn `..`, SSRF IP nội bộ (`169.254.169.254`, `127.0.0.1`), và route nội bộ.
  - [ ] Viết `fetch_github_repo_snapshot()` với `User-Agent: RepoKSV-Auditor/1.0`, hỗ trợ `GITHUB_TOKEN` từ `.env`, timeout 12s, cache TTL 5 phút trong RAM theo `(owner, repo)`.
  - [ ] Cài đủ 4 lớp kiểm: `PUBLIC-ACCESS` (`404/403`), `GIT-FORK-PR` (`pulls?state=open` trên `parent`), `PENALTY-STANDARD` (`commits?since=2026-11-27T12:30:00Z` kiểm `patch` phân biệt sửa `§7` vs thêm câu CP3), `PENALTY-KEY` (cây file `.env/*.pem/id_rsa/credentials*` + tải file nộp qua `raw.githubusercontent.com`, giới hạn `200KB/file`).
  - [ ] Cài cơ chế fallback 2 tầng khi `403/429`: kéo file qua `raw.githubusercontent.com` + trả G10 rõ cho các check cần API.
  - [ ] Nối `AUDIT_GITHUB` vào `agent.answer()` (tuyệt đối chỉ kích hoạt khi input có link GitHub, `S01..S25` vẫn 100% offline).
- **Kiểm chứng bắt buộc:**
  - `py -m unittest tests/test_phase2_github.py -v` (mock đủ 8 ca: repo sạch, Private `404`, `403` rate-limit + fallback `raw`, `429 Retry-After`, Fork + open PR upstream, Commit sửa `metric_spec.yaml` sau CP2, Commit thêm câu `benchmark.csv` hợp lệ, SSRF URL độc hại).
  - 1 lệnh smoke test live trên repo công khai thật của nhóm (`phamtuan2xx3-alt/K5-Day15-L3B-Free2Play`).

---

## Phase 3 — Hướng 2: Bộ 3 Prompt Bloom L0–L6 & Hồ sơ Thông hiểu (`agent.py`)

- **Mục tiêu:** Biến phần hỏi vặn thành quy trình đánh giá thông hiểu cá nhân hoá theo thang Bloom 6 bậc (`L0–L6`) nhưng giữ nguyên `answer(text)` stateless, 1 `@model_call` và luật `NO-AUTO-GRADE`.
- **File chạm / tạo:**
  - `codebase/agent.py`
  - `tests/test_phase3_viva.py` *(mới)*
- **Đầu việc chi tiết:**
  - [ ] Viết parser cú pháp đầu vào cho 3 chế độ: `VIVA_ASK`, `VIVA_DEFENSE`, `VIVA_COACH` (kèm `TARGET`, `QUESTION`, `ANSWER`, `MEMORY`).
  - [ ] Gắn kiểm tra danh tính từ `extract_project_identity()`: repo nhóm thiếu tên hoặc sai tên không có trong `TEAMS.md` → trả ngay HAX G10 liệt kê lại danh sách thành viên thật; repo cá nhân → tự chọn `default_user`.
  - [ ] Viết `SYSTEM_VIVA_ASK`, `SYSTEM_VIVA_DEFENSE`, `SYSTEM_VIVA_COACH` tham khảo cấu trúc từ `_etude`: 3 trục câu hỏi (`noi_dung` / `khai_niem` / `phan_bien`), chống học vẹt, không khen xu nịnh, che đáp án mẫu trong `[VIVA_META_JSON]`, trả 4 mục + `[BLOOM_LOG_DRAFT_JSON]` chờ user xác nhận lưu.
  - [ ] Bọc cả `ANSWER:` và `MEMORY:` trong `<submission_data_untrusted>`; quét injection ngay trên `ANSWER:`.
  - [ ] Viết chế độ `MODEL_PROVIDER=fake` trả JSON hợp lệ cho `VIVA_ASK` / `VIVA_DEFENSE` / `VIVA_COACH` để mọi test và demo offline đều chạy trọn luồng.
- **Kiểm chứng bắt buộc:**
  - `py -m unittest tests/test_phase3_viva.py -v` (test team vs personal, sai tên G10, trả lời khớp căn cứ, lệch số liệu L0, học vẹt L1, injection trong `ANSWER:`, đòi chấm `/100`, tư vấn nâng bậc `VIVA_COACH`).
  - `py run.py eval --fake` vẫn pass 100%.

---

## Phase 4 — Kho lưu SQLite WAL & 4 Bộ Export (`db.py`, `exporters.py`)

- **Mục tiêu:** Xây tầng lưu trữ bền vững, an toàn concurrency bằng SQLite WAL cho `Scan Session` + `User Bloom Memory` + cache GitHub + rate-limit, và 4 bộ Export 0 thư viện ngoài.
- **File tạo:**
  - `.gitignore` *(chỉ thêm `.study_logs/`)*
  - `codebase/db.py` *(mới)*
  - `codebase/exporters.py` *(mới)*
  - `tests/test_phase4_store_export.py` *(mới)*
- **Đầu việc chi tiết:**
  - [ ] Cài đặt `db.py` với `PRAGMA journal_mode=WAL; busy_timeout=5000; foreign_keys=ON;` và 6 bảng (`users`, `scan_sessions`, `viva_entries`, `bloom_profiles`, `github_cache`, `rate_limit_events`).
  - [ ] Viết đầy đủ các hàm: `upsert_user`, `create_scan_session`, `list_scan_sessions`, `get_scan_session`, `compare_with_previous_scan`, `save_viva_entry`, `confirm_bloom_draft` (chỉ gộp khi user xác nhận, tự chuyển `misconceptions` đã gỡ sang `resolved_misconceptions`), `update_card_status`, `get_user_bloom_profile`, `check_and_increment_rate_limit`.
  - [ ] Viết `exporters.py`:
    - `export_anki_tsv()` (`#separator:tab`, `#html:true`, `#tags column:3`, `Front\tBack\tTags`, thoát `\t`/`\n`)
    - `export_markdown_guide()` (`study-guide-<user>.md` xếp nhóm `L0–L1` → `L2` → `L3+`)
    - `export_etude_pack_json()` (`"etude": "pack/1"`, `type: "free"`, Bloom `instructions`)
    - `export_session_json()` (toàn bộ `scan_session` + `viva_entries`)
- **Kiểm chứng bắt buộc:**
  - `py -m unittest tests/test_phase4_store_export.py -v` (dùng SQLite tạm trong `TemporaryDirectory()`, test hợp nhất Bloom từ `L0 -> L3`, kiểm định dạng cả 4 Export gồm parse JSON chuẩn `etude: pack/1` và đếm đúng 3 cột TSV không vỡ dòng, test 15 thread ghi/đọc đồng thời không lỗi `database is locked`).

---

## Phase 5 — FastAPI Backend + RepoKSV OAuth + React/Vite Static Web UI (`server.py`, `app.py`, `web/`)

- **Mục tiêu:** Dựng backend FastAPI bọc Core + Google OAuth `RepoKSV` + rate-limit, nối với giao diện React/Vite + TypeScript build tĩnh ra `web/dist/` (4 khu vực học trực tiếp trên web).
- **File tạo / chạm:**
  - `requirements.txt` *(ghi `fastapi`, `uvicorn[standard]`, `pydantic`)*
  - `codebase/server.py` *(mới — FastAPI app, OAuth PKCE, REST API, rate-limit, SPA routing URL-hack)*
  - `codebase/app.py` *(gọi uvicorn chạy `server:app` mặc định; giữ `--cli` cho dòng lệnh)*
  - `web/` *(đưa vỏ `RepoKSV` từ `develop-tuan-web-repoksv` sang React + Vite build `web/dist/`)*
  - `tests/test_phase5_api.py` *(mới)*
- **Đầu việc chi tiết:**
  - [ ] Nối Google OAuth PKCE (`GET /auth/google`, `/auth/google/callback`, `/auth/logout`) với cookie HMAC-SHA256 `__Host-repoksv_session` sang Python `server.py` + bảng `users` trong SQLite.
  - [ ] Cài đặt toàn bộ REST endpoints (`/api/me`, `/api/submissions`, `/api/scan`, `/api/sessions/*`, `/api/viva/*`, `/api/study/*`, `/api/profiles/*`, `/api/export/{fmt}`) kèm middleware rate-limit (`<= 5 quét/phút/IP`, `<= 30 LLM/user/ngày`) và tách ẩn `[VIVA_META_JSON]` ở server trước khi trả câu hỏi cho client.
  - [ ] Dựng React UI 4 khu vực trong `web/src/` theo `frontend-design` & `modern-web-guidance`:
    - Top Command Bar (`mydomain.com/<owner>/<repo>` URL-hack + chọn `S01..S25` + Google OAuth badge + 3-state Dark Mode toggle chống FOUC).
    - Sidebar Lịch sử Phiên quét + delta so với lần trước.
    - Tab 1: Soi Repo (4 thẻ GitHub + lỗi cứng + chip `file:Lxx` mở `<dialog closedby="any">` xem dòng nguồn).
    - Tab 2: Phỏng vấn, Tư vấn nâng bậc Bloom & Học ngay trên Web (chọn danh tính Team/Cá nhân, hồ sơ Bloom, nút *Hỏi vặn*, *Tư vấn +1 Bloom*, thẻ che đáp án, nút *Lưu vào hồ sơ*, *Thử lại*, *Lật xem giải thích*, *Chưa vững / Đã hiểu*).
    - Tab 3: Xem trước & Tải 4 định dạng Export.
  - [ ] Build tĩnh `npm run build` → `web/dist/` (FastAPI serve tĩnh khi chạy local qua `py run.py`).
- **Kiểm chứng bắt buộc:**
  - `py -m unittest tests/test_phase5_api.py -v` (dùng FastAPI `TestClient` kiểm toàn bộ endpoints, xác thực cookie HMAC, rate-limit `429`, URL-hack `/owner/repo`, ẩn `reference` khi `ask`, 4 định dạng Export).
  - Kiểm thử giao diện thực tế bằng `webapp-testing` (Playwright) / `chrome-devtools` trên `http://127.0.0.1:8000` (check 0 lỗi console, responsive mobile/desktop, XSS payload vô hiệu, modal `<dialog>` đóng được bằng backdrop/Esc).
  - Chạy rà soát bảo mật theo quy trình `security-audit`.

---

## Phase 6 — Đóng gói AWS VPS (2 vCPU / 4 GB) & Nghiệm thu BTC

- **Mục tiêu:** Đưa lên VPS chạy HTTPS ổn định qua `repoksv.tuanpq.com` và chạy sạch bộ kiểm chứng nộp bài CP3/CP4.
- **File tạo / chạm:**
  - `deploy/Caddyfile` *(mới)*
  - `deploy/repoksv.service` *(mới)*
  - `deploy/smoke_check.py` *(mới)*
  - `spec.md` *(chỉ ghi thêm dòng vào §10 changelog khi hoàn tất; giữ nguyên §7)*
- **Đầu việc chi tiết:**
  - [ ] Viết `deploy/Caddyfile` (HTTPS `repoksv.tuanpq.com`, headers CSP/HSTS/nosniff, static `web/dist/`, proxy `/api/*` & `/auth/*` về `127.0.0.1:8000`).
  - [ ] Viết `deploy/repoksv.service` (`systemd`, 2 Uvicorn workers, `EnvironmentFile=/opt/repoksv/.env`).
  - [ ] Viết `deploy/smoke_check.py` kiểm tự động sau deploy: `/health`, HTTPS, OAuth redirect, SSRF reject `169.254.169.254`, rate-limit `429`, URL-hack `/phamtuan2xx3-alt/K5-Day15-L3B-Free2Play`.
- **Kiểm chứng cuối cùng toàn dự án:**
  - `py run.py check` (0 vấn đề, 25/25 câu).
  - `py run.py eval --try` & `py run.py eval` (khi đã điền API key thật trong `.env`).
  - `py run.py simulate --try` & `py run.py simulate`.
  - Xác nhận `git status` không lộ `.env`, `.study_logs/`, `.gitnexus/`, và không đụng 4 file khung BTC hay `spec.md` §7.
