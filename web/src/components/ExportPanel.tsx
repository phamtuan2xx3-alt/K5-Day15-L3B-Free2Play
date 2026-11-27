import { useEffect, useMemo, useState } from "react";
import { fetchExportPreview, getExportUrl } from "../api/client.ts";
import type { ExportFormat, ScanSessionDetail } from "../types.ts";
import { slugifyMember } from "../utils/citations.ts";

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
    <div className="tabpanel-inner">
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: "0.75rem", marginBottom: "1rem" }}>
        <h2 style={{ margin: 0, fontSize: "1.15rem" }}>Xuất dữ liệu</h2>

        {session.members.length >= 2 ? (
          <div className="field-group">
            <label htmlFor="export-member-select" className="field-label">
              Hồ sơ thành viên
            </label>
            <select
              id="export-member-select"
              className="select-input"
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

      <div className="export-controls" role="group" aria-label="Chọn định dạng xuất">
        {FORMAT_META.map((item) => (
          <button
            key={item.fmt}
            type="button"
            className={`btn ${selectedFmt === item.fmt ? "btn-primary" : "btn-secondary"}`}
            onClick={() => void handlePreview(item.fmt)}
            disabled={loading}
          >
            {item.label}
          </button>
        ))}

        <a
          href={downloadHref}
          download={filename || undefined}
          className="btn btn-teal"
          style={{ marginInlineStart: "auto" }}
        >
          Tải file ({activeMeta.ext})
        </a>
      </div>

      {errorMsg && (
        <div className="alert alert-error" role="alert">
          {errorMsg}
        </div>
      )}

      <details className="disclosure">
        <summary>Xem trước ({activeMeta.ext}) — {activeMeta.desc}</summary>
        <pre className="code-preview scroller" aria-label="Xem trước nội dung file xuất">
          {loading ? "Đang tạo…" : previewText || "(Trống)"}
        </pre>
      </details>
    </div>
  );
}
