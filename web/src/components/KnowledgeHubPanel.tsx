import { useCallback, useEffect, useMemo, useState } from "react";
import { Check, Download, FolderGit2, MessageSquare, RefreshCw } from "lucide-react";
import {
  fetchExportAllPreview,
  getAllKnowledge,
  getExportAllUrl,
  updateCardStatus,
} from "@/api/client.ts";
import { CiteText } from "@/components/CiteText.tsx";
import { Alert } from "@/components/ui/alert.tsx";
import { Badge } from "@/components/ui/badge.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Card, CardContent } from "@/components/ui/card.tsx";
import type { BloomConcept, CardStatus, ExportFormat, ScanSessionDetail } from "@/types.ts";
import { BLOOM_LABELS } from "@/utils/citations.ts";

interface KnowledgeHubPanelProps {
  activeSession: ScanSessionDetail | null;
  refreshTrigger?: number;
  onDrillConcept: (concept: BloomConcept) => void;
  onSelectCite: (file: string, line: number, scanId?: string) => void;
}

type LevelFilter = "all" | "weak" | "growing" | "mastered";

const FORMAT_META: Array<{ fmt: ExportFormat; label: string; ext: string; desc: string }> = [
  {
    fmt: "anki",
    label: "Anki (.tsv)",
    ext: ".tsv",
    desc: "Bộ thẻ Anki 2.1+ gồm toàn bộ khái niệm của tài khoản kèm tag repo nguồn.",
  },
  {
    fmt: "md",
    label: "Markdown (.md)",
    ext: ".md",
    desc: "Sổ tay học tập gom nhóm L0–L1, L2, L3+ qua tất cả repo.",
  },
  {
    fmt: "etude",
    label: "Etude (.pack.json)",
    ext: ".pack.json",
    desc: 'Gói thẻ tự luận chuẩn "etude": "pack/1" tổng hợp mọi repo.',
  },
  {
    fmt: "json",
    label: "JSON (.json)",
    ext: ".json",
    desc: "Bản sao lưu đầy đủ toàn bộ hệ thống kiến thức & lịch sử các phiên.",
  },
];

export function KnowledgeHubPanel({
  activeSession,
  refreshTrigger = 0,
  onDrillConcept,
  onSelectCite,
}: KnowledgeHubPanelProps) {
  const [concepts, setConcepts] = useState<BloomConcept[]>([]);
  const [repos, setRepos] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [repoFilter, setRepoFilter] = useState<string>("all");
  const [levelFilter, setLevelFilter] = useState<LevelFilter>("all");
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  // Integrated Export All state
  const [selectedFmt, setSelectedFmt] = useState<ExportFormat>("anki");
  const [previewText, setPreviewText] = useState<string>("");
  const [filename, setFilename] = useState<string>("");
  const [exportLoading, setExportLoading] = useState<boolean>(false);

  const loadKnowledge = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await getAllKnowledge();
      const items = res.concepts ?? [];
      setConcepts(items);
      const repoSet = new Set<string>(res.repos ?? []);
      for (const c of items) {
        if (c.source_repo) repoSet.add(c.source_repo);
      }
      setRepos(Array.from(repoSet).sort());
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Không tải được hệ thống kiến thức.");
    } finally {
      setLoading(false);
    }
  }, []);

  const handlePreview = useCallback(async (fmt: ExportFormat) => {
    setSelectedFmt(fmt);
    setExportLoading(true);
    try {
      const res = await fetchExportAllPreview(fmt);
      setPreviewText(res.content);
      setFilename(res.filename);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Không tạo được bản xem trước.");
    } finally {
      setExportLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadKnowledge();
  }, [loadKnowledge, refreshTrigger]);

  useEffect(() => {
    void handlePreview(selectedFmt);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshTrigger]);

  const counts = useMemo(() => {
    let weak = 0;
    let growing = 0;
    let mastered = 0;
    for (const c of concepts) {
      if (c.bloom_level <= 2 || c.status === "needs_review") {
        if (c.bloom_level >= 5 && c.status === "mastered") mastered += 1;
        else if (c.bloom_level >= 3 && c.status === "mastered") growing += 1;
        else weak += 1;
      } else if (c.bloom_level <= 4) {
        growing += 1;
      } else {
        mastered += 1;
      }
    }
    return { total: concepts.length, weak, growing, mastered };
  }, [concepts]);

  const filteredConcepts = useMemo(() => {
    return concepts.filter((c) => {
      if (repoFilter !== "all" && (c.source_repo || "") !== repoFilter) return false;
      if (levelFilter === "weak") return c.bloom_level <= 2 || c.status === "needs_review";
      if (levelFilter === "growing") return c.bloom_level >= 3 && c.bloom_level <= 4 && c.status === "mastered";
      if (levelFilter === "mastered") return c.bloom_level >= 5 && c.status === "mastered";
      return true;
    });
  }, [concepts, repoFilter, levelFilter]);

  const handleToggleStatus = async (c: BloomConcept) => {
    const nextStatus: CardStatus = c.status === "mastered" ? "needs_review" : "mastered";
    setBusyKey(c.concept_key);
    setErrorMsg(null);
    try {
      await updateCardStatus({
        scan_id: c.source_scan_id || activeSession?.scan_id,
        member_name: c.member_slug || "member",
        member_slug: c.member_slug,
        concept_key: c.concept_key,
        status: nextStatus,
      });
      setStatusMsg(
        nextStatus === "mastered"
          ? `Đã đánh dấu "${c.term || c.concept_key}" là Đã hiểu.`
          : `Đã chuyển "${c.term || c.concept_key}" sang Cần ôn thêm.`,
      );
      await loadKnowledge();
      await handlePreview(selectedFmt);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Không cập nhật được trạng thái.");
    } finally {
      setBusyKey(null);
    }
  };

  const activeMeta = FORMAT_META.find((m) => m.fmt === selectedFmt) ?? FORMAT_META[0];
  const downloadHref = getExportAllUrl(selectedFmt);

  return (
    <div className="tabpanel-inner mx-auto w-full max-w-[1040px] space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="m-0 text-lg font-semibold tracking-tight text-foreground">
            Hệ thống kiến thức tài khoản
          </h2>
          <p className="m-0 mt-0.5 text-xs text-muted-foreground">
            Tổng hợp <strong>{counts.total}</strong> khái niệm từ{" "}
            <strong>{repos.length || (counts.total > 0 ? 1 : 0)}</strong> repo · Hỗ trợ xuất toàn bộ dữ liệu ôn tập
          </p>
        </div>

        <Button type="button" variant="outline" size="sm" onClick={() => void loadKnowledge()} disabled={loading}>
          <RefreshCw aria-hidden="true" className="h-3.5 w-3.5" />
          Làm mới
        </Button>
      </div>

      {/* Bloom Summary & Filter Pills + Repo Filter */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-card p-3">
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Lọc theo mức Bloom">
          <Button
            type="button"
            size="sm"
            variant={levelFilter === "all" ? "default" : "secondary"}
            onClick={() => setLevelFilter("all")}
          >
            Tất cả ({counts.total})
          </Button>
          <Button
            type="button"
            size="sm"
            variant={levelFilter === "weak" ? "default" : "secondary"}
            onClick={() => setLevelFilter("weak")}
          >
            Cần ôn L0–L2 ({counts.weak})
          </Button>
          <Button
            type="button"
            size="sm"
            variant={levelFilter === "growing" ? "default" : "secondary"}
            onClick={() => setLevelFilter("growing")}
          >
            Đang nắm L3–L4 ({counts.growing})
          </Button>
          <Button
            type="button"
            size="sm"
            variant={levelFilter === "mastered" ? "default" : "secondary"}
            onClick={() => setLevelFilter("mastered")}
          >
            Đã vững L5–L6 ({counts.mastered})
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="knowledge-repo-filter" className="text-xs font-medium text-muted-foreground">
            Nguồn repo
          </label>
          <select
            id="knowledge-repo-filter"
            className="h-8 max-w-[260px] rounded-md border border-input bg-background px-2 text-xs text-foreground"
            value={repoFilter}
            onChange={(e) => setRepoFilter(e.target.value)}
          >
            <option value="all">Tất cả repo ({repos.length})</option>
            {repos.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Integrated Export All Section */}
      <Card className="bg-card shadow-none">
        <CardContent className="p-4 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="m-0 text-sm font-semibold text-foreground">Xuất toàn bộ kiến thức</h3>
              <p className="m-0 text-xs text-muted-foreground">{activeMeta.desc}</p>
            </div>
            <a
              href={downloadHref}
              download={filename || undefined}
              className="inline-flex h-9 items-center gap-1.5 rounded-md border border-emerald-700/35 bg-emerald-500/10 px-3.5 text-sm font-medium text-emerald-800 no-underline hover:bg-emerald-500/15 dark:border-emerald-400/40 dark:text-emerald-300 transition-colors"
            >
              <Download aria-hidden="true" className="h-3.5 w-3.5" />
              Tải tất cả ({activeMeta.ext})
            </a>
          </div>

          <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Chọn định dạng xuất">
            {FORMAT_META.map((item) => (
              <Button
                key={item.fmt}
                type="button"
                size="sm"
                variant={selectedFmt === item.fmt ? "default" : "secondary"}
                onClick={() => void handlePreview(item.fmt)}
                disabled={exportLoading}
              >
                {item.label}
              </Button>
            ))}
          </div>

          <details className="disclosure">
            <summary>
              Xem trước file xuất ({activeMeta.ext}) — toàn bộ tài khoản
            </summary>
            <pre
              className="code-preview scroller max-h-[360px] overflow-auto whitespace-pre-wrap break-words rounded-md border border-border bg-card p-3 font-mono text-xs leading-relaxed text-foreground"
              aria-label="Xem trước nội dung file xuất"
            >
              {exportLoading ? "Đang tạo…" : previewText || "(Trống)"}
            </pre>
          </details>
        </CardContent>
      </Card>

      {errorMsg && (
        <Alert variant="destructive" role="alert">
          {errorMsg}
        </Alert>
      )}
      {statusMsg && (
        <Alert variant="success" role="status" aria-live="polite">
          {statusMsg}
        </Alert>
      )}

      {/* All-Repo Knowledge Cards Grid */}
      {loading ? (
        <p className="text-sm text-muted-foreground">Đang tải hệ thống kiến thức…</p>
      ) : filteredConcepts.length === 0 ? (
        <Alert variant="info">
          Chưa có khái niệm nào khớp bộ lọc. Hãy vào tab <strong>Vấn đáp</strong> để kiểm tra &amp; lưu kiến thức từ các repo bạn đã soi.
        </Alert>
      ) : (
        <ul className="m-0 grid list-none grid-cols-1 gap-3 p-0 lg:grid-cols-2">
          {filteredConcepts.map((c) => {
            return (
              <li
                key={`${c.member_slug || "m"}:${c.concept_key}`}
                className="flex flex-col justify-between gap-3 rounded-lg border border-border bg-card p-4"
              >
                <div className="space-y-2">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="space-y-1 min-w-0 flex-1">
                      <strong className="block text-sm text-foreground">{c.term || c.concept_key}</strong>
                      <div className="flex flex-wrap items-center gap-1.5 text-xs min-w-0">
                        {c.source_repo ? (
                          <Badge
                            variant="default"
                            className="max-w-full min-w-0 gap-1 font-mono text-[11px]"
                            title={c.source_repo}
                          >
                            <FolderGit2 aria-hidden="true" className="h-3 w-3 shrink-0" />
                            <span className="truncate">{c.source_repo}</span>
                          </Badge>
                        ) : (
                          <Badge variant="default" className="text-[11px]">
                            Repo chung
                          </Badge>
                        )}
                        {c.member_slug && c.member_slug !== "member" ? (
                          <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">
                            @{c.member_slug}
                          </span>
                        ) : null}
                      </div>
                    </div>
                    <Badge
                      variant={
                        c.bloom_level <= 2 ? "destructive" : c.bloom_level <= 4 ? "warning" : "success"
                      }
                      title={BLOOM_LABELS[c.bloom_level]}
                    >
                      L{c.bloom_level}/6
                    </Badge>
                  </div>

                  {c.source_cite ? (
                    <div className="text-xs">
                      <CiteText
                        text={c.source_cite}
                        onSelectCite={(f, l) => onSelectCite(f, l, c.source_scan_id)}
                      />
                    </div>
                  ) : null}

                  {c.understood_points && c.understood_points.length > 0 ? (
                    <p className="m-0 text-xs text-emerald-700 dark:text-emerald-400">
                      <strong>Đã nắm:</strong> {c.understood_points.slice(0, 2).join("; ")}
                    </p>
                  ) : null}
                  {c.missing_points && c.missing_points.length > 0 ? (
                    <p className="m-0 text-xs text-muted-foreground">
                      <strong>Còn thiếu:</strong> {c.missing_points.slice(0, 2).join("; ")}
                    </p>
                  ) : null}
                  {c.misconceptions && c.misconceptions.length > 0 ? (
                    <p className="m-0 text-xs text-destructive">
                      <strong>Ngộ nhận:</strong> {c.misconceptions[0]}
                    </p>
                  ) : null}
                </div>

                <div className="flex flex-wrap items-center gap-2 border-t border-border/70 pt-2.5">
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    onClick={() => onDrillConcept(c)}
                  >
                    <MessageSquare aria-hidden="true" className="h-3.5 w-3.5" />
                    Ôn lại trong Vấn đáp
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    disabled={busyKey === c.concept_key}
                    onClick={() => void handleToggleStatus(c)}
                  >
                    <Check aria-hidden="true" className="h-3.5 w-3.5" />
                    {c.status === "mastered" ? "Chuyển sang Cần ôn" : "Đánh dấu Đã hiểu"}
                  </Button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
