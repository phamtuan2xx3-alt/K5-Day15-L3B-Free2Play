import { useEffect, useMemo, useState } from "react";
import { Download } from "lucide-react";
import { fetchExportPreview, getExportUrl } from "@/api/client.ts";
import { Alert } from "@/components/ui/alert.tsx";
import { Button } from "@/components/ui/button.tsx";
import type { ExportFormat, ScanSessionDetail } from "@/types.ts";
import { slugifyMember } from "@/utils/citations.ts";

interface ExportPanelProps {
  session: ScanSessionDetail;
}

const FORMAT_META: Array<{ fmt: ExportFormat; label: string; ext: string; desc: string }> = [
  {
    fmt: "anki",
    label: "Anki (.tsv)",
    ext: ".tsv",
    desc: "Chuẩn Anki 2.1+ (#separator:tab, #html:true, 3 cột) — lọc các mục còn yếu L0–L2.",
  },
  {
    fmt: "md",
    label: "Markdown (.md)",
    ext: ".md",
    desc: "Gom theo L0–L1, L2, L3+ cho Notion / Obsidian.",
  },
  {
    fmt: "etude",
    label: "Etude (.pack.json)",
    ext: ".pack.json",
    desc: 'Chuẩn "etude": "pack/1", thẻ tự luận type: "free".',
  },
  {
    fmt: "json",
    label: "JSON (.json)",
    ext: ".json",
    desc: "Toàn bộ scan_session + viva_entries.",
  },
];

export function ExportPanel({ session }: ExportPanelProps) {
  const defaultMember = useMemo(() => {
    if (session.default_user) return session.default_user;
    if (session.members.length >= 1) return session.members[0].name;
    return "nguoi-dung";
  }, [session]);

  const [memberName, setMemberName] = useState<string>(defaultMember);
  const [selectedFmt, setSelectedFmt] = useState<ExportFormat>("anki");
  const [previewText, setPreviewText] = useState<string>("");
  const [filename, setFilename] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    setMemberName(defaultMember);
    setPreviewText("");
    setErrorMsg(null);
  }, [session.scan_id, defaultMember]);

  const memberSlug = useMemo(() => {
    const found = session.members.find((m) => m.name === memberName);
    return found?.slug || slugifyMember(memberName);
  }, [session.members, memberName]);

  const handlePreview = async (fmt: ExportFormat) => {
    setSelectedFmt(fmt);
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetchExportPreview(fmt, session.scan_id, memberSlug);
      setPreviewText(res.content);
      setFilename(res.filename);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Không tải được bản xem trước.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void handlePreview("anki");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session.scan_id, memberSlug]);

  const activeMeta = FORMAT_META.find((m) => m.fmt === selectedFmt) ?? FORMAT_META[0];
  const downloadHref = getExportUrl(selectedFmt, session.scan_id, memberSlug);

  return (
    <div className="tabpanel-inner space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="m-0 text-lg font-semibold tracking-tight text-foreground">Xuất dữ liệu</h2>

        {session.members.length >= 2 ? (
          <div className="flex items-center gap-2">
            <label htmlFor="export-member-select" className="text-xs font-medium text-muted-foreground">
              Thành viên
            </label>
            <select
              id="export-member-select"
              className="h-9 rounded-md border border-input bg-background px-2.5 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-ring"
              value={memberName}
              onChange={(e) => setMemberName(e.target.value)}
            >
              {session.members.map((m) => (
                <option key={m.slug || m.name} value={m.name}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Chọn định dạng xuất">
        {FORMAT_META.map((item) => (
          <Button
            key={item.fmt}
            type="button"
            variant={selectedFmt === item.fmt ? "default" : "secondary"}
            onClick={() => void handlePreview(item.fmt)}
            disabled={loading}
          >
            {item.label}
          </Button>
        ))}

        <a
          href={downloadHref}
          download={filename || undefined}
          className="ml-auto inline-flex h-9 items-center gap-1.5 rounded-md border border-emerald-700/35 bg-emerald-500/10 px-3.5 text-sm font-medium text-emerald-800 no-underline hover:bg-emerald-500/15 dark:border-emerald-400/40 dark:text-emerald-300 transition-colors"
        >
          <Download aria-hidden="true" className="h-3.5 w-3.5" />
          Tải file ({activeMeta.ext})
        </a>
      </div>

      {errorMsg && (
        <Alert variant="destructive" role="alert">
          {errorMsg}
        </Alert>
      )}

      <details className="disclosure">
        <summary>
          Xem trước ({activeMeta.ext}) — {activeMeta.desc}
        </summary>
        <pre
          className="code-preview scroller max-h-[440px] overflow-auto whitespace-pre-wrap break-words rounded-md border border-border bg-card p-3 font-mono text-xs leading-relaxed text-foreground"
          aria-label="Xem trước nội dung file xuất"
        >
          {loading ? "Đang tạo…" : previewText || "(Trống)"}
        </pre>
      </details>
    </div>
  );
}
