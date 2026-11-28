export interface VivaStarterQuestion {
  id: string;
  title: string;
  targetMember?: string;
  question: string;
  sourceCite?: string;
}

export interface ParsedAuditReport {
  section1: string;
  section2: string;
  section3: string;
  section4: string;
  vivaQuestions: VivaStarterQuestion[];
  fullWithoutViva: string;
  hasStructuredSections: boolean;
}

const SECTION_HEADING_RE =
  /^\s*(?:(?:#{1,4}\s*|\*\*\s*)(?:\(([1-4])\)|([1-4])[.)])|\(([1-4])\)|([1-4])\))\s*(.+?)\s*(?:\*\*)?\s*$/;

const ALT_VIVA_HEADING_RE =
  /^\s*(?:#{1,4}\s*|\*\*\s*)?(?:\(?4\)?[.)]?\s*)?(?:Hai|2)\s+câu\s+hỏi\s+vặn\b/i;

function normalizeText(raw: string): string {
  return (raw || "")
    .replace(/<\/?submission_data_untrusted>/gi, "")
    .replace(/<\/?user_answer>/gi, "")
    .trim();
}

export function extractVivaStarterQuestions(section4Text: string): VivaStarterQuestion[] {
  const clean = (section4Text || "").trim();
  if (!clean) return [];

  const lines = clean.split(/\r?\n/);
  const blocks: string[] = [];
  let current: string[] = [];

  const itemStartRe = /^(?:[-*•]\s*)?(?:\*\*)?(?:Câu\s*\d+|#+\s*Câu\s*\d+|\d+[.)])(?:\*\*)?\s*[:—-]?\s*/i;

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      if (current.length > 0) {
        blocks.push(current.join("\n").trim());
        current = [];
      }
      continue;
    }
    if (blocks.length === 0 && current.length === 0 && (SECTION_HEADING_RE.test(trimmed) || ALT_VIVA_HEADING_RE.test(trimmed))) {
      continue;
    }
    if (itemStartRe.test(trimmed) && current.length > 0) {
      blocks.push(current.join("\n").trim());
      current = [trimmed];
    } else {
      current.push(trimmed);
    }
  }
  if (current.length > 0) {
    blocks.push(current.join("\n").trim());
  }

  const questions: VivaStarterQuestion[] = [];
  for (let i = 0; i < blocks.length; i += 1) {
    const body = blocks[i];
    if (!body || body.length < 12) continue;
    const rawClean = body.replace(/^[-*•]\s*/, "").trim();
    const headerMatch = rawClean.match(
      /^(?:\d+[.)]\s*)?(?:\*\*)?Câu\s*\d+(?:\s*\((?:gửi|cho|thành viên)\s+([^)]+)\))?(?:\*\*)?\s*[:—-]?\s*/i,
    );
    const memberFromPrefix = headerMatch?.[1]?.trim();
    const memberFromFallback = rawClean.match(/(?:gửi|cho|thành viên)\s+([^(\n:,—]{2,45})/i)?.[1]?.trim();
    const strippedBody = headerMatch ? rawClean.slice(headerMatch[0].length).trim() : rawClean;
    const citeMatch = strippedBody.match(/([A-Za-z0-9_./-]+\.[A-Za-z0-9]+(?::L\d+)?)/);
    const firstLine = strippedBody.split(/\r?\n/)[0].replace(/[*`]/g, "").trim();
    questions.push({
      id: `viva-starter-${i + 1}`,
      title: firstLine.length > 72 ? `${firstLine.slice(0, 70)}…` : firstLine,
      targetMember: memberFromPrefix || memberFromFallback,
      question: strippedBody || rawClean,
      sourceCite: citeMatch?.[1],
    });
  }
  return questions.slice(0, 4);
}

export function parseAuditReport(markdown: string): ParsedAuditReport {
  const cleaned = normalizeText(markdown);
  if (!cleaned) {
    return {
      section1: "",
      section2: "",
      section3: "",
      section4: "",
      vivaQuestions: [],
      fullWithoutViva: "",
      hasStructuredSections: false,
    };
  }

  const lines = cleaned.split(/\r?\n/);
  const buckets: Record<1 | 2 | 3 | 4, string[]> = { 1: [], 2: [], 3: [], 4: [] };
  const preamble: string[] = [];
  let currentNum: 1 | 2 | 3 | 4 | null = null;
  let foundSections = 0;

  for (const line of lines) {
    const m = line.match(SECTION_HEADING_RE);
    if (m) {
      const n = Number.parseInt(m[1] || m[2] || m[3] || m[4], 10);
      if (n >= 1 && n <= 4 && (currentNum === null || n > currentNum)) {
        currentNum = n as 1 | 2 | 3 | 4;
        foundSections += 1;
        buckets[currentNum].push(line);
        continue;
      }
    }
    if (currentNum !== 4 && ALT_VIVA_HEADING_RE.test(line)) {
      currentNum = 4;
      foundSections += 1;
      buckets[4].push(line);
      continue;
    }

    if (currentNum === null) {
      preamble.push(line);
    } else {
      buckets[currentNum].push(line);
    }
  }

  if (foundSections === 0) {
    return {
      section1: cleaned,
      section2: "",
      section3: "",
      section4: "",
      vivaQuestions: [],
      fullWithoutViva: cleaned,
      hasStructuredSections: false,
    };
  }

  const preambleText = preamble.join("\n").trim();
  const s1Body = buckets[1].join("\n").trim();
  const section1 = preambleText && s1Body ? `${preambleText}\n\n${s1Body}` : s1Body || preambleText;
  const section2 = buckets[2].join("\n").trim();
  const section3 = buckets[3].join("\n").trim();
  const section4 = buckets[4].join("\n").trim();

  const fullWithoutViva = [section1, section2, section3].filter(Boolean).join("\n\n");

  return {
    section1,
    section2,
    section3,
    section4,
    vivaQuestions: extractVivaStarterQuestions(section4),
    fullWithoutViva: fullWithoutViva || cleaned,
    hasStructuredSections: true,
  };
}
