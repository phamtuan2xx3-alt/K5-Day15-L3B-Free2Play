import { AlertTriangle, CheckCircle2, HelpCircle, ShieldAlert } from "lucide-react";
import { InlineMarkdown, MarkdownView } from "@/components/MarkdownView.tsx";
import { Alert } from "@/components/ui/alert.tsx";
import { Badge } from "@/components/ui/badge.tsx";
import { Card, CardContent, CardHeader } from "@/components/ui/card.tsx";
import type { GitHubCheckStatus, ScanDiffSummary, ScanSessionDetail } from "@/types.ts";

interface AuditPanelProps {
  session: ScanSessionDetail;
  diff: ScanDiffSummary | null;
  onSelectCite: (file: string, line: number) => void;
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

export function AuditPanel({ session, diff, onSelectCite }: AuditPanelProps) {
  const checks = normalizeChecks(session.checks, session.source_type);

  return (
    <div className="tabpanel-inner space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="m-0 text-lg font-semibold tracking-tight text-foreground">
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
            <span>
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
      <div
        className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4"
        role="region"
        aria-label="4 lớp kiểm tra GitHub Live Guard"
      >
        {checks.map((chk) => (
          <Card key={chk.key} className="status-card bg-card shadow-none">
            <CardHeader className="flex-row items-center justify-between gap-2 p-3 pb-1.5">
              <span className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-foreground">
                <StatusIcon status={chk.status} />
                {chk.label || chk.key}
              </span>
              <Badge variant={statusVariant(chk.status)}>{statusLabel(chk.status)}</Badge>
            </CardHeader>
            <CardContent className="p-3 pt-0 text-xs text-muted-foreground leading-relaxed">
              <InlineMarkdown text={chk.detail} onSelectCite={onSelectCite} />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Missing required files (HAX G10) */}
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

      {/* Hard flags */}
      <section aria-labelledby="hard-flags-heading" className="space-y-2.5">
        <h3 id="hard-flags-heading" className="m-0 text-sm font-semibold text-foreground">
          Lỗi cứng ({session.hard_flags.length})
        </h3>
        {session.hard_flags.length === 0 ? (
          <Alert variant="success">Không phát hiện lỗi cứng.</Alert>
        ) : (
          <ul className="m-0 grid list-none gap-2 p-0">
            {session.hard_flags.map((flag, idx) => {
              const lineNum = Number.parseInt(String(flag.line), 10) || 1;
              return (
                <li
                  key={`${flag.rule_id}-${flag.file}-${idx}`}
                  className="rounded-lg border border-destructive/40 border-l-4 border-l-destructive bg-destructive/5 px-3.5 py-2.5 text-sm"
                >
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <Badge variant="destructive">{flag.rule_id}</Badge>
                    <button
                      type="button"
                      className="cite-chip"
                      onClick={() => onSelectCite(flag.file, lineNum)}
                    >
                      {flag.file}:L{String(lineNum).padStart(2, "0")}
                    </button>
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

      {/* AI Audit Report with safe MarkdownView */}
      <section aria-labelledby="ai-audit-heading" className="space-y-2.5">
        <h3 id="ai-audit-heading" className="m-0 text-sm font-semibold text-foreground">
          Báo cáo đối chiếu Rubric
        </h3>
        <div className="rounded-lg border border-border bg-card p-4 sm:p-5 max-w-[78ch]">
          <MarkdownView text={session.audit_output} onSelectCite={onSelectCite} />
        </div>
      </section>
    </div>
  );
}
