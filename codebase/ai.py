"""Nối model — chỗ DUY NHẤT trong bản chạy thử gọi model AI.

Hợp đồng (giữ nguyên để khung đo được token):
    call_model(system: str, user: str, model: str | None = None) -> dict với 4 khoá
        "text":       str   chữ model trả về
        "model":      str   tên model đã gọi (để tra giá ở bảng giá model)
        "tokens_in":  int   số token vào, lấy từ trường usage trong phản hồi API — KHÔNG ước lượng
        "tokens_out": int   số token ra, gồm cả token suy luận / suy nghĩ nếu API tính riêng
    @model_call (từ tracing.py) tự ghi mỗi lần gọi vào trace; agent.py gọi call_model bao nhiêu lần
    cũng được, khung tự cộng token.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from tracing import model_call

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOW_RAW = False  # đổi thành True để in nguyên phản hồi API khi cần debug tên trường


def load_env(path=os.path.join(ROOT, ".env")):
    """Đọc file .env (KEY=VALUE mỗi dòng) vào biến môi trường, không ghi đè biến đã có. Khung — không cần sửa."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()
MODEL_PROVIDER = (os.environ.get("MODEL_PROVIDER") or "fake").strip().lower()
MODEL_NAME = (os.environ.get("MODEL_NAME") or "").strip()
API_KEY = (os.environ.get("API_KEY") or "").strip()
API_BASE_URL = (os.environ.get("API_BASE_URL") or "").strip()

URL_OPENAI = "https://api.openai.com/v1/chat/completions"
URL_VILAO = "https://api.vilao.ai/v1/chat/completions"
URL_DEEPSEEK = "https://api.deepseek.com/chat/completions"
URL_CLAUDE = "https://api.anthropic.com/v1/messages"
URL_GEMINI_TMPL = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"
URL_OLLAMA = "http://localhost:11434/api/chat"
USER_AGENT = "RepoKSV-Auditor/1.0"


def normalize_vilao_url(base_url: str | None) -> str:
    """Chuẩn hoá API_BASE_URL cho Vilao (tự nối /chat/completions nếu kết thúc bằng /v1 hoặc /v1/)."""
    raw = (base_url or "").strip()
    if not raw:
        return URL_VILAO
    stripped = raw.rstrip("/")
    if stripped.endswith("/v1"):
        return stripped + "/chat/completions"
    return raw


def post_json(url: str, headers: dict, body: dict, timeout: int = 60) -> dict:
    """Gửi POST JSON, trả về JSON phản hồi. Chỉ dùng thư viện chuẩn (urllib)."""
    req_headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    req_headers.update(headers)
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers=req_headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", "replace")[:300]
        raise RuntimeError("HTTP %d: %s" % (e.code, err_body))
    if SHOW_RAW:
        print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
    return data


def _extract_openai_tokens(usage: dict) -> tuple[int, int]:
    """Đọc tokens_in và tokens_out từ usage chuẩn OpenAI/Vilao, cộng thêm reasoning_tokens nếu có."""
    u = usage or {}
    tokens_in = int(u.get("prompt_tokens") or 0)
    completion_tokens = int(u.get("completion_tokens") or 0)
    details = u.get("completion_tokens_details") or {}
    reasoning_tokens = int(details.get("reasoning_tokens") or 0) if isinstance(details, dict) else 0
    return tokens_in, completion_tokens + reasoning_tokens


def call_openai(
    system: str,
    user: str,
    model_name: str,
    url: str | None = None,
    api_key: str | None = None,
) -> dict:
    """Gọi OpenAI Chat Completions API hoặc endpoint tương thích OpenAI."""
    endpoint = url or API_BASE_URL or URL_OPENAI
    key = API_KEY if api_key is None else api_key
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": user}
    ]
    data = post_json(
        endpoint,
        {"Authorization": "Bearer " + key},
        {"model": model_name, "messages": messages},
    )
    tokens_in, tokens_out = _extract_openai_tokens(data.get("usage") or {})
    content = data["choices"][0]["message"].get("content") or ""
    return {
        "text": content,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
    }


def call_vilao(system: str, user: str, model_name: str) -> dict:
    """Gọi Vilao API (tương thích OpenAI Chat Completions)."""
    endpoint = normalize_vilao_url(API_BASE_URL)
    key = API_KEY or (os.environ.get("VILAO_API_KEY") or "").strip()
    return call_openai(system, user, model_name, url=endpoint, api_key=key)


def call_deepseek(system: str, user: str, model_name: str) -> dict:
    """Gọi DeepSeek API (tương thích định dạng OpenAI)."""
    return call_openai(system, user, model_name, url=API_BASE_URL or URL_DEEPSEEK)


def call_claude(system: str, user: str, model_name: str) -> dict:
    """Gọi Anthropic Claude Messages API."""
    endpoint = API_BASE_URL or URL_CLAUDE
    payload = {
        "model": model_name,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": user}],
    }
    if system:
        payload["system"] = system
    data = post_json(
        endpoint,
        {"x-api-key": API_KEY, "anthropic-version": "2023-06-01"},
        payload,
    )
    text = "".join(
        b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
    )
    u = data.get("usage") or {}
    return {
        "text": text,
        "tokens_in": int(u.get("input_tokens") or 0),
        "tokens_out": int(u.get("output_tokens") or 0),
    }


def call_gemini(system: str, user: str, model_name: str) -> dict:
    """Gọi Google Gemini generateContent API."""
    quoted_model = urllib.parse.quote(model_name, safe="")
    endpoint = API_BASE_URL or (URL_GEMINI_TMPL % quoted_model)
    payload: dict = {
        "contents": [{"role": "user", "parts": [{"text": user}]}],
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    data = post_json(
        endpoint,
        {"x-goog-api-key": API_KEY},
        payload,
    )
    candidates = data.get("candidates") or []
    parts = ((candidates[0].get("content") or {}).get("parts") or []) if candidates else []
    text = "".join(
        p.get("text", "") for p in parts if isinstance(p, dict) and not p.get("thought")
    )
    u = data.get("usageMetadata") or {}
    tokens_in = int(u.get("promptTokenCount") or 0)
    if "candidatesTokenCount" in u:
        tokens_out = int(u.get("candidatesTokenCount") or 0) + int(u.get("thoughtsTokenCount") or 0)
    else:
        total = int(u.get("totalTokenCount") or 0)
        tokens_out = max(0, total - tokens_in)
    return {
        "text": text,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
    }


def call_ollama(system: str, user: str, model_name: str) -> dict:
    """Gọi model chạy cục bộ qua Ollama."""
    endpoint = API_BASE_URL or URL_OLLAMA
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": user}
    ]
    data = post_json(
        endpoint,
        {},
        {"model": model_name, "messages": messages, "stream": False},
        timeout=300,
    )
    return {
        "text": (data.get("message") or {}).get("content") or "",
        "tokens_in": int(data.get("prompt_eval_count") or 0),
        "tokens_out": int(data.get("eval_count") or 0),
    }


@model_call
def call_model(system: str, user: str, model: str | None = None) -> dict:
    """Gọi model theo MODEL_PROVIDER trong .env (hoặc chế độ fake nếu chưa cấu hình)."""
    if MODEL_PROVIDER == "fake":
        last = (user.strip().splitlines() or [""])[-1]
        return {
            "text": "[câu trả lời giả — chưa nối model] " + last[:60],
            "model": "fake",
            "tokens_in": 0,
            "tokens_out": 0,
        }

    target_model = (model or MODEL_NAME).strip()
    if not target_model:
        raise ValueError("Thiếu MODEL_NAME trong .env (xem docs/connect-model.md).")

    effective_key = API_KEY
    if MODEL_PROVIDER == "vilao":
        effective_key = API_KEY or (os.environ.get("VILAO_API_KEY") or "").strip()

    if MODEL_PROVIDER in ("openai", "vilao", "deepseek", "anthropic", "gemini") and not effective_key:
        raise ValueError(
            "Thiếu API_KEY trong .env cho MODEL_PROVIDER=%s (xem docs/connect-model.md)."
            % MODEL_PROVIDER
        )

    if MODEL_PROVIDER == "openai":
        r = call_openai(system, user, target_model)
    elif MODEL_PROVIDER == "vilao":
        r = call_vilao(system, user, target_model)
    elif MODEL_PROVIDER == "deepseek":
        r = call_deepseek(system, user, target_model)
    elif MODEL_PROVIDER == "anthropic":
        r = call_claude(system, user, target_model)
    elif MODEL_PROVIDER == "gemini":
        r = call_gemini(system, user, target_model)
    elif MODEL_PROVIDER == "ollama":
        r = call_ollama(system, user, target_model)
    else:
        raise ValueError(
            "MODEL_PROVIDER=%r không được hỗ trợ. Chọn: fake, openai, vilao, gemini, anthropic, deepseek, ollama."
            % MODEL_PROVIDER
        )

    return {
        "text": str(r["text"]),
        "model": target_model,
        "tokens_in": int(r["tokens_in"]),
        "tokens_out": int(r["tokens_out"]),
    }
