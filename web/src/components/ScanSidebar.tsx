import type { ScanSessionSummary } from "../types.ts";

interface ScanSidebarProps {
  sessions: ScanSessionSummary[];
  activeScanId: string | null;
  onSelectSession: (scanId: string) => void;
  loading: boolean;
}

function formatTime(iso: string): string {
  try {
    const dt = new Date(iso);
    if (Number.isNaN(dt.getTime())) return iso;
    return new Intl.DateTimeFormat("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
      day: "2-digit",
      month: "2-digit",
    }).format(dt);
  } catch {
    return iso;
  }
}

function renderDeltaBadge(delta?: number | null) {
  if (delta === undefined || delta === null) return null;
  if (delta < 0) {
    return <span className="stamp stamp-teal">{delta} lỗi</span>;
  }
  if (delta > 0) {
    return <span className="stamp stamp-crimson">+{delta} lỗi</span>;
  }
  return <span className="stamp stamp-navy">0 đổi</span>;
}

export function ScanSidebar({
  sessions,
  activeScanId,
  onSelectSession,
  loading,
}: ScanSidebarProps) {
  return (
    <aside className="sidebar" aria-label="Lịch sử phiên quét">
      <div className="sidebar-heading">
        <span>Phiên quét gần đây</span>
        <span className="stamp stamp-navy">{sessions.length}</span>
      </div>

      {loading && sessions.length === 0 ? (
        <p style={{ color: "var(--ink-muted)", fontSize: "0.88rem" }}>Đang tải lịch sử…</p>
      ) : sessions.length === 0 ? (
        <p style={{ color: "var(--ink-muted)", fontSize: "0.88rem" }}>
          Chưa có phiên quét nào. Chọn <code>S01..S30</code> hoặc dán link GitHub ở thanh trên để bắt đầu.
        </p>
      ) : (
        <ul className="session-list scroller">
          {sessions.map((s) => {
            const isCurrent = s.scan_id === activeScanId;
            return (
              <li key={s.scan_id}>
                <button
                  type="button"
                  className="session-btn"
                  aria-current={isCurrent ? "true" : undefined}
                  onClick={() => onSelectSession(s.scan_id)}
                >
                  <div className="session-title-row">
                    <span>{s.source_label}</span>
                    {renderDeltaBadge(s.flags_delta)}
                  </div>
                  <div className="session-meta">
                    <span>
                      {s.mode === "team" ? "Nhóm" : "Cá nhân"}
                      {s.commit_sha ? ` · ${s.commit_sha.slice(0, 7)}` : ""}
                    </span>
                    <span>{formatTime(s.created_at)}</span>
                  </div>
                  {typeof s.hard_flags_count === "number" && (
                    <div className="session-meta">
                      <span>Lỗi cứng: {s.hard_flags_count}</span>
                      <span>{s.source_type === "github" ? "GitHub Live" : "Local"}</span>
                    </div>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </aside>
  );
}
