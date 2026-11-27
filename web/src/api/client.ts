import type {
  BloomDraft,
  CardStatus,
  ExportFormat,
  FileLineItem,
  FileLinesResponse,
  HealthResponse,
  MeResponse,
  MemberProfileResponse,
  ScanDiffSummary,
  ScanSessionDetail,
  ScanSessionSummary,
  SubmissionOption,
  VivaAskResponse,
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
  scan_id: string;
  member_name: string;
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

export function getExportUrl(fmt: ExportFormat, scanId: string, member: string): string {
  const params = new URLSearchParams({
    scan_id: scanId,
    member,
  });
  return `/api/export/${fmt}?${params.toString()}`;
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
