export interface CitationToken {
  kind: "text" | "cite";
  text: string;
  file?: string;
  line?: number;
}

/**
 * Tach van ban thanh text thuan va chip trich dan `file:Lxx` (ho tro ca duong dan co `/`).
 * Khong bao gio sinh HTML tho -> chong XSS tuyet doi khi render qua React JSX.
 */
const CITE_REGEX = /([A-Za-z0-9_.-]+(?:\/[A-Za-z0-9_.-]+)*\.[A-Za-z0-9]+):L(\d{1,5})\b/g;

export function parseCitationTokens(input: string): CitationToken[] {
  if (!input) return [];
  const tokens: CitationToken[] = [];
  let lastIndex = 0;

  for (const match of input.matchAll(CITE_REGEX)) {
    const idx = match.index ?? 0;
    if (idx > lastIndex) {
      tokens.push({ kind: "text", text: input.slice(lastIndex, idx) });
    }
    const file = match[1];
    const line = Number.parseInt(match[2], 10);
    tokens.push({
      kind: "cite",
      text: match[0],
      file,
      line: Number.isFinite(line) ? line : 1,
    });
    lastIndex = idx + match[0].length;
  }

  if (lastIndex < input.length) {
    tokens.push({ kind: "text", text: input.slice(lastIndex) });
  }
  return tokens;
}

const RESERVED_TOP_ROUTES = new Set([
  "",
  "api",
  "auth",
  "login",
  "privacy",
  "terms",
  "health",
  "dashboard",
  "assets",
  "static",
  "favicon.svg",
  "favicon.ico",
  "robots.txt",
]);

/**
 * Chuan hoa URL-hack tu `window.location.pathname` hoac input nguoi dung.
 * Ho tro `/owner/repo`, `/https://github.com/owner/repo`, `/https:/github.com/owner/repo`.
 */
export function extractUrlHackTarget(pathname: string): string | null {
  const cleaned = pathname.replace(/^\/+|\/+$/g, "");
  if (!cleaned) return null;

  const firstSeg = cleaned.split("/")[0]?.toLowerCase() ?? "";
  if (RESERVED_TOP_ROUTES.has(firstSeg)) {
    return null;
  }

  const normalizedGh = cleaned
    .replace(/^https:\/+github\.com\//i, "https://github.com/")
    .replace(/^http:\/+github\.com\//i, "https://github.com/")
    .replace(/^github\.com\//i, "https://github.com/");

  if (/^https:\/\/github\.com\/[A-Za-z0-9_.-]{1,100}\/[A-Za-z0-9_.-]{1,100}(?:\/.*)?$/i.test(normalizedGh)) {
    const parts = normalizedGh.replace(/^https:\/\/github\.com\//i, "").split("/");
    return `https://github.com/${parts[0]}/${parts[1].replace(/\.git$/i, "")}`;
  }

  const ownerRepo = cleaned.split("/");
  if (
    ownerRepo.length >= 2 &&
    /^[A-Za-z0-9_.-]{1,100}$/.test(ownerRepo[0]) &&
    /^[A-Za-z0-9_.-]{1,100}$/.test(ownerRepo[1]) &&
    !ownerRepo[0].includes("..") &&
    !ownerRepo[1].includes("..")
  ) {
    return `https://github.com/${ownerRepo[0]}/${ownerRepo[1].replace(/\.git$/i, "")}`;
  }

  return null;
}

export function slugifyMember(name: string): string {
  return (
    name
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/đ/g, "d")
      .replace(/Đ/g, "D")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "user"
  );
}

export const BLOOM_LABELS: Record<number, string> = {
  0: "Chưa nắm / Lệch căn cứ",
  1: "L1 · Remember (Nhớ mặt chữ)",
  2: "L2 · Understand (Feynman)",
  3: "L3 · Apply (Áp dụng)",
  4: "L4 · Analyze (Phân tích Trade-off)",
  5: "L5 · Evaluate (Đối chiếu bằng chứng)",
  6: "L6 · Create (Xử lý tình huống biên)",
};
