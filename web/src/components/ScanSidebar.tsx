import { useEffect, useState } from "react";
import { LogOut, Monitor, Moon, Sun } from "lucide-react";
import { Badge } from "@/components/ui/badge.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Separator } from "@/components/ui/separator.tsx";
import { cn } from "@/lib/utils.ts";
import type { MeResponse, ScanSessionSummary, ThemeMode } from "@/types.ts";

interface ScanSidebarProps {
  sessions: ScanSessionSummary[];
  activeScanId: string | null;
  onSelectSession: (scanId: string) => void;
  loading: boolean;
  me: MeResponse | null;
  onNavigate: (path: string) => void;
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

function getSystemThemeLabel(): "Sáng" | "Tối" {
  if (typeof window === "undefined" || !window.matchMedia) return "Sáng";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "Tối" : "Sáng";
}

function readStoredTheme(): ThemeMode {
  try {
    const val = localStorage.getItem("color-scheme");
    if (val === "light" || val === "dark") return val;
  } catch {
    // ignore storage access issues
  }
  return "system";
}

function applyThemeMeta(mode: ThemeMode) {
  const meta = document.querySelector<HTMLMetaElement>('meta[name="color-scheme"]');
  if (meta) {
    meta.content = mode === "system" ? "light dark" : mode;
  }
}

function renderDeltaBadge(delta?: number | null) {
  if (delta === undefined || delta === null) return null;
  if (delta < 0) return <Badge variant="success">{delta} lỗi</Badge>;
  if (delta > 0) return <Badge variant="destructive">+{delta} lỗi</Badge>;
  return <Badge variant="secondary">0 đổi</Badge>;
}

export function ScanSidebar({
  sessions,
  activeScanId,
  onSelectSession,
  loading,
  me,
  onNavigate,
}: ScanSidebarProps) {
  const [theme, setTheme] = useState<ThemeMode>(() => readStoredTheme());
  const [sysLabel, setSysLabel] = useState<"Sáng" | "Tối">(() => getSystemThemeLabel());

  useEffect(() => {
    applyThemeMeta(theme);
  }, [theme]);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onMqChange = () => setSysLabel(mq.matches ? "Tối" : "Sáng");
    mq.addEventListener("change", onMqChange);

    const onStorage = (e: StorageEvent) => {
      if (e.key === "color-scheme") {
        setTheme(readStoredTheme());
      }
    };
    window.addEventListener("storage", onStorage);

    return () => {
      mq.removeEventListener("change", onMqChange);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  const handleSelectTheme = (next: ThemeMode) => {
    setTheme(next);
    try {
      if (next === "system") {
        localStorage.removeItem("color-scheme");
      } else {
        localStorage.setItem("color-scheme", next);
      }
    } catch {
      // ignore storage errors
    }
    applyThemeMeta(next);
  };

  return (
    <aside
      className="order-last lg:order-first flex flex-col border-t lg:border-t-0 lg:border-r border-border bg-card"
      aria-label="Thanh điều hướng và lịch sử phiên quét"
    >
      {/* Seamless h-14 Brand header aligned with TopBar on desktop */}
      <div className="hidden h-14 shrink-0 items-center border-b border-border px-4 lg:flex">
        <a
          href="/"
          className="flex min-w-0 items-center gap-2.5 text-foreground no-underline"
          onClick={(e) => {
            e.preventDefault();
            onNavigate("/");
          }}
        >
          <img src="/repoksv-logo-120.png" alt="" className="brand-logo" width={32} height={32} />
          <div className="min-w-0">
            <div className="text-sm font-bold leading-tight tracking-tight">RepoKSV</div>
            <div className="truncate text-[11px] text-muted-foreground">Kiểm Sát Viên · Free2Play</div>
          </div>
        </a>
      </div>

      {/* Sidebar body */}
      <div className="flex flex-1 flex-col gap-3 p-3.5 lg:sticky lg:top-0 lg:max-h-[calc(100vh-3.5rem)]">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-semibold text-muted-foreground">Phiên quét gần đây</span>
          <Badge variant="outline">{sessions.length}</Badge>
        </div>

        <div className="scroller min-h-0 flex-1 overflow-y-auto max-h-56 lg:max-h-none">
          {loading && sessions.length === 0 ? (
            <p className="text-xs text-muted-foreground m-0">Đang tải…</p>
          ) : sessions.length === 0 ? (
            <p className="text-xs text-muted-foreground m-0">
              Chưa có phiên quét. Chọn <code>S01–S30</code> hoặc dán link GitHub.
            </p>
          ) : (
            <ul className="m-0 grid list-none gap-1.5 p-0">
              {sessions.map((s) => {
                const isCurrent = s.scan_id === activeScanId;
                const flagCount = typeof s.hard_flags_count === "number" ? s.hard_flags_count : 0;
                return (
                  <li key={s.scan_id}>
                    <button
                      type="button"
                      aria-current={isCurrent ? "true" : undefined}
                      onClick={() => onSelectSession(s.scan_id)}
                      className={cn(
                        "session-btn w-full rounded-md border px-2.5 py-2 text-left cursor-pointer touch-manipulation transition-[transform,border-color] duration-150 ease-[cubic-bezier(0.23,1,0.32,1)] active:scale-[0.99]",
                        isCurrent
                          ? "border-primary border-l-4 bg-accent text-foreground"
                          : "border-border bg-background hover:border-primary/60 text-foreground",
                      )}
                    >
                      <div className="flex items-center justify-between gap-1.5">
                        <span className="inline-flex min-w-0 items-center gap-1.5 text-xs font-semibold">
                          <span
                            aria-hidden="true"
                            className={cn(
                              "h-2 w-2 shrink-0 rounded-full",
                              flagCount > 0 ? "bg-destructive" : "bg-emerald-600 dark:bg-emerald-400",
                            )}
                          />
                          <span className="truncate">{s.source_label}</span>
                        </span>
                        {renderDeltaBadge(s.flags_delta)}
                      </div>
                      <div className="mt-1 flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
                        <span>
                          {s.mode === "team" ? "Nhóm" : "Cá nhân"}
                          {s.commit_sha ? ` · ${s.commit_sha.slice(0, 7)}` : ""}
                        </span>
                        <span className="tabular-nums">{formatTime(s.created_at)}</span>
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <Separator />

        {/* Footer: 3-state Theme Switcher + Google Auth */}
        <div className="flex flex-col gap-2.5">
          <fieldset
            aria-label="Chọn giao diện sáng tối"
            className="grid grid-cols-3 gap-1 rounded-md border border-border bg-background p-1 m-0"
          >
            <button
              type="button"
              aria-pressed={theme === "system"}
              onClick={() => handleSelectTheme("system")}
              title={`Hệ thống (${sysLabel})`}
              className={cn(
                "inline-flex items-center justify-center gap-1 whitespace-nowrap rounded px-1 py-1 text-[11px] font-medium cursor-pointer touch-manipulation",
                theme === "system"
                  ? "bg-card text-foreground shadow-2xs border border-border"
                  : "text-muted-foreground hover:text-foreground border border-transparent",
              )}
            >
              <Monitor aria-hidden="true" className="h-3 w-3 shrink-0" />
              <span>Hệ thống</span>
            </button>
            <button
              type="button"
              aria-pressed={theme === "light"}
              onClick={() => handleSelectTheme("light")}
              className={cn(
                "inline-flex items-center justify-center gap-1 whitespace-nowrap rounded px-1 py-1 text-[11px] font-medium cursor-pointer touch-manipulation",
                theme === "light"
                  ? "bg-card text-foreground shadow-2xs border border-border"
                  : "text-muted-foreground hover:text-foreground border border-transparent",
              )}
            >
              <Sun aria-hidden="true" className="h-3 w-3 shrink-0" />
              <span>Sáng</span>
            </button>
            <button
              type="button"
              aria-pressed={theme === "dark"}
              onClick={() => handleSelectTheme("dark")}
              className={cn(
                "inline-flex items-center justify-center gap-1 whitespace-nowrap rounded px-1 py-1 text-[11px] font-medium cursor-pointer touch-manipulation",
                theme === "dark"
                  ? "bg-card text-foreground shadow-2xs border border-border"
                  : "text-muted-foreground hover:text-foreground border border-transparent",
              )}
            >
              <Moon aria-hidden="true" className="h-3 w-3 shrink-0" />
              <span>Tối</span>
            </button>
          </fieldset>

          {me?.authenticated && me.user ? (
            <div className="flex items-center justify-between gap-2 rounded-md border border-border bg-background px-2.5 py-1.5 text-xs">
              <div className="flex min-w-0 items-center gap-2">
                {me.user.picture_url && (
                  <img
                    src={me.user.picture_url}
                    alt={me.user.display_name || me.user.email}
                    className="h-6 w-6 rounded-full object-cover shrink-0"
                    width={24}
                    height={24}
                    referrerPolicy="no-referrer"
                  />
                )}
                <span className="truncate font-medium" title={me.user.email}>
                  {me.user.display_name || me.user.email}
                </span>
              </div>
              <form method="POST" action="/auth/logout" className="m-0 shrink-0">
                <Button type="submit" variant="ghost" size="sm" className="h-7 px-2 text-xs">
                  <LogOut aria-hidden="true" className="h-3.5 w-3.5" />
                  Đăng xuất
                </Button>
              </form>
            </div>
          ) : (
            <div className="flex flex-col gap-1.5">
              {me?.guest_demo ? (
                <div className="flex items-center justify-between text-[11px] text-muted-foreground px-1">
                  <span>Chế độ khách</span>
                  <Badge variant="secondary">
                    Demo{typeof me.guest_remaining === "number" ? ` (${me.guest_remaining})` : ""}
                  </Badge>
                </div>
              ) : null}
              <a
                href="/auth/google"
                className="inline-flex h-8 w-full items-center justify-center gap-2 rounded-md border border-border bg-background px-3 text-xs font-medium text-foreground no-underline hover:bg-accent"
              >
                <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M21.8 12.23c0-.68-.06-1.36-.18-2.02H12v3.83h5.5a4.7 4.7 0 0 1-2.04 3.09v2.56h3.3c1.93-1.78 3.04-4.4 3.04-7.46ZM12 22c2.75 0 5.06-.91 6.75-2.47l-3.3-2.56c-.91.61-2.08.97-3.45.97-2.65 0-4.9-1.79-5.7-4.2H2.89v2.64A10 10 0 0 0 12 22ZM6.3 13.74A5.98 5.98 0 0 1 6 12c0-.6.1-1.19.3-1.74V7.62H2.89A10 10 0 0 0 2 12c0 1.61.39 3.14 1.09 4.38l3.21-2.64ZM12 6.06c1.5 0 2.84.52 3.9 1.53l2.92-2.92C17.05 2.99 14.74 2 12 2a10 10 0 0 0-9.11 5.62l3.41 2.64C7.1 7.85 9.35 6.06 12 6.06Z"
                  />
                </svg>
                Đăng nhập Google
              </a>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
