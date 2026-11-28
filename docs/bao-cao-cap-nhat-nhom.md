# Báo cáo cập nhật phát hành & bàn giao nhóm — RepoKSV (`develop-tuan`)

> **Ngày cập nhật:** 28/11/2026  
> **Nhánh triển khai:** `develop-tuan` @ `7695a343c2fab5f87f1e18a5ea657653ddac2d67` (`7695a34`)  
> **URL Production:** <https://repoksv.tuanpq.com>

---

## Phần 1 — Tổng quan phát hành & Trạng thái Live

### 1.1. Kiến trúc & Thông tin triển khai

| Thành phần | Hạ tầng / Tham chiếu | Chi tiết đã xác minh |
|---|---|---|
| **Frontend (Production)** | Vercel (`tun-p-trick/repoksv`) | URL chính: `https://repoksv.tuanpq.com` · Deployment ID: `dpl_4UwPvnSUWXmdckPh4tDyZU7C9mh5` (`https://repoksv-48w6jaftv-tun-p-trick.vercel.app`) · `web/vercel.json` rewrite `/api/*`, `/auth/*`, `/health` → `https://api-repoksv.tuanpq.com` |
| **Backend (Production)** | AWS EC2 `i-05273e37e98d10f66` (`ap-southeast-2`) | Thư mục `/opt/repoksv` · Container `repoksv-app` (`8000/tcp`, trạng thái `healthy`) kết nối qua `repoksv-tunnel` (`cloudflare/cloudflared:latest`) |
| **Git Branch & Commit** | `origin/develop-tuan` | Commit đã deploy: `7695a343c2fab5f87f1e18a5ea657653ddac2d67` (`7695a34`) · Chuỗi commit liền trước: `eb1d3bd`, `bc24bf0`, `4a03da5` |
| **AWS SSM Command IDs** | EC2 `i-05273e37e98d10f66` | Deploy build & recreate: `87663be6-cfaf-4249-85fa-ab0dab5c0864` (`HEAD` tại `7695a34`, container `healthy`) · Verify container status: `62a379ec-d800-4ba1-b0f7-13d60724cb88` (`Status: Success`, exit `0`) |

### 1.2. Bảng trạng thái xác minh Live Production (`https://repoksv.tuanpq.com`)

| Kiểm tra | Kết quả | Chi tiết thực đo |
|---|---|---|
| `GET /health` | `200 OK` | `{"status":"ok","oauth_configured":true,"model_provider":"deepseek","allow_guest_demo":false}` |
| `GET /favicon.svg` | `200 OK` | Chứa SVG logo chữ `K` màu `#1B365D` & tia quét `#9B2226` |
| `POST /api/viva/chat/stream` | `401` | Trả `401 {"detail":"Vui lòng đăng nhập Google để tiếp tục."}` (đúng route, không còn `404`, khóa auth đúng khi `allow_guest_demo=false`) |
| `GET /api/export/md?scope=all` | `401` | Bảo vệ xác thực chuẩn khi chưa đăng nhập |
| `py deploy/smoke_check.py --base-url https://repoksv.tuanpq.com --strict-headers` | **4/4 PASS** | `Health` OK · `Security Headers` (CSP, `nosniff`, `X-Frame-Options`, HSTS) OK · `URL-Hack Route` (`/phamtuan2xx3-alt/K5-Day15-L3B-Free2Play` → `200`) · `SSRF Guard` (`3/3` payload bị chặn) |
| Playwright Live (`https://repoksv.tuanpq.com/`) | `200 OK` | Giao diện mới đã live (`RepoKSV` wordmark sạch, bỏ `[KSV]` badge), `0` lỗi page/CSP (chỉ có 401 dự kiến từ `/api/me` do `allow_guest_demo=false`) |

---

## Phần 2 — Chi tiết thay đổi & tính năng đã hoàn thiện

### 2.1. Backend (`codebase/ai.py`, `codebase/agent.py`, `codebase/db.py`, `codebase/exporters.py`, `codebase/server.py`)

- **SSE Streaming toàn trình (`eb1d3bd`, `7695a34`):**
  - `codebase/server.py`: bổ sung `POST /api/scan/stream` (`L1108`), `POST /api/viva/ask/stream`, `POST /api/viva/defense/stream`, `POST /api/viva/coach/stream` và `POST /api/viva/chat/stream` (`L1871`), truyền tiến độ từng pha và stream nội dung reasoning/markdown theo thời gian thực từ DeepSeek/OpenAI (`codebase/ai.py`).
- **Dynamic Rubric & GitHub Live Guard (`bc24bf0`, `7695a34`):**
  - `codebase/agent.py`: `_run_audit_pipeline` (`L1266`) đọc rubric động (`RUBRIC.md`/`README.md`/`TEAM.md`) từ repo đang kiểm toán kết hợp bộ luật cứng phổ quát (`PENALTY-KEY`, `GIT-FORK-PR`, `PENALTY-STANDARD`, `NO-AUTO-GRADE`) + nguyên tắc HAX G10; bổ sung `_format_live_checks_note` (`L299`) vào ghi chú trạng thái GitHub audit.
- **Hội thoại Vấn đáp Bloom L0–L6 (`7695a34`):**
  - `codebase/server.py`: bổ sung `POST /api/viva/chat` (`L1845`) và `POST /api/viva/chat/stream` (`L1871`) hỗ trợ các chế độ `start` / `next` / `answer` / `tutor` — hỏi từng câu ngắn bám repo, chấm mức thông hiểu Bloom L0–L6 và gia sư nâng +1 bậc, chống prompt injection và ký xác thực `viva_meta_token` bằng HMAC-SHA256 (`typ="viva_meta"`).
- **Hệ thống kiến thức đa repo & Export All (`7695a34`):**
  - `codebase/db.py`: bổ sung trường `source_repo` & `source_scan_id` trong bảng `bloom_profiles` và hàm `list_all_bloom_concepts` (`L952`).
  - `codebase/server.py` & `codebase/exporters.py`: `GET /api/bloom/me` trả kèm danh sách `repos` tổng hợp từ `list_all_bloom_concepts`; `GET /api/export/{target_key}` (`L2061`) hỗ trợ `?scope=all` cho cả 4 định dạng (`anki` `.tsv` chống DDE formula injection, `md`, `etude` `.pack.json` chuẩn `"etude": "pack/1"`, `json`).

### 2.2. Frontend (`web/src/`, `web/public/`, `web/dist/`)

- **Kiến trúc 3 tab Operate-mode Segmented Control (`web/src/App.tsx`, `web/src/styles.css`):**
  - 3 tab chính `Soi Repo`, `Vấn đáp`, `Hệ thống kiến thức` đặt trong thanh segmented rail đồng trục `max-w-[1040px]`, giữ nguyên phím mũi tên `ArrowRight` / `ArrowLeft`, `aria-controls`, `aria-selected`, và exact accessible names.
- **Tab 1 — `Soi Repo` (`web/src/components/AuditPanel.tsx`, `web/src/utils/auditSections.ts`):**
  - Phân tách kết quả audit thành 4 sub-tab: `(1) Lỗi cứng & An toàn`, `(2) Đối chiếu & Lập luận`, `(3) Đạt / Chưa kiểm (G10)`, `Xem toàn bộ`.
  - Badge đếm `safetyCount` giữ tương phản rõ trên nền nút active; bỏ viền `border-l-4` trên thẻ lỗi cứng; bổ sung CTA chuyển sang Vấn đáp kèm câu gợi ý; click `.cite-chip` mở `<dialog closedby="any">` xem đúng dòng mã nguồn được tô sáng.
- **Tab 2 — `Vấn đáp` (`web/src/components/VivaStudyPanel.tsx`):**
  - Giao diện Operate-mode căn trái đồng trục `1040px` (loại bỏ hero căn giữa, bỏ kicker/eyebrow ALL-CAPS thừa).
  - Header gồm dropdown chọn thành viên `#viva-member-select` (khi repo nhóm) và nút `Bắt đầu kiểm tra kiến thức` / `Câu hỏi mới` / `Làm mới chat`, khối `Câu hỏi gợi ý từ lần soi repo`, khung chat giới hạn dòng đọc `max-w-[74ch]` và composer `#viva-answer-box`.
- **Tab 3 — `Hệ thống kiến thức` (`web/src/components/KnowledgeHubPanel.tsx`):**
  - Gộp toàn bộ khái niệm Bloom của mọi repo đã quét, lọc theo mức Bloom & repo nguồn, tích hợp xem trước & tải 4 định dạng Anki/Markdown/Etude/JSON.
  - Đồng nhất 100% kiểu hiển thị `.cite-chip` giữa mọi repo (0 CSS drift) và click trích dẫn mở đúng `source_scan_id` của thẻ tương ứng.
- **Shell, Thương hiệu & Responsive (`web/src/components/ScanSidebar.tsx`, `web/src/components/TopBar.tsx`, `web/public/favicon.svg`, `web/public/logo.svg`):**
  - Desktop split-pane (`lg:h-screen lg:overflow-hidden` + `#content-scroller` cuộn độc lập), thu/mở sidebar mượt không giật khi cuộn.
  - Đồng bộ favicon & logo vector chữ `K` `#1B365D`/`#9B2226` với `repoksv-logo-120.png`, wordmark `RepoKSV` dùng 1 font sans-serif (bỏ badge mono `[KSV]`), `.session-btn` giữ border `1px` đồng đều (`0px` dịch ngang khi đổi repo active), hỗ trợ Light/Dark và Mobile `390x844` không tràn ngang.
  - **Bảo toàn CSP:** `web/index.html` giữ nguyên không sửa đổi để khớp hash `sha256-qKOSqlQG6FhYddlaB9jvO91UOnsHCJ/+bYkt2NOtm7o=` trong `web/vercel.json` và `deploy/Caddyfile`.

---

## Phần 3 — Bằng chứng kiểm thử đã chạy

1. **Bộ Unit, Integration, Pentest & E2E (`py -m unittest discover -s tests -v`):**
   - **Kết quả:** **68/68 PASS** (`Ran 68 tests in 33.622s — OK`).
   - Phạm vi: `test_phase1_core`, `test_phase2_github`, `test_phase3_viva`, `test_phase4_store_export`, `test_phase5_api`, `test_e2e_playwright`, `test_local_e2e_flows` (14 luồng trên Uvicorn local + Playwright), `test_security_pentest_local` (12 nhóm tấn công SSRF, IDOR, token type confusion, CSRF, path traversal, SQLi, XSS, prompt injection, rate-limit, body-cap 256 KB, TSV formula injection).
2. **Kiểm tra khung BTC (`py run.py check`):**
   - **Kết quả:** **PASS** — `30` câu thử (`S01–S30`: `thuong 13 · kho 12 · tu_choi 5`, `16/30` từ người dùng / data thật), `4` metric trong `eval/metric_spec.yaml`, `4` thành viên trong `TEAMS.md`, `0` vấn đề.
3. **Playwright Audit Local (`http://127.0.0.1:8081`):**
   - Đồng trục 3 tab (`tab1Left = tab2Left = tab3Left = 320px`, `tab2Width = 1040px`), `dx = 0` trên mọi `.session-btn` khi đổi repo, `tab3_styles_equal: true` (`11` `.cite-chip`), `window.scrollY === 0` khi cuộn `#content-scroller`, Mobile `390x844` cả 3 tab Light & Dark đạt `scrollWidth = 380 <= 390`, `0` console/page/HTTP errors, `0` emoji/decorative arrows.
4. **Production Live Smoke Check & Playwright (`https://repoksv.tuanpq.com`):**
   - `py deploy/smoke_check.py --base-url https://repoksv.tuanpq.com --strict-headers`: **4/4 PASS**.
   - Playwright trực tiếp trên `https://repoksv.tuanpq.com`: `200 OK`, `0` lỗi page/CSP.

---

## Phần 4 — Hướng dẫn cho thành viên nhóm (Cập nhật, Chạy Local & Review PR)

### 4.1. Kéo code mới nhất về máy

```bash
git fetch origin
git checkout develop-tuan
git pull origin develop-tuan
```

### 4.2. Chạy kiểm thử CLI & bộ test

```bash
py run.py check
py run.py
py -m unittest discover -s tests -v
```

### 4.3. Chạy bản Web giao diện đầy đủ ở chế độ Khách Demo (Local)

- **Windows PowerShell:**

```powershell
$env:ALLOW_GUEST_DEMO = "true"
$env:LOCAL_DEMO_ANON_ID = "localdemo"
$env:SESSION_SECRET = "dev-local-session-secret-change-me"
py -m uvicorn codebase.server:app --host 127.0.0.1 --port 8081
```

- **macOS / Linux:**

```bash
ALLOW_GUEST_DEMO=true \
LOCAL_DEMO_ANON_ID=localdemo \
SESSION_SECRET=dev-local-session-secret-change-me \
python3 -m uvicorn codebase.server:app --host 127.0.0.1 --port 8081
```

Mở trình duyệt tại <http://127.0.0.1:8081>.

### 4.4. Build lại Frontend (`web/`)

```powershell
# Windows (khi dùng Node v24 qua nvm nếu chưa có trong PATH mặc định)
$env:PATH = "C:\Users\phamt\AppData\Local\nvm\v24.22.3;" + $env:PATH
cd web
npm ci
npx tsc --noEmit
npm run build
```

### 4.5. Quy ước bắt buộc & Checklist Review PR trước khi merge `develop-tuan` → `main`

- **Không sửa file khung BTC & chuẩn chốt CP2:** giữ nguyên `run.py`, `codebase/tracing.py`, `eval/run_eval.py`, `cost/simulate.py`, `spec.md` §7, `eval/metric_spec.yaml`, `eval/benchmark.csv`.
- **Không commit file nhạy cảm / file tạm:** tuyệt đối không stage `.env`, `.study_logs/`, `eval/run-2.csv`, `traces/run-2.jsonl`, `.worktrees/`, hay ảnh `.png` debug.
- **Bảo toàn CSP hash:** không sửa inline `<script>` trong `web/index.html` nếu chưa cập nhật đồng thời hash SHA-256 trong `web/vercel.json` và `deploy/Caddyfile`.
- **Cổng kiểm bắt buộc trước khi tạo PR / merge:** `py run.py check` (0 lỗi), `py -m unittest discover -s tests -v` (100% PASS), và `git diff` kiểm sạch phạm vi.

---

## Phần 5 — Tham chiếu triển khai Production (AWS EC2 + Vercel)

### 5.1. Deploy Backend lên AWS EC2 (`i-05273e37e98d10f66`, `ap-southeast-2`)

```bash
cd /opt/repoksv
git fetch origin
git reset --hard origin/develop-tuan
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile tunnel up -d --build
docker ps --filter name=repoksv
```

### 5.2. Deploy Frontend lên Vercel & Kiểm chứng sau Deploy

```powershell
cd web
vercel deploy --prod --yes
cd ..
py deploy/smoke_check.py --base-url https://repoksv.tuanpq.com --strict-headers
```
