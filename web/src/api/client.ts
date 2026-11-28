import type {
  AllKnowledgeResponse,
  BloomDraft,
  CardStatus,
  ExportFormat,
  FileLineItem,
  FileLinesResponse,
  HealthResponse,
  MeResponse,
  MemberProfileResponse,
  ScanDiffSummary,
  ScanPreflightPayload,
  ScanSessionDetail,
  ScanSessionSummary,
  StreamStageEvent,
  SubmissionOption,
  VivaAskResponse,
  VivaChatHistoryItem,
  VivaChatMode,
  VivaChatResponse,
  VivaCoachResponse,
  VivaDefenseResponse,
} from "../types.ts";

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!res.ok) {
    let message = `Lỗi máy chủ (${res.status})`;
    let code: string | undefined;
    try {
      const data = (await res.json()) as { detail?: string; error?: string; code?: string };
      message = data.detail || data.error || message;
      code = data.code;
    } catch {
      const text = await res.text().catch(() => "");
      if (text) message = text.slice(0, 240);
    }

    if (res.status === 401) {
      throw new ApiError(401, message || "Phiên đăng nhập đã hết hạn hoặc chưa đăng nhập.", code);
    }
    if (res.status === 429) {
      throw new ApiError(429, message || "Bạn thao tác quá nhanh. Vui lòng đợi một lát rồi thử lại.", code);
    }
    throw new ApiError(res.status, message, code);
  }

  return (await res.json()) as T;
}

export async function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health");
}

export async function getMe(): Promise<MeResponse> {
  try {
    const raw = await requestJson<Record<string, unknown>>("/api/me");
    const userObj = (raw.user ?? (raw.user_id ? raw : null)) as MeResponse["user"];
    return {
      authenticated: Boolean(raw.authenticated ?? userObj),
      user: userObj,
      guest_demo: Boolean(raw.guest_demo ?? raw.allow_guest_demo),
      guest_remaining: typeof raw.guest_remaining === "number" ? raw.guest_remaining : undefined,
      oauth_configured: typeof raw.oauth_configured === "boolean" ? raw.oauth_configured : undefined,
    };
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      return { authenticated: false, user: null, guest_demo: false };
    }
    throw err;
  }
}

export async function getSubmissions(): Promise<SubmissionOption[]> {
  const data = await requestJson<SubmissionOption[] | { submissions: SubmissionOption[] }>("/api/submissions");
  if (Array.isArray(data)) return data;
  return data.submissions ?? [];
}

export async function scanTarget(target: string, forceRefresh = false): Promise<ScanSessionDetail> {
  return requestJson<ScanSessionDetail>("/api/scan", {
    method: "POST",
    body: JSON.stringify({ target, force_refresh: forceRefresh }),
  });
}

export interface SseStreamHandlers {
  onStage?: (event: StreamStageEvent) => void;
  onPreflight?: (payload: ScanPreflightPayload) => void;
  onReasoning?: (delta: string) => void;
  onContent?: (delta: string) => void;
  signal?: AbortSignal;
}

export async function streamSsePost<TDone>(
  url: string,
  body: unknown,
  handlers: SseStreamHandlers = {},
): Promise<TDone> {
  const res = await fetch(url, {
    method: "POST",
    credentials: "include",
    signal: handlers.signal,
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let message = `Lỗi máy chủ (${res.status})`;
    let code: string | undefined;
    try {
      const data = (await res.json()) as { detail?: string; error?: string; code?: string };
      message = data.detail || data.error || message;
      code = data.code;
    } catch {
      const text = await res.text().catch(() => "");
      if (text) message = text.slice(0, 240);
    }
    if (res.status === 401) {
      throw new ApiError(401, message || "Phiên đăng nhập đã hết hạn hoặc chưa đăng nhập.", code);
    }
    if (res.status === 429) {
      throw new ApiError(429, message || "Bạn thao tác quá nhanh. Vui lòng đợi một lát rồi thử lại.", code);
    }
    throw new ApiError(res.status, message, code);
  }

  const ctype = (res.headers.get("Content-Type") || "").toLowerCase();
  if (ctype.includes("application/json")) {
    return (await res.json()) as TDone;
  }
  if (!res.body) {
    throw new ApiError(500, "Trình duyệt không hỗ trợ đọc stream phản hồi.");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let donePayload: TDone | null = null;

  const processFrame = (rawFrame: string) => {
    const trimmed = rawFrame.trim();
    if (!trimmed) return;
    let eventName = "message";
    const dataLines: string[] = [];
    for (const line of rawFrame.split(/\r?\n/)) {
      if (!line || line.startsWith(":")) continue;
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trimStart());
      }
    }
    if (dataLines.length === 0) return;
    const rawData = dataLines.join("\n");
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(rawData) as Record<string, unknown>;
    } catch {
      return;
    }

    if (eventName === "stage") {
      handlers.onStage?.({
        step: String(parsed.step ?? ""),
        label: String(parsed.label ?? ""),
      });
    } else if (eventName === "preflight") {
      handlers.onPreflight?.(parsed as unknown as ScanPreflightPayload);
    } else if (eventName === "reasoning") {
      const delta = typeof parsed.delta === "string" ? parsed.delta : "";
      if (delta) handlers.onReasoning?.(delta);
    } else if (eventName === "content") {
      const delta = typeof parsed.delta === "string" ? parsed.delta : "";
      if (delta) handlers.onContent?.(delta);
    } else if (eventName === "error") {
      const status = typeof parsed.status === "number" ? parsed.status : 500;
      const detail = typeof parsed.detail === "string" ? parsed.detail : "Lỗi trong lúc streaming.";
      throw new ApiError(status, detail);
    } else if (eventName === "done") {
      donePayload = parsed as unknown as TDone;
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (value) {
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split(/\r?\n\r?\n/);
      buffer = parts.pop() ?? "";
      for (const frame of parts) {
        processFrame(frame);
      }
    }
    if (done) {
      buffer += decoder.decode();
      if (buffer.trim()) {
        for (const frame of buffer.split(/\r?\n\r?\n/)) {
          processFrame(frame);
        }
      }
      break;
    }
  }

  if (donePayload === null) {
    throw new ApiError(502, "Kết nối stream kết thúc trước khi nhận kết quả hoàn chỉnh.");
  }
  return donePayload;
}

export async function scanTargetStream(
  target: string,
  forceRefresh = false,
  handlers: SseStreamHandlers = {},
): Promise<ScanSessionDetail> {
  return streamSsePost<ScanSessionDetail>(
    "/api/scan/stream",
    { target, force_refresh: forceRefresh },
    handlers,
  );
}

export async function listSessions(): Promise<ScanSessionSummary[]> {
  const data = await requestJson<ScanSessionSummary[] | { sessions: ScanSessionSummary[] }>("/api/sessions");
  if (Array.isArray(data)) return data;
  return data.sessions ?? [];
}

export async function getSession(scanId: string): Promise<ScanSessionDetail> {
  return requestJson<ScanSessionDetail>(`/api/sessions/${encodeURIComponent(scanId)}`);
}

export async function getSessionDiff(scanId: string): Promise<ScanDiffSummary> {
  return requestJson<ScanDiffSummary>(`/api/sessions/${encodeURIComponent(scanId)}/diff`);
}

export async function getFileLines(scanId: string, file: string, line?: number): Promise<FileLinesResponse> {
  const params = new URLSearchParams({ file });
  if (line !== undefined) params.set("line", String(line));
  const raw = await requestJson<Record<string, unknown>>(
    `/api/sessions/${encodeURIComponent(scanId)}/file-lines?${params.toString()}`,
  );

  let lines: FileLineItem[] = [];
  if (Array.isArray(raw.lines)) {
    lines = raw.lines.map((item, idx) => {
      if (typeof item === "string") {
        const m = item.match(/^L(\d+)\s*\|\s?(.*)$/);
        if (m) return { line: Number.parseInt(m[1], 10), text: m[2] };
        return { line: idx + 1, text: item };
      }
      const obj = item as { line?: number; text?: string; content?: string };
      return { line: obj.line ?? idx + 1, text: obj.text ?? obj.content ?? "" };
    });
  } else if (typeof raw.content === "string") {
    lines = raw.content.split(/\r?\n/).map((lineStr, idx) => {
      const m = lineStr.match(/^L(\d+)\s*\|\s?(.*)$/);
      if (m) return { line: Number.parseInt(m[1], 10), text: m[2] };
      return { line: idx + 1, text: lineStr };
    });
  }

  return {
    file: typeof raw.file === "string" ? raw.file : file,
    target_line: typeof raw.target_line === "number" ? raw.target_line : line,
    lines,
  };
}

export async function vivaAsk(payload: {
  scan_id: string;
  member_name: string;
  topic?: string;
}): Promise<VivaAskResponse> {
  return requestJson<VivaAskResponse>("/api/viva/ask", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function vivaAskStream(
  payload: { scan_id: string; member_name: string; topic?: string },
  handlers: SseStreamHandlers = {},
): Promise<VivaAskResponse> {
  return streamSsePost<VivaAskResponse>("/api/viva/ask/stream", payload, handlers);
}

export async function vivaDefense(payload: {
  scan_id: string;
  member_name: string;
  question: string;
  answer: string;
  viva_meta?: Record<string, unknown> | string;
}): Promise<VivaDefenseResponse> {
  return requestJson<VivaDefenseResponse>("/api/viva/defense", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function vivaDefenseStream(
  payload: {
    scan_id: string;
    member_name: string;
    question: string;
    answer: string;
    viva_meta?: Record<string, unknown> | string;
  },
  handlers: SseStreamHandlers = {},
): Promise<VivaDefenseResponse> {
  return streamSsePost<VivaDefenseResponse>("/api/viva/defense/stream", payload, handlers);
}

export async function vivaCoach(payload: {
  scan_id: string;
  member_name: string;
  goal?: string;
}): Promise<VivaCoachResponse> {
  return requestJson<VivaCoachResponse>("/api/viva/coach", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function vivaCoachStream(
  payload: { scan_id: string; member_name: string; goal?: string },
  handlers: SseStreamHandlers = {},
): Promise<VivaCoachResponse> {
  return streamSsePost<VivaCoachResponse>("/api/viva/coach/stream", payload, handlers);
}

export async function vivaChatStream(
  payload: {
    scan_id: string;
    member_name: string;
    mode: VivaChatMode;
    message?: string;
    history?: VivaChatHistoryItem[];
    active_concept?: Record<string, unknown>;
    viva_meta?: Record<string, unknown> | string;
  },
  handlers: SseStreamHandlers = {},
): Promise<VivaChatResponse> {
  return streamSsePost<VivaChatResponse>("/api/viva/chat/stream", payload, handlers);
}

export async function confirmStudyLog(payload: {
  scan_id: string;
  member_name: string;
  entry_id?: number;
  draft?: BloomDraft;
}): Promise<{ ok: boolean; profile?: MemberProfileResponse }> {
  return requestJson<{ ok: boolean; profile?: MemberProfileResponse }>("/api/study/confirm-log", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCardStatus(payload: {
  scan_id?: string;
  member_name: string;
  member_slug?: string;
  concept_key: string;
  status: CardStatus;
}): Promise<{ ok: boolean }> {
  return requestJson<{ ok: boolean }>("/api/study/card-status", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getMemberProfile(memberSlug: string): Promise<MemberProfileResponse> {
  return requestJson<MemberProfileResponse>(`/api/profiles/${encodeURIComponent(memberSlug)}`);
}

export async function getAllKnowledge(): Promise<AllKnowledgeResponse> {
  return requestJson<AllKnowledgeResponse>("/api/bloom/me");
}

export function getExportUrl(fmt: ExportFormat, scanId: string, member: string): string {
  const params = new URLSearchParams({
    scan_id: scanId,
    member,
  });
  return `/api/export/${fmt}?${params.toString()}`;
}

export function getExportAllUrl(fmt: ExportFormat): string {
  return `/api/export/${fmt}?scope=all`;
}

export async function fetchExportPreview(
  fmt: ExportFormat,
  scanId: string,
  member: string,
): Promise<{ content: string; filename: string }> {
  const url = getExportUrl(fmt, scanId, member);
  const res = await fetch(url, { credentials: "include" });
  if (!res.ok) {
    throw new ApiError(res.status, `Không xuất được định dạng ${fmt} (${res.status})`);
  }
  const disp = res.headers.get("Content-Disposition") ?? "";
  const m = disp.match(/filename="?([^";]+)"?/i);
  const extMap: Record<ExportFormat, string> = {
    anki: `study-anki-${member}.tsv`,
    md: `study-guide-${member}.md`,
    etude: `study-pack-${member}.pack.json`,
    json: `scan-${scanId}.json`,
  };
  const content = await res.text();
  return {
    content,
    filename: m?.[1] || extMap[fmt],
  };
}

export async function fetchExportAllPreview(
  fmt: ExportFormat,
): Promise<{ content: string; filename: string }> {
  const url = getExportAllUrl(fmt);
  const res = await fetch(url, { credentials: "include" });
  if (!res.ok) {
    throw new ApiError(res.status, `Không xuất được định dạng ${fmt} (${res.status})`);
  }
  const disp = res.headers.get("Content-Disposition") ?? "";
  const m = disp.match(/filename="?([^";]+)"?/i);
  const extMap: Record<ExportFormat, string> = {
    anki: "anki-all-repos.tsv",
    md: "study-guide-all.md",
    etude: "study-pack-all.pack.json",
    json: "knowledge-all.json",
  };
  const content = await res.text();
  return {
    content,
    filename: m?.[1] || extMap[fmt],
  };
}
