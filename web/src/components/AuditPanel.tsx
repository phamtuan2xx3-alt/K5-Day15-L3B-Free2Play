import type { GitHubCheckStatus, ScanDiffSummary, ScanSessionDetail } from "../types.ts";
import { CiteText } from "./CiteText.tsx";

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
          : `${item.desc} (Kiểm tra trên hồ sơ mẫu offline).`,
    };
  });
}

function statusStampClass(status: string): string {
  const s = status.toLowerCase();
  if (s === "pass" || s === "ok" || s === "clean") return "stamp stamp-teal";
  if (s === "fail" || s === "error" || s === "flagged") return "stamp stamp-crimson";
  if (s === "warn" || s === "g10" || s === "unknown") return "stamp stamp-warn";
  return "stamp stamp-navy";
}

function statusLabel(status: string): string {
  const s = status.toLowerCase();
  if (s === "pass" || s === "ok" || s === "clean") return "ĐẠT";
  if (s === "fail" || s === "error" || s === "flagged") return "LỖI CỨNG";
  if (s === "warn" || s === "g10" || s === "unknown") return "G10";
  return status.toUpperCase();
}

export function AuditPanel({ session, diff, onSelectCite }: AuditPanelProps) {
  const checks = normalizeChecks(session.checks, session.source_type);

  return (
    <div className="tabpanel-inner">
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: "0.75rem", marginBottom: "1rem" }}>
        <div>
          <h2 style={{ margin: "0 0 0.25rem", fontSize: "1.18rem" }}>
            Hồ sơ kiểm toán: {session.source_label}
          </h2>
          <div style={{ fontSize: "0.84rem", color: "var(--ink-muted)", display: "flex", flexWrap: "wrap", gap: "0.6rem" }}>
            <span>Chế độ: <strong>{session.mode === "team" ? "Nhóm" : "Cá nhân"}</strong></span>
            {session.commit_sha ? <span>Commit: <code>{session.commit_sha.slice(0, 7)}</code></span> : null}
            <span>Mã phiên: <code>{session.scan_id}</code></span>
          </div>
        </div>

        {diff && diff.previous_scan_id ? (
          <div className="alert alert-info" style={{ margin: 0, padding: "0.45rem 0.75rem" }}>
            So với phiên trước (<code>{diff.previous_scan_id.slice(-12)}</code>):{" "}
            <strong>
              {typeof diff.flags_delta === "number"
                ? diff.flags_delta < 0
                  ? `Giảm ${Math.abs(diff.flags_delta)} lỗi cứng`
                  : diff.flags_delta > 0
                    ? `Tăng +${diff.flags_delta} lỗi cứng`
                    : "Không đổi số lỗi cứng"
                : diff.summary || "Đã đối chiếu"}
            </strong>
          </div>
        ) : null}
      </div>

      {/* 4 the trang thai GitHub song */}
      <div className="status-grid" role="region" aria-label="4 lớp kiểm tra GitHub Live Guard">
        {checks.map((chk) => (
          <div key={chk.key} className="status-card">
            <div className="status-card-head">
              <span className="status-card-title">{chk.label || chk.key}</span>
              <span className={statusStampClass(chk.status)}>{statusLabel(chk.status)}</span>
            </div>
            <p style={{ margin: 0, fontSize: "0.84rem", color: "var(--ink-muted)" }}>
              <CiteText text={chk.detail} onSelectCite={onSelectCite} />
            </p>
          </div>
        ))}
      </div>

      {/* File thieu bat buoc (HAX G10) */}
      {session.missing_required && session.missing_required.length > 0 ? (
        <div className="alert alert-info" role="status">
          <strong>CHƯA KIỂM ĐƯỢC (HAX G10) — Thiếu file bắt buộc:</strong>{" "}
          {session.missing_required.map((fname, idx) => (
            <span key={fname}>
              {idx > 0 ? ", " : ""}
              <code>{fname}</code>
            </span>
          ))}
        </div>
      ) : null}

      {/* Danh sach loi cung */}
      <section aria-labelledby="hard-flags-heading" style={{ marginBottom: "1.25rem" }}>
        <h3 id="hard-flags-heading" style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>
          Lỗi cứng từ bộ quét code ({session.hard_flags.length})
        </h3>
        {session.hard_flags.length === 0 ? (
          <div className="alert alert-ok">Không phát hiện lỗi cứng từ bộ quét code.</div>
        ) : (
          <ul className="flags-list">
            {session.hard_flags.map((flag, idx) => {
              const lineNum = Number.parseInt(String(flag.line), 10) || 1;
              return (
                <li key={`${flag.rule_id}-${flag.file}-${idx}`} className="flag-row">
                  <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                    <span className="stamp stamp-crimson">{flag.rule_id}</span>
                    <button
                      type="button"
                      className="cite-chip"
                      onClick={() => onSelectCite(flag.file, lineNum)}
                    >
                      {flag.file}:L{String(lineNum).padStart(2, "0")}
                    </button>
                  </div>
                  <div>
                    <CiteText text={flag.detail} onSelectCite={onSelectCite} />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {/* Bao cao doi chieu rubric AI + chip file:Lxx */}
      <section aria-labelledby="ai-audit-heading">
        <h3 id="ai-audit-heading" style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>
          Báo cáo đối chiếu chéo Rubric (bấm chip <code>file:Lxx</code> để mở đúng dòng nguồn)
        </h3>
        <div className="audit-prose">
          <CiteText text={session.audit_output} onSelectCite={onSelectCite} />
        </div>
      </section>
    </div>
  );
}
