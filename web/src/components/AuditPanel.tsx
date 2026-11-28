import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, HelpCircle, MessageSquare, ShieldAlert, X } from "lucide-react";
import { InlineMarkdown, MarkdownView } from "@/components/MarkdownView.tsx";
import { Alert } from "@/components/ui/alert.tsx";
import { Badge } from "@/components/ui/badge.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Card, CardContent, CardHeader } from "@/components/ui/card.tsx";
import type {
  GitHubCheckStatus,
  HardFlag,
  ScanDiffSummary,
  ScanSessionDetail,
  ScanStreamState,
} from "@/types.ts";
import { parseAuditReport, type VivaStarterQuestion } from "@/utils/auditSections.ts";

interface AuditPanelProps {
  session: ScanSessionDetail;
  diff: ScanDiffSummary | null;
  onSelectCite: (file: string, line: number) => void;
  onGoToViva?: (starters: VivaStarterQuestion[]) => void;
}

const DEFAULT_CHECK_KEYS: Array<{ key: string; title: string; desc: string }> = [
  { key: "PUBLIC-ACCESS", title: "PUBLIC-ACCESS", desc: "Truy cập công khai (không Private)" },
  { key: "GIT-FORK-PR", title: "GIT-FORK-PR", desc: "Fork & Open PR về repo gốc BTC" },
  { key: "PENALTY-STANDARD", title: "PENALTY-STANDARD", desc: "Chống sửa chuẩn đạt sau CP2" },
  { key: "PENALTY-KEY", title: "PENALTY-KEY", desc: "Lộ .env / khóa bí mật trên cây file" },
];

function normalizeChecks(
  rawChecks: ScanSessionDetail["checks"],
  sourceType: string,
): GitHubCheckStatus[] {
  if (Array.isArray(rawChecks) && rawChecks.length > 0) {
    return rawChecks;
  }
  const obj = !Array.isArray(rawChecks) && rawChecks ? rawChecks : {};
  return DEFAULT_CHECK_KEYS.map((item) => {
    const found = obj[item.key];
    if (found) {
      return {
        key: item.key,
        label: found.label || item.title,
        status: found.status || "unknown",
        detail: found.detail || item.desc,
      };
    }
    return {
      key: item.key,
      label: item.title,
      status: sourceType === "github" ? "unknown" : "pass",
      detail:
        sourceType === "github"
          ? "Chưa có trạng thái từ GitHub Live Guard."
          : `${item.desc} (Kiểm tra hồ sơ mẫu offline).`,
    };
  });
}

function statusVariant(status: string): "success" | "destructive" | "warning" | "default" {
  const s = status.toLowerCase();
  if (s === "pass" || s === "ok" || s === "clean") return "success";
  if (s === "fail" || s === "error" || s === "flagged") return "destructive";
  if (s === "warn" || s === "g10" || s === "unknown") return "warning";
  return "default";
}

function statusLabel(status: string): string {
  const s = status.toLowerCase();
  if (s === "pass" || s === "ok" || s === "clean") return "ĐẠT";
  if (s === "fail" || s === "error" || s === "flagged") return "LỖI CỨNG";
  if (s === "warn" || s === "g10" || s === "unknown") return "G10";
  return status.toUpperCase();
}

function StatusIcon({ status }: { status: string }) {
  const s = status.toLowerCase();
  if (s === "pass" || s === "ok" || s === "clean") {
    return <CheckCircle2 aria-hidden="true" className="h-3.5 w-3.5 text-emerald-700 dark:text-emerald-400" />;
  }
  if (s === "fail" || s === "error" || s === "flagged") {
    return <ShieldAlert aria-hidden="true" className="h-3.5 w-3.5 text-destructive" />;
  }
  if (s === "warn" || s === "g10" || s === "unknown") {
    return <AlertTriangle aria-hidden="true" className="h-3.5 w-3.5 text-amber-700 dark:text-amber-400" />;
  }
  return <HelpCircle aria-hidden="true" className="h-3.5 w-3.5 text-muted-foreground" />;
}

function ChecksGrid({
  checks,
  onSelectCite,
}: {
  checks: GitHubCheckStatus[];
  onSelectCite?: (file: string, line: number) => void;
}) {
  return (
    <div
      className="grid grid-cols-2 gap-2 sm:gap-2.5 lg:grid-cols-4"
      role="region"
      aria-label="4 lớp kiểm tra GitHub Live Guard"
    >
      {checks.map((chk) => (
        <Card key={chk.key} className="status-card bg-card shadow-none">
          <CardHeader className="flex-row items-center justify-between gap-1.5 p-2.5 pb-1 sm:p-3 sm:pb-1.5">
            <span className="inline-flex min-w-0 items-center gap-1 font-mono text-[11px] sm:text-xs font-semibold text-foreground truncate">
              <StatusIcon status={chk.status} />
              <span className="truncate">{chk.label || chk.key}</span>
            </span>
            <Badge variant={statusVariant(chk.status)} className="shrink-0">
              {statusLabel(chk.status)}
            </Badge>
          </CardHeader>
          <CardContent className="p-2.5 pt-0 sm:p-3 sm:pt-0 text-[11px] sm:text-xs text-muted-foreground leading-relaxed">
            <InlineMarkdown text={chk.detail} onSelectCite={onSelectCite} />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function HardFlagsSection({
  hardFlags,
  onSelectCite,
}: {
  hardFlags: HardFlag[];
  onSelectCite?: (file: string, line: number) => void;
}) {
  return (
    <section aria-labelledby="hard-flags-heading" className="space-y-2.5">
      <h3 id="hard-flags-heading" className="m-0 text-sm font-semibold text-foreground">
        Lỗi cứng ({hardFlags.length})
      </h3>
      {hardFlags.length === 0 ? (
        <Alert variant="success">Không phát hiện lỗi cứng.</Alert>
      ) : (
        <ul className="m-0 grid list-none gap-2 p-0">
          {hardFlags.map((flag, idx) => {
            const lineNum = Number.parseInt(String(flag.line), 10) || 1;
            return (
              <li
                key={`${flag.rule_id}-${flag.file}-${idx}`}
                className="rounded-lg border border-destructive/35 bg-destructive/5 px-3.5 py-2.5 text-sm"
              >
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <Badge variant="destructive">{flag.rule_id}</Badge>
                  {onSelectCite ? (
                    <button
                      type="button"
                      className="cite-chip"
                      onClick={() => onSelectCite(flag.file, lineNum)}
                    >
                      {flag.file}:L{String(lineNum).padStart(2, "0")}
                    </button>
                  ) : (
                    <code className="cite-chip">{flag.file}:L{String(lineNum).padStart(2, "0")}</code>
                  )}
                </div>
                <div className="text-sm text-foreground">
                  <InlineMarkdown text={flag.detail} onSelectCite={onSelectCite} />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

const STREAM_STEPS = [
  { id: "fetch", label: "Quét mã & GitHub Guard" },
  { id: "ai", label: "Giám khảo AI đối chiếu" },
  { id: "verify", label: "Hậu kiểm trích dẫn" },
] as const;

export function ScanStreamPanel({
  stream,
  onCancel,
}: {
  stream: ScanStreamState;
  onCancel: () => void;
}) {
  const [elapsedSec, setElapsedSec] = useState(() =>
    Math.max(0, Math.floor((Date.now() - stream.startedAt) / 1000)),
  );
  const [reasoningOpen, setReasoningOpen] = useState(true);
  const [userToggledReasoning, setUserToggledReasoning] = useState(false);

  useEffect(() => {
    setElapsedSec(Math.max(0, Math.floor((Date.now() - stream.startedAt) / 1000)));
    const id = window.setInterval(() => {
      setElapsedSec(Math.max(0, Math.floor((Date.now() - stream.startedAt) / 1000)));
    }, 1000);
    return () => window.clearInterval(id);
  }, [stream.startedAt]);

  useEffect(() => {
    setReasoningOpen(true);
    setUserToggledReasoning(false);
  }, [stream.startedAt]);

  useEffect(() => {
    if (!userToggledReasoning && stream.contentText.length > 0) {
      setReasoningOpen(false);
    }
  }, [stream.contentText.length, userToggledReasoning]);

  const activeStepIndex =
    stream.stageStep === "verify" ? 2 : stream.stageStep === "ai" || stream.preflight ? 1 : 0;

  const preflight = stream.preflight;
  const checks = preflight ? normalizeChecks(preflight.checks, preflight.source_type) : [];

  return (
    <div className="tabpanel-inner mx-auto w-full max-w-[1040px] space-y-5" aria-live="polite">
      {/* Live Timeline Bar */}
      <Card className="bg-card shadow-none border-primary/35">
        <CardContent className="p-4 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <span className="stream-dot shrink-0" aria-hidden="true" />
              <strong className="text-sm text-foreground truncate">
                {stream.stageLabel || `Đang quét ${stream.target}…`}
              </strong>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Badge variant="default" className="font-mono tabular-nums">
                {elapsedSec}s
              </Badge>
              <Button type="button" variant="outline" size="sm" onClick={onCancel}>
                <X aria-hidden="true" className="h-3.5 w-3.5" />
                Huỷ
              </Button>
            </div>
          </div>

          <ol className="m-0 grid list-none grid-cols-1 gap-2 p-0 sm:grid-cols-3">
            {STREAM_STEPS.map((st, idx) => {
              const isDone = idx < activeStepIndex;
              const isCurrent = idx === activeStepIndex;
              return (
                <li
                  key={st.id}
                  className={`flex items-center gap-2 rounded-md border px-2.5 py-1.5 text-xs ${
                    isCurrent
                      ? "border-primary/50 bg-primary/10 font-semibold text-foreground"
                      : isDone
                        ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                        : "border-border bg-muted/40 text-muted-foreground"
                  }`}
                >
                  {isDone ? (
                    <CheckCircle2 aria-hidden="true" className="h-3.5 w-3.5 shrink-0" />
                  ) : isCurrent ? (
                    <span className="stream-dot shrink-0" aria-hidden="true" />
                  ) : (
                    <span className="inline-block h-2 w-2 rounded-full bg-muted-foreground/40 shrink-0" />
                  )}
                  <span>
                    {idx + 1}. {st.label}
                  </span>
                </li>
              );
            })}
          </ol>
        </CardContent>
      </Card>

      {/* Instant deterministic preflight results */}
      {preflight ? (
        <>
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <strong className="text-sm text-foreground">{preflight.source_label}</strong>
            <span>
              Chế độ:{" "}
              <strong className="text-foreground">{preflight.mode === "team" ? "Nhóm" : "Cá nhân"}</strong>
            </span>
            {preflight.commit_sha ? (
              <span>
                Commit: <code className="font-mono">{preflight.commit_sha.slice(0, 7)}</code>
              </span>
            ) : null}
            {typeof preflight.present_files_count === "number" ? (
              <span>({preflight.present_files_count} file)</span>
            ) : null}
          </div>

          <ChecksGrid checks={checks} />

          {preflight.missing_required && preflight.missing_required.length > 0 ? (
            <Alert variant="info" role="status">
              <strong>HAX G10 — Thiếu file bắt buộc:</strong>{" "}
              {preflight.missing_required.map((fname, idx) => (
                <span key={fname}>
                  {idx > 0 ? ", " : ""}
                  <code className="font-mono text-xs">{fname}</code>
                </span>
              ))}
            </Alert>
          ) : null}

          <HardFlagsSection hardFlags={preflight.hard_flags} />
        </>
      ) : null}

      {/* Collapsible AI reasoning stream */}
      {stream.reasoningText ? (
        <details
          className="disclosure"
          open={reasoningOpen}
          onToggle={(e) => {
            setUserToggledReasoning(true);
            setReasoningOpen(e.currentTarget.open);
          }}
        >
          <summary>
            Suy luận của Giám khảo AI ({stream.reasoningText.length.toLocaleString("vi-VN")} ký tự
            {stream.contentText ? " · đã xong, đang xuất báo cáo" : " · đang phân tích…"})
          </summary>
          <pre className="m-0 max-h-56 overflow-y-auto scroller whitespace-pre-wrap break-words rounded border border-border/70 bg-card/80 p-3 font-mono text-xs leading-relaxed text-muted-foreground">
            {stream.reasoningText}
          </pre>
        </details>
      ) : null}

      {/* Live Markdown Audit Report */}
      <section aria-labelledby="stream-audit-heading" className="space-y-2.5">
        <h3 id="stream-audit-heading" className="m-0 flex items-center gap-2 text-sm font-semibold text-foreground">
          <span>Báo cáo đối chiếu Rubric</span>
          <Badge variant="default">Đang stream</Badge>
        </h3>
        <div className="w-full rounded-lg border border-border bg-card p-4 sm:p-5">
          {stream.contentText ? (
            <MarkdownView text={stream.contentText} />
          ) : (
            <p className="m-0 text-sm text-muted-foreground">
              {stream.reasoningText
                ? "Giám khảo AI đang tổng hợp luận điểm trước khi viết báo cáo chính thức…"
                : "Đang chờ token đầu tiên từ Giám khảo AI…"}
            </p>
          )}
        </div>
      </section>
    </div>
  );
}

type AuditSubTab = "sec1" | "sec2" | "sec3" | "all";

export function AuditPanel({ session, diff, onSelectCite, onGoToViva }: AuditPanelProps) {
  const checks = normalizeChecks(session.checks, session.source_type);
  const parsed = useMemo(() => parseAuditReport(session.audit_output), [session.audit_output]);
  const [subTab, setSubTab] = useState<AuditSubTab>("sec1");

  useEffect(() => {
    setSubTab("sec1");
  }, [session.scan_id]);

  const safetyCount = (session.hard_flags?.length ?? 0) + (session.missing_required?.length ?? 0);

  return (
    <div className="tabpanel-inner mx-auto w-full max-w-[1040px] space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="m-0 text-base sm:text-lg font-semibold tracking-tight text-foreground break-words">
            Hồ sơ kiểm toán: {session.source_label}
          </h2>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span>
              Chế độ: <strong className="text-foreground">{session.mode === "team" ? "Nhóm" : "Cá nhân"}</strong>
            </span>
            {session.commit_sha ? (
              <span>
                Commit: <code className="font-mono">{session.commit_sha.slice(0, 7)}</code>
              </span>
            ) : null}
            <span className="break-all text-[11px] sm:text-xs">
              Phiên: <code className="font-mono">{session.scan_id}</code>
            </span>
          </div>
        </div>

        {diff && diff.previous_scan_id ? (
          <Alert variant="info" className="w-auto py-1.5 px-3 text-xs">
            So với <code className="font-mono">{diff.previous_scan_id.slice(-10)}</code>:{" "}
            <strong>
              {typeof diff.flags_delta === "number"
                ? diff.flags_delta < 0
                  ? `Giảm ${Math.abs(diff.flags_delta)} lỗi`
                  : diff.flags_delta > 0
                    ? `Tăng +${diff.flags_delta} lỗi`
                    : "Không đổi"
                : diff.summary || "Đã đối chiếu"}
            </strong>
          </Alert>
        ) : null}
      </div>

      {/* 4 GitHub Live Guard status cards */}
      <ChecksGrid checks={checks} onSelectCite={onSelectCite} />

      {/* Segmented Sub-tabs for easier scanning */}
      <div
        className="grid grid-cols-2 gap-1.5 border-b border-border pb-3 sm:flex sm:flex-wrap sm:items-center sm:gap-2"
        role="group"
        aria-label="Phân mục báo cáo kiểm toán"
      >
        <Button
          type="button"
          size="sm"
          className="h-auto min-h-[38px] py-1.5 px-2 text-xs whitespace-normal text-center leading-tight sm:h-8 sm:min-h-0 sm:px-3 sm:whitespace-nowrap inline-flex items-center justify-center gap-1.5"
          variant={subTab === "sec1" ? "default" : "secondary"}
          onClick={() => setSubTab("sec1")}
        >
          <span>(1) Lỗi cứng &amp; An toàn</span>
          {safetyCount > 0 ? (
            <Badge
              variant={subTab === "sec1" ? "default" : "destructive"}
              className={
                subTab === "sec1"
                  ? "px-1.5 py-0 text-[11px] leading-4 bg-primary-foreground/20 text-primary-foreground border-transparent"
                  : "px-1.5 py-0 text-[11px] leading-4"
              }
            >
              {safetyCount}
            </Badge>
          ) : null}
        </Button>

        <Button
          type="button"
          size="sm"
          className="h-auto min-h-[38px] py-1.5 px-2 text-xs whitespace-normal text-center leading-tight sm:h-8 sm:min-h-0 sm:px-3 sm:whitespace-nowrap"
          variant={subTab === "sec2" ? "default" : "secondary"}
          onClick={() => setSubTab("sec2")}
        >
          (2) Đối chiếu &amp; Lập luận
        </Button>

        <Button
          type="button"
          size="sm"
          className="h-auto min-h-[38px] py-1.5 px-2 text-xs whitespace-normal text-center leading-tight sm:h-8 sm:min-h-0 sm:px-3 sm:whitespace-nowrap"
          variant={subTab === "sec3" ? "default" : "secondary"}
          onClick={() => setSubTab("sec3")}
        >
          (3) Đạt / Chưa kiểm (G10)
        </Button>

        <Button
          type="button"
          size="sm"
          className="h-auto min-h-[38px] py-1.5 px-2 text-xs whitespace-normal text-center leading-tight sm:h-8 sm:min-h-0 sm:px-3 sm:whitespace-nowrap"
          variant={subTab === "all" ? "default" : "outline"}
          onClick={() => setSubTab("all")}
        >
          Xem toàn bộ
        </Button>
      </div>

      {/* Sub-tab 1 or All: Missing required + Hard flags */}
      {(subTab === "sec1" || subTab === "all") && (
        <div className="space-y-4">
          {session.missing_required && session.missing_required.length > 0 ? (
            <Alert variant="info" role="status">
              <strong>HAX G10 — Thiếu file bắt buộc:</strong>{" "}
              {session.missing_required.map((fname, idx) => (
                <span key={fname}>
                  {idx > 0 ? ", " : ""}
                  <code className="font-mono text-xs">{fname}</code>
                </span>
              ))}
            </Alert>
          ) : null}

          <HardFlagsSection hardFlags={session.hard_flags} onSelectCite={onSelectCite} />
        </div>
      )}

      {/* AI Audit Section Content */}
      <section aria-labelledby="ai-audit-heading" className="space-y-2.5">
        <h3 id="ai-audit-heading" className="m-0 text-sm font-semibold text-foreground">
          {subTab === "sec1"
            ? "Phân tích lỗi cứng & an toàn"
            : subTab === "sec2"
              ? "Đối chiếu chéo bằng chứng & quy định repo"
              : subTab === "sec3"
                ? "Tổng hợp hạng mục Đạt / Chưa kiểm (G10)"
                : "Báo cáo đối chiếu Rubric đầy đủ"}
        </h3>
        <div className="w-full rounded-lg border border-border bg-card p-4 sm:p-5">
          {subTab === "sec1" ? (
            parsed.section1 ? (
              <MarkdownView text={parsed.section1} onSelectCite={onSelectCite} />
            ) : (
              <p className="m-0 text-sm text-muted-foreground">Không có ghi chú thêm ở mục (1).</p>
            )
          ) : subTab === "sec2" ? (
            parsed.section2 ? (
              <MarkdownView text={parsed.section2} onSelectCite={onSelectCite} />
            ) : (
              <p className="m-0 text-sm text-muted-foreground">
                Chưa tách được mục (2) từ báo cáo này — bạn có thể bấm <strong>Xem toàn bộ</strong>.
              </p>
            )
          ) : subTab === "sec3" ? (
            parsed.section3 ? (
              <MarkdownView text={parsed.section3} onSelectCite={onSelectCite} />
            ) : (
              <p className="m-0 text-sm text-muted-foreground">
                Chưa tách được mục (3) từ báo cáo này — bạn có thể bấm <strong>Xem toàn bộ</strong>.
              </p>
            )
          ) : (
            <MarkdownView text={parsed.fullWithoutViva || session.audit_output} onSelectCite={onSelectCite} />
          )}
        </div>
      </section>

      {/* Redirect CTA to Tab 2 (Viva) instead of dumping Section (4) inline */}
      {onGoToViva ? (
        <Card className="bg-muted/35 shadow-none">
          <CardContent className="flex flex-wrap items-center justify-between gap-3 p-4">
            <div className="space-y-0.5">
              <strong className="block text-sm text-foreground">
                {parsed.vivaQuestions.length > 0
                  ? `Có ${parsed.vivaQuestions.length} câu hỏi vặn phản biện từ lần soi này`
                  : "Luyện vấn đáp phản biện & chấm mức hiểu Bloom L0–L6"}
              </strong>
              <p className="m-0 text-xs text-muted-foreground">
                Câu hỏi phản biện đã được chuyển sang tab Vấn đáp để bạn trả lời từng câu và nâng bậc kiến thức.
              </p>
            </div>
            <Button
              type="button"
              onClick={() => onGoToViva(parsed.vivaQuestions)}
              className="w-full sm:w-auto justify-center"
            >
              <MessageSquare aria-hidden="true" className="h-3.5 w-3.5" />
              {parsed.vivaQuestions.length > 0
                ? `Chuyển sang Vấn đáp (${parsed.vivaQuestions.length} câu gợi ý)`
                : "Chuyển sang Vấn đáp"}
            </Button>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
