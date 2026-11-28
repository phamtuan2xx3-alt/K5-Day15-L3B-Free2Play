import { useEffect, useState } from "react";
import { LogOut, Monitor, Moon, PanelLeftClose, PanelLeftOpen, Sun, User } from "lucide-react";
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
  collapsed: boolean;
  onToggleCollapse: () => void;
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
  if (delta < 0) return <Badge variant="success" className="shrink-0 text-[10px] px-1.5 py-0">{delta} lỗi</Badge>;
  if (delta > 0) return <Badge variant="destructive" className="shrink-0 text-[10px] px-1.5 py-0">+{delta} lỗi</Badge>;
  return null;
}

function formatCompactSessionTag(label: string): string {
  const raw = (label || "").trim();
  if (/^S\d{2}$/i.test(raw)) return raw.toUpperCase();
  const repoPart = raw.includes("/") ? raw.split("/").pop() || raw : raw;
  const cleaned = repoPart.replace(/[^A-Za-z0-9]/g, "");
  return (cleaned.slice(0, 2) || "RP").toUpperCase();
}

export function BrandWordmark() {
  return (
    <span className="inline-flex items-baseline text-[19px] sm:text-[20px] font-extrabold tracking-[-0.03em] leading-none select-none">
      <span className="text-foreground">Repo</span>
      <span className="text-primary">KSV</span>
    </span>
  );
}

export function ScanSidebar({
  sessions,
  activeScanId,
  onSelectSession,
  loading,
  me,
  onNavigate,
  collapsed,
  onToggleCollapse,
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

  const handleCycleTheme = () => {
    const order: ThemeMode[] = ["system", "light", "dark"];
    const next = order[(order.indexOf(theme) + 1) % order.length];
    handleSelectTheme(next);
  };

  return (
    <aside
      className="order-last lg:order-first flex min-w-0 flex-col overflow-x-hidden border-t lg:border-t-0 lg:border-r border-border bg-card lg:h-full lg:min-h-0 lg:overflow-hidden"
      aria-label="Thanh điều hướng và lịch sử phiên quét"
    >
      {/* Desktop Header: Stylized Logo + Collapse/Expand Toggle */}
      <div
        className={cn(
          "hidden h-14 shrink-0 items-center border-b border-border lg:flex",
          collapsed ? "justify-center px-2" : "justify-between gap-2 px-3.5",
        )}
      >
        {collapsed ? (
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label="Mở rộng thanh bên"
            title="Mở rộng thanh bên"
            className="group relative flex h-9 w-9 items-center justify-center rounded-md border border-transparent hover:border-border hover:bg-accent cursor-pointer touch-manipulation transition-[background-color,color,transform] duration-150 ease-[cubic-bezier(0.23,1,0.32,1)] active:scale-95"
          >
            <img
              src="/repoksv-logo-120.png"
              alt="RepoKSV"
              className="brand-logo transition-opacity duration-150 group-hover:opacity-0"
              width={28}
              height={28}
            />
            <PanelLeftOpen
              aria-hidden="true"
              className="absolute h-4 w-4 text-foreground opacity-0 transition-opacity duration-150 group-hover:opacity-100"
            />
          </button>
        ) : (
          <>
            <a
              href="/"
              className="flex min-w-0 items-center gap-2.5 whitespace-nowrap text-foreground no-underline"
              onClick={(e) => {
                e.preventDefault();
                onNavigate("/");
              }}
            >
              <img src="/repoksv-logo-120.png" alt="" className="brand-logo" width={32} height={32} />
              <BrandWordmark />
            </a>
            <button
              type="button"
              onClick={onToggleCollapse}
              aria-label="Thu gọn thanh bên"
              title="Thu gọn thanh bên"
              className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground cursor-pointer touch-manipulation transition-[background-color,color,transform] duration-150 ease-[cubic-bezier(0.23,1,0.32,1)] active:scale-95"
            >
              <PanelLeftClose aria-hidden="true" className="h-4 w-4" />
            </button>
          </>
        )}
      </div>

      {/* Sidebar body */}
      <div
        key={collapsed ? "rail" : "full"}
        className={cn(
          "sidebar-fade flex min-h-0 min-w-0 flex-1 flex-col gap-3",
          collapsed ? "lg:items-center p-2" : "p-3",
        )}
      >
        {!collapsed ? (
          <div className="flex min-w-0 items-center justify-between gap-2 whitespace-nowrap px-1">
            <span className="truncate text-xs font-semibold text-muted-foreground">Phiên quét gần đây</span>
            <Badge variant="outline" className="shrink-0 text-[11px] tabular-nums">
              {sessions.length}
            </Badge>
          </div>
        ) : null}

        <div className="scroller min-h-0 min-w-0 w-full flex-1 overflow-y-auto overflow-x-hidden max-h-56 lg:max-h-none">
          {loading && sessions.length === 0 ? (
            <p className="text-xs text-muted-foreground m-0 px-1">{collapsed ? "…" : "Đang tải…"}</p>
          ) : sessions.length === 0 ? (
            !collapsed ? (
              <p className="text-xs text-muted-foreground m-0 px-1">
                Chưa có phiên quét. Chọn <code>S01–S30</code> hoặc dán link GitHub.
              </p>
            ) : null
          ) : (
            <ul className={cn("m-0 flex min-w-0 list-none flex-col p-0", collapsed ? "items-center gap-1.5" : "gap-1")}>
              {sessions.map((s) => {
                const isCurrent = s.scan_id === activeScanId;
                const flagCount = typeof s.hard_flags_count === "number" ? s.hard_flags_count : 0;

                if (collapsed) {
                  return (
                    <li key={s.scan_id} className="w-full flex justify-center">
                      <button
                        type="button"
                        aria-current={isCurrent ? "true" : undefined}
                        title={s.source_label}
                        onClick={() => onSelectSession(s.scan_id)}
                        className={cn(
                          "session-btn relative flex h-9 w-9 items-center justify-center rounded-md border font-mono text-[11px] font-bold cursor-pointer touch-manipulation transition-colors",
                          isCurrent
                            ? "border-primary bg-accent text-foreground"
                            : "border-border bg-background text-muted-foreground hover:border-primary/60 hover:text-foreground",
                        )}
                      >
                        <span
                          aria-hidden="true"
                          className={cn(
                            "absolute right-1 top-1 h-1.5 w-1.5 rounded-full",
                            flagCount > 0 ? "bg-destructive" : "bg-emerald-600 dark:bg-emerald-400",
                          )}
                        />
                        {formatCompactSessionTag(s.source_label)}
                      </button>
                    </li>
                  );
                }

                return (
                  <li key={s.scan_id} className="min-w-0 w-full">
                    <button
                      type="button"
                      aria-current={isCurrent ? "true" : undefined}
                      title={s.source_label}
                      onClick={() => onSelectSession(s.scan_id)}
                      className={cn(
                        "session-btn group block w-full min-w-0 overflow-hidden rounded-md border px-2.5 py-2 text-left cursor-pointer touch-manipulation transition-colors",
                        isCurrent
                          ? "border-primary/45 bg-accent text-foreground"
                          : "border-transparent bg-transparent hover:bg-accent/60 text-foreground/90",
                      )}
                    >
                      <div className="flex min-w-0 items-center gap-2">
                        <span
                          aria-hidden="true"
                          className={cn(
                            "h-2 w-2 shrink-0 rounded-full",
                            flagCount > 0 ? "bg-destructive" : "bg-emerald-600 dark:bg-emerald-400",
                          )}
                        />
                        <span className="block min-w-0 flex-1 truncate text-[13px] font-medium leading-snug">
                          {s.source_label}
                        </span>
                        {renderDeltaBadge(s.flags_delta)}
                      </div>
                      <div className="mt-0.5 flex min-w-0 items-center justify-between gap-2 pl-4 text-[11px] text-muted-foreground">
                        <span className="truncate">
                          {s.mode === "team" ? "Nhóm" : "Cá nhân"}
                          {s.commit_sha ? ` · ${s.commit_sha.slice(0, 7)}` : ""}
                        </span>
                        <span className="shrink-0 tabular-nums">{formatTime(s.created_at)}</span>
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
        {collapsed ? (
          <div className="hidden lg:flex flex-col items-center gap-2">
            <button
              type="button"
              onClick={handleCycleTheme}
              title={`Đổi giao diện (hiện tại: ${theme === "system" ? `Hệ thống - ${sysLabel}` : theme === "light" ? "Sáng" : "Tối"})`}
              aria-label="Đổi giao diện sáng tối"
              className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-background text-foreground hover:bg-accent cursor-pointer touch-manipulation"
            >
              {theme === "dark" ? (
                <Moon aria-hidden="true" className="h-3.5 w-3.5" />
              ) : theme === "light" ? (
                <Sun aria-hidden="true" className="h-3.5 w-3.5" />
              ) : (
                <Monitor aria-hidden="true" className="h-3.5 w-3.5" />
              )}
            </button>
            {me?.authenticated && me.user?.picture_url ? (
              <img
                src={me.user.picture_url}
                alt={me.user.display_name || me.user.email}
                title={me.user.display_name || me.user.email}
                className="h-8 w-8 rounded-full border border-border object-cover"
                width={32}
                height={32}
                referrerPolicy="no-referrer"
              />
            ) : (
              <a
                href="/auth/google"
                title="Đăng nhập Google"
                aria-label="Đăng nhập Google"
                className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-background text-foreground hover:bg-accent no-underline"
              >
                <User aria-hidden="true" className="h-3.5 w-3.5" />
              </a>
            )}
          </div>
        ) : (
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
        )}
      </div>
    </aside>
  );
}
