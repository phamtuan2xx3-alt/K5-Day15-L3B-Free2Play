import { parseCitationTokens } from "../utils/citations.ts";

interface CiteTextProps {
  text: string;
  onSelectCite?: (file: string, line: number) => void;
}

export function CiteText({ text, onSelectCite }: CiteTextProps) {
  const tokens = parseCitationTokens(text);

  return (
    <>
      {tokens.map((tok, idx) => {
        if (tok.kind === "cite" && tok.file && tok.line !== undefined && onSelectCite) {
          return (
            <button
              key={`${tok.file}:${tok.line}-${idx}`}
              type="button"
              className="cite-chip"
              onClick={() => onSelectCite(tok.file!, tok.line!)}
              title={`Xem nguồn ${tok.file} tại dòng ${tok.line}`}
            >
              {tok.text}
            </button>
          );
        }
        return <span key={idx}>{tok.text}</span>;
      })}
    </>
  );
}
