import type { ReactNode } from "react";
import { cn } from "@/lib/utils.ts";
import { parseCitationTokens } from "@/utils/citations.ts";

interface MarkdownViewProps {
  text: string;
  onSelectCite?: (file: string, line: number) => void;
  className?: string;
}

const INLINE_PATTERN = /(\*\*[^*\n]+\*\*|`[^`\n]+`)/g;

function renderCiteAwareText(segment: string, onSelectCite?: (file: string, line: number) => void): ReactNode[] {
  const tokens = parseCitationTokens(segment);
  return tokens.map((tok, idx) => {
    if (tok.kind === "cite" && tok.file && tok.line !== undefined && onSelectCite) {
      return (
        <button
          key={`${tok.file}:${tok.line}-${idx}`}
          type="button"
          className="cite-chip"
          onClick={() => onSelectCite(tok.file!, tok.line!)}
          title={`Xem nguồn ${tok.file} dòng ${tok.line}`}
        >
          {tok.text}
        </button>
      );
    }
    return <span key={idx}>{tok.text}</span>;
  });
}

export function InlineMarkdown({
  text,
  onSelectCite,
}: {
  text: string;
  onSelectCite?: (file: string, line: number) => void;
}) {
  if (!text) return null;
  const parts = text.split(INLINE_PATTERN);
  return (
    <>
      {parts.map((part, idx) => {
        if (!part) return null;
        if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
          const inner = part.slice(2, -2);
          return (
            <strong key={idx} className="font-semibold text-foreground">
              {renderCiteAwareText(inner, onSelectCite)}
            </strong>
          );
        }
        if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
          const inner = part.slice(1, -1);
          const citeTokens = parseCitationTokens(inner);
          if (citeTokens.length === 1 && citeTokens[0].kind === "cite" && onSelectCite) {
            const tok = citeTokens[0];
            return (
              <button
                key={idx}
                type="button"
                className="cite-chip"
                onClick={() => onSelectCite(tok.file!, tok.line!)}
                title={`Xem nguồn ${tok.file} dòng ${tok.line}`}
              >
                {tok.text}
              </button>
            );
          }
          return (
            <code
              key={idx}
              className="rounded border border-border/70 bg-muted px-1 py-0.5 font-mono text-[0.84em] text-foreground"
            >
              {inner}
            </code>
          );
        }
        return <span key={idx}>{renderCiteAwareText(part, onSelectCite)}</span>;
      })}
    </>
  );
}

function cleanUntrustedWrapper(raw: string): string {
  return (raw || "")
    .replace(/<\/?submission_data_untrusted>/gi, "")
    .replace(/<\/?user_answer>/gi, "")
    .trim();
}

export function MarkdownView({ text, onSelectCite, className }: MarkdownViewProps) {
  const cleaned = cleanUntrustedWrapper(text);
  if (!cleaned) return null;

  const lines = cleaned.split(/\r?\n/);
  const nodes: ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      i += 1;
      continue;
    }

    // Fenced code block
    if (trimmed.startsWith("```")) {
      const codeLines: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i += 1;
      }
      if (i < lines.length) i += 1;
      nodes.push(
        <pre
          key={`code-${i}`}
          className="my-2 overflow-x-auto rounded-md border border-border bg-muted/60 p-3 font-mono text-xs leading-relaxed text-foreground"
        >
          {codeLines.join("\n")}
        </pre>,
      );
      continue;
    }

    // Headings (#..####)
    const headingMatch = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const content = headingMatch[2];
      nodes.push(
        <div
          key={`h-${i}`}
          role="heading"
          aria-level={Math.min(level + 2, 6)}
          className={cn(
            "font-semibold text-foreground tracking-tight",
            level <= 2 ? "mt-4 mb-1.5 text-[15px] border-b border-border/70 pb-1" : "mt-3 mb-1 text-sm",
          )}
        >
          <InlineMarkdown text={content} onSelectCite={onSelectCite} />
        </div>,
      );
      i += 1;
      continue;
    }

    // Horizontal rule
    if (/^(-{3,}|\*{3,})$/.test(trimmed)) {
      nodes.push(<hr key={`hr-${i}`} className="my-3 border-border" />);
      i += 1;
      continue;
    }

    // Unordered list
    if (/^[-*]\s+/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, ""));
        i += 1;
      }
      nodes.push(
        <ul key={`ul-${i}`} className="my-1.5 space-y-1 pl-5 list-disc text-sm leading-relaxed">
          {items.map((item, idx) => (
            <li key={idx}>
              <InlineMarkdown text={item} onSelectCite={onSelectCite} />
            </li>
          ))}
        </ul>,
      );
      continue;
    }

    // Ordered list
    if (/^\d+\.\s+/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ""));
        i += 1;
      }
      nodes.push(
        <ol key={`ol-${i}`} className="my-1.5 space-y-1 pl-5 list-decimal text-sm leading-relaxed">
          {items.map((item, idx) => (
            <li key={idx}>
              <InlineMarkdown text={item} onSelectCite={onSelectCite} />
            </li>
          ))}
        </ol>,
      );
      continue;
    }

    // Paragraph (collect consecutive plain lines)
    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].trim().startsWith("```") &&
      !/^#{1,4}\s+/.test(lines[i].trim()) &&
      !/^\s*[-*]\s+/.test(lines[i]) &&
      !/^\s*\d+\.\s+/.test(lines[i])
    ) {
      paraLines.push(lines[i]);
      i += 1;
    }
    nodes.push(
      <p key={`p-${i}`} className="my-1.5 text-sm leading-relaxed text-foreground/95 whitespace-pre-wrap">
        <InlineMarkdown text={paraLines.join("\n")} onSelectCite={onSelectCite} />
      </p>,
    );
  }

  return <div className={cn("space-y-1 break-words", className)}>{nodes}</div>;
}
