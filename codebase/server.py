"""FastAPI Backend cho RepoKSV (Hướng 1 + Hướng 2) — OAuth PKCE, Rate-Limit, REST API & Export."""
from __future__ import annotations

import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import OrderedDict
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

# Bảo đảm import đồng nhất dù chạy từ root (`codebase.server`) hay từ `codebase/` (`server`)
_CODEBASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_CODEBASE_DIR)
if _CODEBASE_DIR not in sys.path:
    sys.path.insert(0, _CODEBASE_DIR)

import agent  # noqa: E402
import ai  # noqa: E402
import db as db_mod  # noqa: E402
import exporters  # noqa: E402
import github_guard  # noqa: E402
import tools  # noqa: E402
import tracing  # noqa: E402

WEB_DIST_DIR = os.path.join(_ROOT_DIR, "web", "dist")
SUBMISSIONS_MANIFEST = os.path.join(_ROOT_DIR, "data", "submissions", "manifest.json")

SESSION_COOKIE_HTTPS = "__Host-repoksv_session"
SESSION_COOKIE_HTTP = "repoksv_session"
OAUTH_STATE_COOKIE = "repoksv_oauth"
ANON_COOKIE = "repoksv_anon"
SESSION_TTL_S = 7 * 24 * 3600
OAUTH_TTL_S = 600
SCAN_RATE_LIMIT = 5
SCAN_WINDOW_S = 60
LLM_DAILY_LIMIT = 30
LLM_WINDOW_S = 86400
MAX_RAM_SCANS = 40
MAX_BODY_BYTES = 262_144

logger = logging.getLogger("repoksv.server")
_SAFE_HOST_RE = re.compile(r"^[A-Za-z0-9.\[\]:-]{1,253}$")
_PROCESS_FALLBACK_SECRET = secrets.token_urlsafe(32)
_VIVA_META_TAG_RE = re.compile(r"\[VIVA_META_JSON\].*?\[/VIVA_META_JSON\]", re.DOTALL | re.IGNORECASE)
_BLOOM_DRAFT_TAG_RE = re.compile(
    r"\[BLOOM_LOG_DRAFT_JSON\].*?\[/BLOOM_LOG_DRAFT_JSON\]", re.DOTALL | re.IGNORECASE
)
_BLOOM_TITLES = {
    0: "L0 — Chưa nắm / Lệch căn cứ",
    1: "Remember",
    2: "Understand (Feynman)",
    3: "Apply",
    4: "Analyze (Trade-off)",
    5: "Evaluate (Bằng chứng)",
    6: "Create (Thiết kế hệ thống)",
}


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_session_secret() -> bytes:
    secret = (os.environ.get("SESSION_SECRET") or "").strip()
    if not secret:
        secret = _PROCESS_FALLBACK_SECRET
    return secret.encode("utf-8")


def _b64u_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64u_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def sign_token(
    payload: dict[str, Any],
    ttl_seconds: int = SESSION_TTL_S,
    typ: str = "generic",
) -> str:
    """Ký payload JSON bằng HMAC-SHA256 dạng base64url(payload).base64url(sig) kèm domain _typ."""
    data = dict(payload)
    data["_typ"] = typ
    data.setdefault("exp", int(time.time()) + ttl_seconds)
    raw_b64 = _b64u_encode(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(_get_session_secret(), raw_b64.encode("ascii"), hashlib.sha256).digest()
    return f"{raw_b64}.{_b64u_encode(sig)}"


def verify_token(token: str | None, expected_typ: str | None = None) -> dict[str, Any] | None:
    """Xác thực chữ ký HMAC-SHA256, miền token (_typ) và hạn dùng."""
    if not token or "." not in token:
        return None
    raw_b64, sig_b64 = token.split(".", 1)
    expected_sig = hmac.new(_get_session_secret(), raw_b64.encode("ascii"), hashlib.sha256).digest()
    try:
        actual_sig = _b64u_decode(sig_b64)
    except Exception:
        return None
    if not hmac.compare_digest(expected_sig, actual_sig):
        return None
    try:
        payload = json.loads(_b64u_decode(raw_b64).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    if expected_typ is not None and payload.get("_typ") != expected_typ:
        return None
    exp = payload.get("exp")
    if isinstance(exp, (int, float)) and time.time() > float(exp):
        return None
    return payload


def _is_trusted_proxy_peer(request: Request) -> bool:
    peer = (request.client.host if request.client else "").strip()
    if peer in {"127.0.0.1", "::1"}:
        return True
    raw_cidrs = (os.environ.get("TRUSTED_PROXY_CIDRS") or "").strip()
    if not raw_cidrs or not peer:
        return False
    try:
        peer_ip = ipaddress.ip_address(peer)
    except ValueError:
        return False
    for item in raw_cidrs.split(","):
        cidr = item.strip()
        if not cidr:
            continue
        try:
            if peer_ip in ipaddress.ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue
    return False


def _is_https_request(request: Request) -> bool:
    if _is_trusted_proxy_peer(request):
        xf_proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
        if xf_proto:
            return xf_proto == "https"
    return (request.url.scheme or "").lower() == "https"


def _trusted_request_host(request: Request) -> str:
    """Trích host hợp lệ, chỉ tin X-Forwarded-Host khi đi qua proxy loopback."""
    if _is_trusted_proxy_peer(request):
        xf_host = (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()
        if xf_host:
            if not _SAFE_HOST_RE.fullmatch(xf_host):
                raise HTTPException(status_code=400, detail="Host không hợp lệ.")
            return xf_host
    hdr_host = (request.headers.get("host") or "").strip()
    if hdr_host:
        if not _SAFE_HOST_RE.fullmatch(hdr_host):
            raise HTTPException(status_code=400, detail="Host không hợp lệ.")
        return hdr_host
    netloc = (request.url.netloc or "").strip()
    if not netloc or not _SAFE_HOST_RE.fullmatch(netloc):
        raise HTTPException(status_code=400, detail="Host không hợp lệ.")
    return netloc


def _session_cookie_name(request: Request) -> str:
    return SESSION_COOKIE_HTTPS if _is_https_request(request) else SESSION_COOKIE_HTTP


def _client_ip(request: Request) -> str:
    """Xác định IP client an toàn: chỉ tin X-Real-IP / hop cuối XFF khi đi qua proxy tin cậy."""
    peer = request.client.host if request.client else "127.0.0.1"
    if _is_trusted_proxy_peer(request):
        real_ip = (request.headers.get("x-real-ip") or "").strip()
        if real_ip:
            return real_ip
        xff = [p.strip() for p in (request.headers.get("x-forwarded-for") or "").split(",") if p.strip()]
        if xff:
            return xff[-1]
    return peer


def _oauth_configured() -> bool:
    return bool(
        (os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
        and (os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
    )


def _google_redirect_uri(request: Request) -> str:
    configured = (os.environ.get("GOOGLE_REDIRECT_URI") or "").strip()
    if configured:
        return configured
    scheme = "https" if _is_https_request(request) else request.url.scheme
    host = _trusted_request_host(request)
    return f"{scheme}://{host}/auth/google/callback"


def _exchange_google_code(
    *,
    code: str,
    code_verifier: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> dict[str, Any]:
    """Đổi authorization code lấy access_token + thông tin user Google."""
    body = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "RepoKSV-Auditor/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        token_data = json.loads(resp.read().decode("utf-8"))

    access_token = token_data.get("access_token")
    if not access_token:
        raise RuntimeError("Google OAuth không trả access_token.")

    info_req = urllib.request.Request(
        "https://openidconnect.googleapis.com/v1/userinfo",
        method="GET",
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "RepoKSV-Auditor/1.0",
        },
    )
    with urllib.request.urlopen(info_req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _strip_hidden_blocks(text: str) -> str:
    cleaned = _VIVA_META_TAG_RE.sub("", text or "")
    cleaned = _BLOOM_DRAFT_TAG_RE.sub("", cleaned)
    return cleaned.strip()


def _extract_visible_question(text: str) -> str:
    cleaned = _strip_hidden_blocks(text)
    m = re.search(r"\*\*Câu hỏi nâng bậc \(\+1 Bloom\):\*\*\s*(.+)$", cleaned, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return cleaned


def _format_diff(diff: dict[str, Any] | None) -> dict[str, Any] | None:
    if not diff:
        return None
    flags_delta = diff.get("flag_delta")
    prev_count = diff.get("previous_flag_count")
    cur_count = diff.get("current_flag_count")
    if not diff.get("has_previous"):
        summary = "Phiên quét đầu tiên"
    elif isinstance(flags_delta, int):
        if flags_delta < 0:
            summary = f"Giảm {abs(flags_delta)} lỗi cứng so với phiên trước"
        elif flags_delta > 0:
            summary = f"Tăng +{flags_delta} lỗi cứng so với phiên trước"
        else:
            summary = "Không đổi số lỗi cứng"
    else:
        summary = "Đã đối chiếu"
    return {
        "has_previous": bool(diff.get("has_previous")),
        "previous_scan_id": diff.get("previous_scan_id"),
        "flags_delta": flags_delta if diff.get("has_previous") else None,
        "previous_flags_count": prev_count,
        "current_flags_count": cur_count,
        "bloom_delta": diff.get("bloom_delta"),
        "summary": summary,
    }


def _normalize_checks_for_ui(
    source_type: str,
    raw_checks: dict[str, Any] | None,
    hard_flags: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Chuẩn hoá 4 thẻ trạng thái PUBLIC-ACCESS / GIT-FORK-PR / PENALTY-STANDARD / PENALTY-KEY."""
    if source_type == "github" and raw_checks:
        def _map_status(raw_status: str) -> str:
            s = (raw_status or "").lower()
            if s in {"pass", "ok", "clean"}:
                return "pass"
            if s in {"fail", "error", "flagged"}:
                return "fail"
            if s in {"unknown_g10", "unknown", "warn", "g10"}:
                return "unknown"
            return s or "unknown"

        pub = raw_checks.get("public_access") or {}
        fork = raw_checks.get("git_fork_pr") or {}
        std = raw_checks.get("penalty_standard") or {}
        key = raw_checks.get("penalty_key") or {}
        return {
            "PUBLIC-ACCESS": {
                "key": "PUBLIC-ACCESS",
                "label": "PUBLIC-ACCESS",
                "status": _map_status(str(pub.get("status") or "pass")),
                "detail": str(
                    pub.get("detail")
                    or (
                        f"Repo công khai (nhánh {pub.get('default_branch', 'main')})."
                        if pub.get("status") == "pass"
                        else "Không truy cập được repo ở chế độ công khai."
                    )
                ),
            },
            "GIT-FORK-PR": {
                "key": "GIT-FORK-PR",
                "label": "GIT-FORK-PR",
                "status": _map_status(str(fork.get("status") or "pass")),
                "detail": str(
                    fork.get("detail")
                    or (
                        "Không phát hiện PR mở nhầm về repo gốc BTC."
                        if fork.get("status") == "pass"
                        else f"Phát hiện PR mở lên `{fork.get('parent', 'upstream')}`."
                    )
                ),
            },
            "PENALTY-STANDARD": {
                "key": "PENALTY-STANDARD",
                "label": "PENALTY-STANDARD",
                "status": _map_status(str(std.get("status") or "pass")),
                "detail": str(
                    std.get("detail")
                    or (
                        "Chưa phát hiện sửa chuẩn đạt / xoá câu thử sau CP2."
                        if std.get("status") == "pass"
                        else "Phát hiện chỉnh sửa chuẩn CP2 sau mốc chốt."
                    )
                ),
            },
            "PENALTY-KEY": {
                "key": "PENALTY-KEY",
                "label": "PENALTY-KEY",
                "status": _map_status(str(key.get("status") or "pass")),
                "detail": str(
                    key.get("detail")
                    or (
                        "Không phát hiện .env / khóa bí mật trên cây file."
                        if key.get("status") == "pass"
                        else "Phát hiện tệp nhạy cảm hoặc secret bị lộ."
                    )
                ),
            },
        }

    # Offline S01..S25: suy luận 4 thẻ từ hard_flags
    rule_ids = {str(f.get("rule_id") or "") for f in hard_flags}
    return {
        "PUBLIC-ACCESS": {
            "key": "PUBLIC-ACCESS",
            "label": "PUBLIC-ACCESS",
            "status": "fail" if "PUBLIC-ACCESS" in rule_ids else "pass",
            "detail": (
                "Hồ sơ mô phỏng đánh dấu trạng thái Private."
                if "PUBLIC-ACCESS" in rule_ids
                else "Hồ sơ mẫu offline sẵn sàng kiểm toán."
            ),
        },
        "GIT-FORK-PR": {
            "key": "GIT-FORK-PR",
            "label": "GIT-FORK-PR",
            "status": "fail" if "GIT-FORK-PR" in rule_ids else "pass",
            "detail": (
                "Phát hiện cờ GIT-FORK-PR trong hồ sơ."
                if "GIT-FORK-PR" in rule_ids
                else "Không phát hiện cờ PR nhầm repo gốc."
            ),
        },
        "PENALTY-STANDARD": {
            "key": "PENALTY-STANDARD",
            "label": "PENALTY-STANDARD",
            "status": "fail" if "PENALTY-STANDARD" in rule_ids else "pass",
            "detail": (
                "Phát hiện dấu hiệu sửa chuẩn đạt / xoá câu thử sau CP2."
                if "PENALTY-STANDARD" in rule_ids
                else "Chuẩn đạt & bộ câu thử giữ nguyên."
            ),
        },
        "PENALTY-KEY": {
            "key": "PENALTY-KEY",
            "label": "PENALTY-KEY",
            "status": "fail" if "PENALTY-KEY" in rule_ids else "pass",
            "detail": (
                "Phát hiện lộ key/PII hoặc file nhạy cảm."
                if "PENALTY-KEY" in rule_ids
                else "Không phát hiện lộ bí mật / PII."
            ),
        },
    }


class ScanRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=300)
    force_refresh: bool = False


class VivaAskRequest(BaseModel):
    scan_id: str = Field(..., min_length=1, max_length=120)
    member_name: str = Field(default="", max_length=120)
    topic: str | None = Field(default=None, max_length=300)


class VivaDefenseRequest(BaseModel):
    scan_id: str = Field(..., min_length=1, max_length=120)
    member_name: str = Field(default="", max_length=120)
    question: str = Field(default="", max_length=2000)
    answer: str = Field(..., min_length=1, max_length=8000)
    viva_meta: dict[str, Any] | str | None = None

    @field_validator("viva_meta")
    @classmethod
    def _validate_viva_meta_len(cls, v: Any) -> Any:
        if isinstance(v, str) and len(v) > 8192:
            raise ValueError("viva_meta vượt quá 8192 ký tự.")
        return v


class VivaCoachRequest(BaseModel):
    scan_id: str = Field(..., min_length=1, max_length=120)
    member_name: str = Field(default="", max_length=120)
    goal: str | None = Field(default=None, max_length=500)


class ConfirmLogRequest(BaseModel):
    scan_id: str | None = Field(default=None, max_length=120)
    member_name: str = Field(default="", max_length=120)
    entry_id: int | None = None
    draft: dict[str, Any] | None = None
    concept_key: str | None = Field(default=None, max_length=120)
    status: str | None = Field(default=None, max_length=40)


class CardStatusRequest(BaseModel):
    scan_id: str | None = Field(default=None, max_length=120)
    member_name: str = Field(default="", max_length=120)
    concept_key: str = Field(..., min_length=1, max_length=120)
    status: str = Field(..., min_length=1, max_length=40)


def create_app(db_path: str | os.PathLike[str] | None = None) -> FastAPI:
    """Khởi tạo FastAPI app gắn SQLite WAL (cho phép truyền db_path riêng khi test)."""
    ai.load_env()
    if not (os.environ.get("SESSION_SECRET") or "").strip():
        logger.warning(
            "SESSION_SECRET chưa được cấu hình trong .env — đang dùng khóa tạm theo process; "
            "khi chạy --workers 2 cần đặt SESSION_SECRET chung trong .env để tránh lệch cookie/OAuth giữa các worker."
        )
    effective_db_path = db_path or os.environ.get("REPOKSV_DB_PATH") or None
    store = db_mod.RepoKsvDB(effective_db_path)
    ram_scan_files: OrderedDict[str, dict[str, str]] = OrderedDict()

    enable_docs = _env_bool("ENABLE_API_DOCS", False)
    app = FastAPI(
        title="RepoKSV API",
        version="1.0.0",
        docs_url="/docs" if enable_docs else None,
        redoc_url="/redoc" if enable_docs else None,
        openapi_url="/openapi.json" if enable_docs else None,
    )
    app.state.db = store
    app.state.ram_scan_files = ram_scan_files

    def _attach_security_headers(resp: Response, path: str) -> Response:
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if path.startswith(("/api/", "/auth/")) or path in {"/api", "/auth"}:
            resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.middleware("http")
    async def security_middleware(request: Request, call_next: Any) -> Response:
        path = request.url.path
        cl_hdr = request.headers.get("content-length")
        if cl_hdr is not None:
            try:
                if int(cl_hdr) > MAX_BODY_BYTES:
                    return _attach_security_headers(
                        JSONResponse({"detail": "Payload vượt quá giới hạn 256 KB."}, status_code=413),
                        path,
                    )
            except ValueError:
                return _attach_security_headers(
                    JSONResponse({"detail": "Content-Length không hợp lệ."}, status_code=400),
                    path,
                )

        if request.method.upper() in {"POST", "PUT", "DELETE", "PATCH"}:
            chunks: list[bytes] = []
            total_bytes = 0
            async for chunk in request.stream():
                if not chunk:
                    continue
                total_bytes += len(chunk)
                if total_bytes > MAX_BODY_BYTES:
                    return _attach_security_headers(
                        JSONResponse({"detail": "Payload vượt quá giới hạn 256 KB."}, status_code=413),
                        path,
                    )
                chunks.append(chunk)
            request._body = b"".join(chunks)
            origin = (request.headers.get("origin") or "").strip()
            if origin:
                if origin.lower() == "null":
                    return _attach_security_headers(
                        JSONResponse({"detail": "Origin không hợp lệ (CSRF check)."}, status_code=403),
                        path,
                    )
                parsed_origin = urllib.parse.urlsplit(origin)
                origin_host = (parsed_origin.netloc or "").lower()
                try:
                    target_host = _trusted_request_host(request).lower()
                except HTTPException as exc:
                    return _attach_security_headers(
                        JSONResponse({"detail": exc.detail}, status_code=exc.status_code),
                        path,
                    )
                if (
                    parsed_origin.scheme.lower() not in {"http", "https"}
                    or not origin_host
                    or origin_host != target_host
                ):
                    return _attach_security_headers(
                        JSONResponse({"detail": "Origin không khớp host máy chủ (CSRF check)."}, status_code=403),
                        path,
                    )

        resp = await call_next(request)
        return _attach_security_headers(resp, path)

    assets_dir = os.path.join(WEB_DIST_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    def _put_ram_files(scan_id: str, files_content: dict[str, str]) -> None:
        ram_scan_files[scan_id] = dict(files_content)
        ram_scan_files.move_to_end(scan_id)
        while len(ram_scan_files) > MAX_RAM_SCANS:
            ram_scan_files.popitem(last=False)

    def _resolve_actor(request: Request, response: Response | None = None, *, require_write: bool = True) -> str:
        """Lấy owner_user_id từ cookie session Google hoặc guest demo anon:<id>."""
        for cname in (SESSION_COOKIE_HTTPS, SESSION_COOKIE_HTTP):
            tok = request.cookies.get(cname)
            payload = verify_token(tok, expected_typ="session")
            if payload and payload.get("user_id"):
                uid = str(payload["user_id"])
                user = store.get_user(uid)
                if user is not None:
                    return uid

        if not _env_bool("ALLOW_GUEST_DEMO", False):
            raise HTTPException(status_code=401, detail="Vui lòng đăng nhập Google để tiếp tục.")

        anon_tok = request.cookies.get(ANON_COOKIE)
        anon_payload = verify_token(anon_tok, expected_typ="anon")
        if anon_payload and anon_payload.get("anon_id"):
            anon_id = str(anon_payload["anon_id"])
        else:
            anon_id = secrets.token_hex(12)
            if response is not None:
                signed_anon = sign_token({"anon_id": anon_id}, ttl_seconds=SESSION_TTL_S, typ="anon")
                response.set_cookie(
                    ANON_COOKIE,
                    signed_anon,
                    max_age=SESSION_TTL_S,
                    httponly=True,
                    samesite="lax",
                    secure=_is_https_request(request),
                    path="/",
                )
        owner_id = f"anon:{anon_id}"
        if require_write or store.get_user(owner_id) is None:
            store.upsert_user(owner_id, display_name="Guest Demo")
        return owner_id

    def _resolve_scan_files(session: dict[str, Any]) -> tuple[dict[str, str], str]:
        """Nạp files_content trong RAM cho phiên local SXX hoặc phiên GitHub."""
        source_type = session.get("source_type")
        label = str(session.get("source_label") or "")
        if source_type == "local":
            bundle = tools.load_submission_bundle(label)
            if not bundle.get("exists"):
                raise HTTPException(status_code=404, detail=f"Không tìm thấy dữ liệu hồ sơ {label}.")
            return {k: v for k, v in bundle["files_content"].items() if k != "meta.json"}, ""

        scan_id = str(session.get("scan_id") or "")
        cached = ram_scan_files.get(scan_id)
        if cached is not None:
            owner = label.split("/", 1)[0] if "/" in label else ""
            return cached, owner

        snap = github_guard.fetch_github_repo_snapshot(label, force_refresh=False, db=store)
        if not snap.get("ok"):
            raise HTTPException(
                status_code=404,
                detail=snap.get("g10_message") or "Không tải lại được file từ GitHub vào RAM.",
            )
        files_content = {k: v for k, v in (snap.get("files_content") or {}).items() if k != "meta.json"}
        _put_ram_files(scan_id, files_content)
        return files_content, str(snap.get("owner") or "")

    def _session_to_detail(session: dict[str, Any]) -> dict[str, Any]:
        members = session.get("members") or []
        default_user = members[0]["name"] if len(members) == 1 else (None if len(members) >= 2 else "Người dùng cá nhân")
        if session.get("mode") == "personal" and not members and session.get("source_type") == "github":
            default_user = str(session.get("source_label") or "").split("/", 1)[0] or "Người dùng cá nhân"
        viva = store.list_viva_entries(session["scan_id"])
        diff_raw = store.compare_with_previous_scan(session["scan_id"], owner_user_id=session["owner_user_id"])
        return {
            "scan_id": session["scan_id"],
            "source_type": session["source_type"],
            "source_label": session["source_label"],
            "commit_sha": session["commit_sha"],
            "mode": session["mode"],
            "members": members,
            "default_user": default_user,
            "audit_output": session["audit_output"],
            "hard_flags": session["hard_flags"],
            "hard_flags_count": len(session["hard_flags"]),
            "checks": session["checks"],
            "missing_required": session["missing_required"],
            "line_counts": session["line_counts"],
            "tracing": session["tracing"],
            "viva_entries": viva,
            "diff": _format_diff(diff_raw),
            "created_at": session["created_at"],
        }

    # ── Health & Auth ──────────────────────────────────────────────────────

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "oauth_configured": _oauth_configured(),
            "model_provider": (os.environ.get("MODEL_PROVIDER") or ai.MODEL_PROVIDER or "fake").lower(),
            "allow_guest_demo": _env_bool("ALLOW_GUEST_DEMO", False),
        }

    @app.get("/api/me")
    def get_me(request: Request, response: Response) -> dict[str, Any]:
        allow_guest = _env_bool("ALLOW_GUEST_DEMO", False)
        for cname in (SESSION_COOKIE_HTTPS, SESSION_COOKIE_HTTP):
            payload = verify_token(request.cookies.get(cname), expected_typ="session")
            if payload and payload.get("user_id"):
                user = store.get_user(str(payload["user_id"]))
                if user is not None:
                    return {
                        "authenticated": True,
                        "user": {
                            "user_id": user["user_id"],
                            "email": user["email"],
                            "display_name": user["display_name"],
                            "picture_url": user["picture_url"],
                        },
                        "guest_demo": allow_guest,
                        "oauth_configured": _oauth_configured(),
                    }

        if not allow_guest:
            raise HTTPException(status_code=401, detail="Chưa đăng nhập.")

        _resolve_actor(request, response, require_write=False)
        ip = _client_ip(request)
        conn = store._get_conn()
        row = conn.execute(
            "SELECT window_start, count FROM rate_limit_events WHERE bucket_key = ?",
            (f"ip:{ip}:scan",),
        ).fetchone()
        used = 0
        if row is not None and (int(time.time()) - int(row["window_start"])) < SCAN_WINDOW_S:
            used = int(row["count"])
        return {
            "authenticated": False,
            "user": None,
            "guest_demo": True,
            "guest_remaining": max(0, SCAN_RATE_LIMIT - used),
            "oauth_configured": _oauth_configured(),
        }

    @app.get("/auth/google")
    def auth_google(request: Request) -> RedirectResponse:
        client_id = (os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
        client_secret = (os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
        if not client_id or not client_secret:
            raise HTTPException(status_code=503, detail="Google OAuth chưa được cấu hình trên máy chủ.")

        state = secrets.token_urlsafe(24)
        code_verifier = secrets.token_urlsafe(48)
        challenge = _b64u_encode(hashlib.sha256(code_verifier.encode("ascii")).digest())
        redirect_uri = _google_redirect_uri(request)

        params = urllib.parse.urlencode({
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "prompt": "select_account",
        })
        resp = RedirectResponse(
            url=f"https://accounts.google.com/o/oauth2/v2/auth?{params}",
            status_code=302,
        )
        oauth_tok = sign_token(
            {"state": state, "code_verifier": code_verifier},
            ttl_seconds=OAUTH_TTL_S,
            typ="oauth",
        )
        resp.set_cookie(
            OAUTH_STATE_COOKIE,
            oauth_tok,
            max_age=OAUTH_TTL_S,
            httponly=True,
            samesite="lax",
            secure=_is_https_request(request),
            path="/",
        )
        return resp

    @app.get("/auth/google/callback")
    def auth_google_callback(
        request: Request,
        code: str | None = None,
        state: str | None = None,
        error: str | None = None,
    ) -> RedirectResponse:
        if error:
            safe_err = re.sub(r"[^A-Za-z0-9._ -]", "", error)[:64]
            raise HTTPException(status_code=400, detail=f"Google OAuth bị từ chối: {safe_err}")

        oauth_payload = verify_token(request.cookies.get(OAUTH_STATE_COOKIE), expected_typ="oauth")
        expected_state = str(oauth_payload.get("state") or "") if oauth_payload else ""
        if not oauth_payload or not state or not expected_state or not hmac.compare_digest(expected_state, state):
            raise HTTPException(status_code=400, detail="OAuth state không hợp lệ hoặc đã hết hạn.")
        if not code:
            raise HTTPException(status_code=400, detail="Thiếu authorization code từ Google.")

        client_id = (os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
        client_secret = (os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
        if not client_id or not client_secret:
            raise HTTPException(status_code=503, detail="Google OAuth chưa được cấu hình.")

        try:
            userinfo = _exchange_google_code(
                code=code,
                code_verifier=str(oauth_payload.get("code_verifier") or ""),
                redirect_uri=_google_redirect_uri(request),
                client_id=client_id,
                client_secret=client_secret,
            )
        except Exception as exc:
            logger.exception("Google OAuth token exchange failed: %s", exc)
            raise HTTPException(status_code=502, detail="Không đổi được mã Google OAuth.") from exc

        sub = str(userinfo.get("sub") or "").strip()
        if not sub:
            raise HTTPException(status_code=502, detail="Google userinfo thiếu trường sub.")
        uid = f"google:{sub}"
        store.upsert_user(
            uid,
            google_sub=sub,
            email=str(userinfo.get("email") or ""),
            display_name=str(userinfo.get("name") or userinfo.get("email") or "Google User"),
            picture_url=str(userinfo.get("picture") or ""),
        )
        session_tok = sign_token({"user_id": uid}, ttl_seconds=SESSION_TTL_S, typ="session")
        resp = RedirectResponse(url="/", status_code=302)
        https_req = _is_https_request(request)
        resp.delete_cookie(
            OAUTH_STATE_COOKIE,
            path="/",
            secure=https_req,
            httponly=True,
            samesite="lax",
        )
        resp.set_cookie(
            _session_cookie_name(request),
            session_tok,
            max_age=SESSION_TTL_S,
            httponly=True,
            samesite="lax",
            secure=https_req,
            path="/",
        )
        return resp

    @app.post("/auth/logout")
    def auth_logout(request: Request) -> RedirectResponse:
        resp = RedirectResponse(url="/", status_code=302)
        https_req = _is_https_request(request)
        resp.delete_cookie(
            SESSION_COOKIE_HTTPS,
            path="/",
            secure=True,
            httponly=True,
            samesite="lax",
        )
        for cname in (SESSION_COOKIE_HTTP, OAUTH_STATE_COOKIE):
            resp.delete_cookie(
                cname,
                path="/",
                secure=https_req,
                httponly=True,
                samesite="lax",
            )
        return resp

    # ── Submissions & Scanning ─────────────────────────────────────────────

    @app.get("/api/submissions")
    def list_submissions() -> dict[str, Any]:
        if not os.path.isfile(SUBMISSIONS_MANIFEST):
            return {"submissions": []}
        with open(SUBMISSIONS_MANIFEST, encoding="utf-8-sig") as f:
            data = json.load(f)
        cases = data.get("cases") or {}
        items = [{"id": sid, "label": sid, "title": desc} for sid, desc in sorted(cases.items())]
        return {"submissions": items}

    @app.post("/api/scan")
    def scan_repo(req: ScanRequest, request: Request, response: Response) -> dict[str, Any]:
        owner_user_id = _resolve_actor(request, response)
        ip = _client_ip(request)
        allowed, _, retry_after = store.check_and_increment_rate_limit(
            f"ip:{ip}:scan", SCAN_RATE_LIMIT, SCAN_WINDOW_S
        )
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Vượt giới hạn {SCAN_RATE_LIMIT} lượt quét/phút. Thử lại sau {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )

        raw_target = req.target.strip()
        sub_id = agent._extract_submission_id(raw_target)
        if sub_id:
            bundle = tools.load_submission_bundle(sub_id)
            if not bundle.get("exists"):
                raise HTTPException(status_code=404, detail=f"Không tìm thấy hồ sơ `{sub_id}`.")
            files_content = {k: v for k, v in bundle["files_content"].items() if k != "meta.json"}
            hard_flags = tools.scan_in_memory_submission(bundle["files_content"], meta=bundle.get("meta"))
            identity = tools.extract_project_identity(files_content)
            file_info = bundle["file_info"]

            tracing.begin("api_scan")
            try:
                res = agent._run_audit_pipeline(
                    f"SUBMISSION_ID: {sub_id}",
                    file_info,
                    hard_flags,
                    {k: tools.read_file_lines(sub_id, k) for k in file_info["present_files"] if k != "meta.json"},
                )
            finally:
                trace_summary, _ = tracing.end()

            checks_ui = _normalize_checks_for_ui("local", None, hard_flags)
            created = store.create_scan_session(
                owner_user_id,
                "local",
                sub_id,
                res["output"],
                commit_sha="",
                mode=identity["mode"],
                members=identity["members"],
                hard_flags=hard_flags,
                checks=checks_ui,
                missing_required=file_info["missing_required"],
                line_counts=file_info["line_counts"],
                tracing=trace_summary,
            )
            return _session_to_detail(created)

        parsed_gh = github_guard.parse_github_target(raw_target)
        if not parsed_gh:
            raise HTTPException(
                status_code=400,
                detail="URL GitHub không hợp lệ hoặc bị chặn bởi bộ lọc SSRF.",
            )

        snap = github_guard.fetch_github_repo_snapshot(
            parsed_gh, force_refresh=req.force_refresh, db=store
        )
        if not snap.get("ok"):
            err_code = snap.get("error_code")
            if err_code == "INVALID_OR_BLOCKED_URL":
                raise HTTPException(status_code=400, detail=snap.get("g10_message") or "URL bị chặn SSRF.")
            if err_code == "RATE_LIMITED":
                raise HTTPException(status_code=429, detail=snap.get("g10_message") or "GitHub API rate limited.")
            raise HTTPException(status_code=404, detail=snap.get("g10_message") or "Không truy cập được repo GitHub.")

        full_name = str(snap["full_name"])
        commit_sha = str(snap.get("commit_sha") or "")
        files_content = {k: v for k, v in (snap.get("files_content") or {}).items() if k != "meta.json"}
        identity = snap.get("identity") or tools.extract_project_identity(files_content, github_owner=snap.get("owner", ""))
        hard_flags = snap.get("hard_flags") or []
        checks_ui = _normalize_checks_for_ui("github", snap.get("checks"), hard_flags)

        cache_key = f"audit:{full_name.lower()}"
        cached_audit = None if req.force_refresh else store.get_cached_github(cache_key)
        if cached_audit and cached_audit.get("commit_sha") == commit_sha and (cached_audit.get("payload") or {}).get("audit_output"):
            audit_output = str(cached_audit["payload"]["audit_output"])
            trace_summary = {"model_calls": 0, "tool_calls": 0, "tokens_in": 0, "tokens_out": 0, "from_cache": True}
        else:
            file_info = {
                "exists": True,
                "submission_id": full_name,
                "present_files": snap["present_files"],
                "missing_required": snap["missing_required"],
                "line_counts": snap["line_counts"],
            }
            numbered_contents = {
                fname: tools.format_numbered_lines(raw_txt, limit=120)
                for fname, raw_txt in files_content.items()
            }
            notes_list = list(snap.get("g10_warnings") or [])
            if identity.get("mode") == "team":
                notes_list.append("Chế độ nhóm — thành viên trong TEAMS.md: " + ", ".join(identity.get("member_names") or []))
            else:
                notes_list.append(f"Chế độ cá nhân — mặc định: {identity.get('default_user')}")

            tracing.begin("api_scan_github")
            try:
                res = agent._run_audit_pipeline(
                    f"AUDIT_GITHUB | {parsed_gh['url']}",
                    file_info,
                    hard_flags,
                    numbered_contents,
                    extra_notes="\n".join(f"- {n}" for n in notes_list if n),
                )
            finally:
                trace_summary, _ = tracing.end()
            audit_output = res["output"]
            store.set_cached_github(cache_key, commit_sha, {"audit_output": audit_output}, ttl_seconds=300)

        created = store.create_scan_session(
            owner_user_id,
            "github",
            full_name,
            audit_output,
            commit_sha=commit_sha,
            mode=identity["mode"],
            members=identity["members"],
            hard_flags=hard_flags,
            checks=checks_ui,
            missing_required=snap["missing_required"],
            line_counts=snap["line_counts"],
            tracing=trace_summary,
        )
        _put_ram_files(created["scan_id"], files_content)
        return _session_to_detail(created)

    @app.get("/api/sessions")
    @app.get("/api/scans")
    def list_sessions(request: Request, response: Response) -> dict[str, Any]:
        owner_user_id = _resolve_actor(request, response, require_write=False)
        rows = store.list_scan_sessions(owner_user_id, limit=50)
        summaries = []
        for s in rows:
            diff = store.compare_with_previous_scan(s["scan_id"], owner_user_id=owner_user_id)
            summaries.append({
                "scan_id": s["scan_id"],
                "source_type": s["source_type"],
                "source_label": s["source_label"],
                "commit_sha": s["commit_sha"],
                "mode": s["mode"],
                "hard_flags_count": len(s["hard_flags"]),
                "flags_delta": diff["flag_delta"] if diff["has_previous"] else None,
                "created_at": s["created_at"],
            })
        return {"sessions": summaries}

    @app.get("/api/sessions/{scan_id}")
    @app.get("/api/scans/{scan_id}")
    def get_session(scan_id: str, request: Request, response: Response) -> dict[str, Any]:
        owner_user_id = _resolve_actor(request, response, require_write=False)
        session = store.get_scan_session(scan_id, owner_user_id=owner_user_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên quét.")
        return _session_to_detail(session)

    @app.get("/api/sessions/{scan_id}/diff")
    def get_session_diff(scan_id: str, request: Request, response: Response) -> dict[str, Any]:
        owner_user_id = _resolve_actor(request, response, require_write=False)
        session = store.get_scan_session(scan_id, owner_user_id=owner_user_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên quét.")
        diff_raw = store.compare_with_previous_scan(scan_id, owner_user_id=owner_user_id)
        return _format_diff(diff_raw) or {}

    def _read_session_file_lines(
        scan_id: str,
        file_param: str,
        line: int | None,
        owner_user_id: str,
    ) -> dict[str, Any]:
        session = store.get_scan_session(scan_id, owner_user_id=owner_user_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên quét.")

        rel = (file_param or "").strip().replace("\\", "/")
        if not rel or rel.startswith("/") or ".." in rel.split("/") or "\x00" in rel:
            raise HTTPException(status_code=400, detail="Đường dẫn file không hợp lệ.")

        if session["source_type"] == "local":
            folder = tools._resolve_submission_dir(session["source_label"])
            if not folder:
                raise HTTPException(status_code=404, detail="Không tìm thấy thư mục hồ sơ.")
            base_real = os.path.realpath(folder)
            full_path = os.path.realpath(os.path.join(base_real, rel))
            if not full_path.startswith(base_real + os.sep) or not os.path.isfile(full_path):
                raise HTTPException(status_code=404, detail=f"Không tìm thấy file `{rel}`.")
            with open(full_path, encoding="utf-8-sig", errors="replace") as f:
                raw_lines = f.read().splitlines()
        else:
            files_content, _ = _resolve_scan_files(session)
            if rel not in files_content:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy file `{rel}` trong RAM cache.")
            raw_lines = files_content[rel].splitlines()

        items = [{"line": idx, "text": txt} for idx, txt in enumerate(raw_lines[:400], 1)]
        return {"file": rel, "target_line": line, "lines": items}

    @app.get("/api/sessions/{scan_id}/file-lines")
    def get_session_file_lines(
        scan_id: str,
        request: Request,
        response: Response,
        file: str = Query(..., min_length=1),
        line: int | None = Query(default=None),
    ) -> dict[str, Any]:
        owner_user_id = _resolve_actor(request, response, require_write=False)
        return _read_session_file_lines(scan_id, file, line, owner_user_id)

    @app.get("/api/file")
    def get_file_alias(
        request: Request,
        response: Response,
        scan_id: str = Query(..., min_length=1),
        file: str = Query(..., min_length=1),
        line: int | None = Query(default=None),
    ) -> dict[str, Any]:
        owner_user_id = _resolve_actor(request, response, require_write=False)
        return _read_session_file_lines(scan_id, file, line, owner_user_id)

    # ── Viva Ask / Defense / Coach & Study Memory ──────────────────────────

    def _enforce_llm_quota(owner_user_id: str, request: Request) -> None:
        if owner_user_id.startswith("anon:"):
            ip = _client_ip(request)
            ip_ok, _, ip_retry = store.check_and_increment_rate_limit(
                f"ip:{ip}:llm", LLM_DAILY_LIMIT, LLM_WINDOW_S
            )
            if not ip_ok:
                raise HTTPException(
                    status_code=429,
                    detail=f"IP khách đã đạt giới hạn {LLM_DAILY_LIMIT} lượt hỏi/chẩn đoán AI hôm nay.",
                    headers={"Retry-After": str(ip_retry)},
                )
        allowed, _, retry_after = store.check_and_increment_rate_limit(
            f"user:{owner_user_id}:llm", LLM_DAILY_LIMIT, LLM_WINDOW_S
        )
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Bạn đã đạt giới hạn {LLM_DAILY_LIMIT} lượt hỏi/chẩn đoán AI hôm nay.",
                headers={"Retry-After": str(retry_after)},
            )

    @app.post("/api/viva/ask")
    def api_viva_ask(req: VivaAskRequest, request: Request, response: Response) -> dict[str, Any]:
        owner_user_id = _resolve_actor(request, response)
        session = store.get_scan_session(req.scan_id, owner_user_id=owner_user_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên quét.")
        _enforce_llm_quota(owner_user_id, request)

        files_content, github_owner = _resolve_scan_files(session)
        bloom_summary = store.summarize_profile_for_prompt(owner_user_id, req.member_name)
        res = agent.viva_ask(
            files_content,
            member_name=req.member_name,
            topic=req.topic or "",
            bloom_summary=bloom_summary,
            github_owner=github_owner,
            line_counts=session.get("line_counts"),
        )
        if not res.get("ok"):
            raise HTTPException(status_code=400, detail=res.get("output") or "Không tạo được câu hỏi.")

        cards = res.get("cards") or []
        first_card = cards[0] if cards else (res.get("viva_meta") or {})
        visible_question = str(first_card.get("question") or _strip_hidden_blocks(res.get("output", "")))
        visible_raw = _strip_hidden_blocks(res.get("output", ""))
        resolved_member = str(res.get("member_name") or req.member_name or "Thành viên")

        hidden_meta = {
            "concept_key": first_card.get("concept_key", "viva-card-1"),
            "term": first_card.get("term", ""),
            "tag": first_card.get("tag", "khai_niem"),
            "source_cite": first_card.get("source_cite") or first_card.get("file_ref", ""),
            "reference": first_card.get("reference", ""),
            "rubric": first_card.get("rubric", ""),
            "common_misconceptions": first_card.get("common_misconceptions", []),
        }
        viva_meta_token = sign_token({"meta": hidden_meta}, ttl_seconds=SESSION_TTL_S, typ="viva_meta")
        entry = store.save_viva_entry(
            session["scan_id"],
            resolved_member,
            "ask",
            concept_key=str(hidden_meta["concept_key"]),
            question=visible_question,
            ai_feedback=visible_raw,
            draft=hidden_meta,
            saved_by_user=0,
        )
        return {
            "entry_id": entry["id"],
            "question": visible_question,
            "concept_key": hidden_meta["concept_key"],
            "term": hidden_meta["term"],
            "tag": hidden_meta["tag"],
            "source_cite": hidden_meta["source_cite"],
            "viva_meta_token": viva_meta_token,
            "raw_output": visible_raw,
        }

    @app.post("/api/viva/defense")
    def api_viva_defense(req: VivaDefenseRequest, request: Request, response: Response) -> dict[str, Any]:
        owner_user_id = _resolve_actor(request, response)
        session = store.get_scan_session(req.scan_id, owner_user_id=owner_user_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên quét.")
        _enforce_llm_quota(owner_user_id, request)

        viva_meta_dict: dict[str, Any] = {}
        if isinstance(req.viva_meta, str) and req.viva_meta:
            decoded = verify_token(req.viva_meta, expected_typ="viva_meta")
            if decoded and isinstance(decoded.get("meta"), dict):
                viva_meta_dict = decoded["meta"]

        files_content, github_owner = _resolve_scan_files(session)
        res = agent.viva_defense(
            files_content,
            member_name=req.member_name,
            question=req.question,
            user_answer=req.answer,
            viva_meta=viva_meta_dict,
            github_owner=github_owner,
            line_counts=session.get("line_counts"),
        )
        if not res.get("ok"):
            raise HTTPException(status_code=400, detail=res.get("output") or "Không đánh giá được câu trả lời.")

        draft = res.get("draft_profile_update") or {}
        if viva_meta_dict:
            if not draft.get("reference"):
                draft["reference"] = viva_meta_dict.get("reference", "")
            if not draft.get("rubric"):
                draft["rubric"] = viva_meta_dict.get("rubric", "")
        level = int(res.get("level", 0))
        visible_feedback = _strip_hidden_blocks(res.get("output", ""))
        resolved_member = str(res.get("member_name") or req.member_name or "Thành viên")

        entry = store.save_viva_entry(
            session["scan_id"],
            resolved_member,
            "defense",
            concept_key=str(draft.get("concept_key") or ""),
            question=req.question,
            answer=req.answer,
            ai_feedback=visible_feedback,
            bloom_level=level,
            draft=draft,
            saved_by_user=0,
        )
        return {
            "entry_id": entry["id"],
            "ai_feedback": visible_feedback,
            "bloom_level": level,
            "bloom_label": _BLOOM_TITLES.get(level, f"Level {level}"),
            "draft": draft,
        }

    @app.post("/api/viva/coach")
    def api_viva_coach(req: VivaCoachRequest, request: Request, response: Response) -> dict[str, Any]:
        owner_user_id = _resolve_actor(request, response)
        session = store.get_scan_session(req.scan_id, owner_user_id=owner_user_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên quét.")
        _enforce_llm_quota(owner_user_id, request)

        files_content, github_owner = _resolve_scan_files(session)
        bloom_summary = store.summarize_profile_for_prompt(owner_user_id, req.member_name)
        res = agent.viva_coach(
            files_content,
            member_name=req.member_name,
            goal=req.goal or "",
            bloom_summary=bloom_summary,
            save_draft=False,
            github_owner=github_owner,
            line_counts=session.get("line_counts"),
        )
        if not res.get("ok"):
            raise HTTPException(status_code=400, detail=res.get("output") or "Không tạo được tư vấn Bloom.")

        visible_advice = _strip_hidden_blocks(res.get("output", ""))
        question = _extract_visible_question(visible_advice)
        meta = res.get("viva_meta") or {}
        resolved_member = str(res.get("member_name") or req.member_name or "Thành viên")
        hidden_meta = {
            "concept_key": meta.get("concept_key", "viva-coach-step"),
            "term": meta.get("term", req.goal or "Nâng +1 Bloom"),
            "tag": meta.get("tag", "khai_niem"),
            "source_cite": meta.get("source_cite", ""),
            "reference": meta.get("reference", ""),
            "rubric": meta.get("rubric", ""),
            "common_misconceptions": meta.get("common_misconceptions", []),
        }
        viva_meta_token = sign_token({"meta": hidden_meta}, ttl_seconds=SESSION_TTL_S, typ="viva_meta")
        entry = store.save_viva_entry(
            session["scan_id"],
            resolved_member,
            "coach",
            concept_key=str(hidden_meta["concept_key"]),
            question=question,
            ai_feedback=visible_advice,
            draft=hidden_meta,
            saved_by_user=0,
        )
        return {
            "entry_id": entry["id"],
            "advice": visible_advice,
            "question": question,
            "concept_key": hidden_meta["concept_key"],
            "term": hidden_meta["term"],
            "tag": hidden_meta["tag"],
            "source_cite": hidden_meta["source_cite"],
            "viva_meta_token": viva_meta_token,
        }

    @app.post("/api/study/confirm-log")
    @app.post("/api/viva/confirm")
    def api_confirm_study_log(req: ConfirmLogRequest, request: Request, response: Response) -> dict[str, Any]:
        owner_user_id = _resolve_actor(request, response)
        if req.concept_key and req.status and req.entry_id is None and not req.draft:
            try:
                updated = store.update_card_status(
                    owner_user_id, req.member_name or "member", req.concept_key, req.status
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            if updated is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy khái niệm cần cập nhật.")
            return {
                "ok": True,
                "profile": store.get_user_bloom_profile(owner_user_id, req.member_name or updated["member_slug"]),
            }

        try:
            saved = store.confirm_bloom_draft(
                owner_user_id,
                req.member_name,
                draft=req.draft,
                viva_entry_id=req.entry_id,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        profile = store.get_user_bloom_profile(owner_user_id, "", member_slug=saved["member_slug"])
        return {"ok": True, "profile": profile}

    @app.post("/api/study/card-status")
    def api_update_card_status(req: CardStatusRequest, request: Request, response: Response) -> dict[str, Any]:
        owner_user_id = _resolve_actor(request, response)
        try:
            updated = store.update_card_status(
                owner_user_id, req.member_name or "member", req.concept_key, req.status
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if updated is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy thẻ khái niệm trong hồ sơ.")
        return {"ok": True, "concept": updated}

    @app.get("/api/profiles/{member_slug}")
    def api_get_member_profile(member_slug: str, request: Request, response: Response) -> dict[str, Any]:
        owner_user_id = _resolve_actor(request, response, require_write=False)
        return store.get_user_bloom_profile(owner_user_id, "", member_slug=db_mod.slugify(member_slug, "member"))

    @app.get("/api/bloom/me")
    def api_get_bloom_me(
        request: Request,
        response: Response,
        member: str = Query(default=""),
    ) -> dict[str, Any]:
        owner_user_id = _resolve_actor(request, response, require_write=False)
        if member:
            return store.get_user_bloom_profile(owner_user_id, member)
        conn = store._get_conn()
        rows = conn.execute(
            "SELECT * FROM bloom_profiles WHERE owner_user_id = ? ORDER BY bloom_level ASC, updated_at DESC",
            (owner_user_id,),
        ).fetchall()
        concepts = [store._row_to_bloom_item(r) for r in rows]
        return {"owner_user_id": owner_user_id, "member_slug": "all", "concepts": concepts}

    # ── Export (4 formats) ─────────────────────────────────────────────────

    def _run_export(fmt: str, scan_id: str, member: str, owner_user_id: str) -> Response:
        session = store.get_scan_session(scan_id, owner_user_id=owner_user_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên quét.")

        resolved_member = member.strip()
        if not resolved_member:
            members = session.get("members") or []
            resolved_member = members[0]["name"] if members else "nguoi-dung"

        profile = store.get_user_bloom_profile(owner_user_id, resolved_member)
        viva = store.list_viva_entries(scan_id)

        fmt_low = (fmt or "").strip().lower()
        if fmt_low == "anki":
            filename, body = exporters.export_anki_tsv(session, resolved_member, profile)
            media_type = "text/tab-separated-values; charset=utf-8"
        elif fmt_low == "md":
            filename, body = exporters.export_markdown_guide(session, resolved_member, profile)
            media_type = "text/markdown; charset=utf-8"
        elif fmt_low == "etude":
            filename, body = exporters.export_etude_pack_json(session, resolved_member, profile)
            media_type = "application/json; charset=utf-8"
        elif fmt_low == "json":
            filename, body = exporters.export_session_json(session, viva)
            media_type = "application/json; charset=utf-8"
        else:
            raise HTTPException(status_code=400, detail=f"Định dạng export không hỗ trợ: {fmt}")

        return Response(
            content=body.encode("utf-8"),
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.get("/api/export/{target_key}")
    def api_export(
        target_key: str,
        request: Request,
        response: Response,
        scan_id: str = Query(default=""),
        fmt: str = Query(default="anki"),
        member: str = Query(default=""),
    ) -> Response:
        owner_user_id = _resolve_actor(request, response, require_write=False)
        if target_key.lower() in {"anki", "md", "etude", "json"}:
            if not scan_id:
                raise HTTPException(status_code=400, detail="Thiếu tham số scan_id.")
            return _run_export(target_key, scan_id, member, owner_user_id)
        return _run_export(fmt, target_key, member, owner_user_id)

    # ── Static SPA & URL-Hack Catch-All ────────────────────────────────────

    _PUBLIC_STATIC_MIME = {
        "favicon.svg": "image/svg+xml",
        "logo.svg": "image/svg+xml",
        "repoksv-logo-120.png": "image/png",
        "repoksv-avatar.png": "image/png",
        "robots.txt": "text/plain; charset=utf-8",
    }

    def _serve_public_asset(asset_name: str) -> Response:
        media_type = _PUBLIC_STATIC_MIME.get(asset_name)
        if not media_type:
            raise HTTPException(status_code=404)
        fpath = os.path.join(WEB_DIST_DIR, asset_name)
        if os.path.isfile(fpath):
            return FileResponse(
                fpath,
                media_type=media_type,
                headers={"Cache-Control": "public, max-age=86400"},
            )
        raise HTTPException(status_code=404)

    @app.get("/favicon.svg", include_in_schema=False)
    def favicon() -> Response:
        return _serve_public_asset("favicon.svg")

    @app.get("/logo.svg", include_in_schema=False)
    def logo_svg() -> Response:
        return _serve_public_asset("logo.svg")

    @app.get("/repoksv-logo-120.png", include_in_schema=False)
    def logo_png() -> Response:
        return _serve_public_asset("repoksv-logo-120.png")

    @app.get("/repoksv-avatar.png", include_in_schema=False)
    def avatar_png() -> Response:
        return _serve_public_asset("repoksv-avatar.png")

    @app.get("/robots.txt", include_in_schema=False)
    def robots_txt() -> Response:
        return _serve_public_asset("robots.txt")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_catch_all(full_path: str) -> Response:
        if full_path.startswith(("api/", "auth/")) or full_path in {"api", "auth"}:
            raise HTTPException(status_code=404, detail="Endpoint không tồn tại.")
        if not enable_docs and full_path in {"docs", "docs/", "redoc", "redoc/", "openapi.json"}:
            raise HTTPException(status_code=404, detail="Not Found")
        index_html = os.path.join(WEB_DIST_DIR, "index.html")
        if os.path.isfile(index_html):
            return FileResponse(index_html, media_type="text/html; charset=utf-8")
        return HTMLResponse(
            content=(
                "<!doctype html><html lang='vi'><body><h1>RepoKSV API</h1>"
                "<p>Chưa build giao diện tĩnh <code>web/dist/</code>. Chạy <code>npm run build</code> trong <code>web/</code>.</p>"
                "</body></html>"
            ),
            status_code=200,
        )

    return app


app = create_app()
