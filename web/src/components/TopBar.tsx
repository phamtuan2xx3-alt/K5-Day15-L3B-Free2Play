import { useEffect, useState, type FormEvent } from "react";
import type { MeResponse, SubmissionOption, ThemeMode } from "../types.ts";

interface TopBarProps {
  targetInput: string;
  onTargetInputChange: (val: string) => void;
  submissions: SubmissionOption[];
  scanning: boolean;
  onScan: (target: string, forceRefresh?: boolean) => void;
  me: MeResponse | null;
  onNavigate: (path: string) => void;
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

export function TopBar({
  targetInput,
  onTargetInputChange,
  submissions,
  scanning,
  onScan,
  me,
  onNavigate,
}: TopBarProps) {
  const [theme, setTheme] = useState<ThemeMode>(() => readStoredTheme());
  const [sysLabel, setSysLabel] = useState<"Sáng" | "Tối">(() => getSystemThemeLabel());

  useEffect(() => {
    applyThemeMeta(theme);
  }, [theme]);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onMqChange = () => {
      setSysLabel(mq.matches ? "Tối" : "Sáng");
    };
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
      // ignore storage errors, meta still updated
    }
    applyThemeMeta(next);
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = targetInput.trim();
    if (!trimmed) return;
    onScan(trimmed, false);
  };

  return (
    <header className="topbar">
      <div className="topbar-inner">
        <a
          href="/"
          className="brand-mark"
          onClick={(e) => {
            e.preventDefault();
            onNavigate("/");
          }}
        >
          <img src="/repoksv-logo-120.png" alt="" className="brand-logo" width={34} height={34} />
          <span>
            RepoKSV
            <span className="brand-sub">Kiểm Sát Viên · Free2Play</span>
          </span>
        </a>

        <form className="scan-bar" onSubmit={handleSubmit} aria-label="Quét hồ sơ hoặc link GitHub">
          <label htmlFor="repo-target-input" className="skip-link">
            URL GitHub hoặc mã hồ sơ
          </label>
          <input
            id="repo-target-input"
            name="target"
            type="text"
            autoComplete="off"
            spellCheck={false}
            className="scan-input"
            value={targetInput}
            onChange={(e) => onTargetInputChange(e.target.value)}
            placeholder="https://github.com/owner/repo hoặc S01–S30…"
          />

          <select
            aria-label="Chọn nhanh hồ sơ mẫu S01 đến S30"
            className="sample-select"
            value={/^S\d{2}$/i.test(targetInput.trim()) ? targetInput.trim().toUpperCase() : ""}
            onChange={(e) => {
              const val = e.target.value;
              if (val) {
                onTargetInputChange(val);
                onScan(val, false);
              }
            }}
          >
            <option value="">Mẫu S01–S30…</option>
            {submissions.map((sub) => (
              <option key={sub.id} value={sub.id}>
                {sub.id}
                {sub.title || sub.label ? ` — ${sub.title || sub.label}` : ""}
              </option>
            ))}
          </select>

          <button type="submit" className="btn btn-primary" disabled={scanning || !targetInput.trim()}>
            {scanning ? "Đang quét…" : "Quét hồ sơ"}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            disabled={scanning || !targetInput.trim()}
            onClick={() => onScan(targetInput.trim(), true)}
            title="Bỏ qua cache và kiểm tra lại trực tiếp"
          >
            Quét lại
          </button>
        </form>

        <div className="topbar-controls">
          <fieldset className="theme-fieldset" aria-label="Chọn giao diện sáng tối">
            <button
              type="button"
              className="theme-btn"
              aria-pressed={theme === "system"}
              onClick={() => handleSelectTheme("system")}
              title={`Theo hệ thống (Hiện đang ${sysLabel})`}
            >
              Hệ thống ({sysLabel})
            </button>
            <button
              type="button"
              className="theme-btn"
              aria-pressed={theme === "light"}
              onClick={() => handleSelectTheme("light")}
            >
              Sáng
            </button>
            <button
              type="button"
              className="theme-btn"
              aria-pressed={theme === "dark"}
              onClick={() => handleSelectTheme("dark")}
            >
              Tối
            </button>
          </fieldset>

          {me?.authenticated && me.user ? (
            <div className="auth-pill">
              {me.user.picture_url && (
                <img
                  src={me.user.picture_url}
                  alt={me.user.display_name || me.user.email}
                  className="auth-avatar"
                  width={24}
                  height={24}
                  referrerPolicy="no-referrer"
                />
              )}
              <span title={me.user.email}>{me.user.display_name || me.user.email}</span>
              <form method="POST" action="/auth/logout" style={{ margin: 0 }}>
                <button type="submit" className="btn btn-secondary" style={{ padding: "0.24rem 0.55rem", fontSize: "0.78rem" }}>
                  Đăng xuất
                </button>
              </form>
            </div>
          ) : (
            <div className="auth-pill">
              {me?.guest_demo ? (
                <span className="stamp stamp-navy">
                  Guest Demo{typeof me.guest_remaining === "number" ? ` (${me.guest_remaining})` : ""}
                </span>
              ) : null}
              <a href="/auth/google" className="btn btn-secondary btn-google" style={{ padding: "0.28rem 0.65rem", fontSize: "0.82rem" }}>
                <svg aria-hidden="true" width="15" height="15" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M21.8 12.23c0-.68-.06-1.36-.18-2.02H12v3.83h5.5a4.7 4.7 0 0 1-2.04 3.09v2.56h3.3c1.93-1.78 3.04-4.4 3.04-7.46ZM12 22c2.75 0 5.06-.91 6.75-2.47l-3.3-2.56c-.91.61-2.08.97-3.45.97-2.65 0-4.9-1.79-5.7-4.2H2.89v2.64A10 10 0 0 0 12 22ZM6.3 13.74A5.98 5.98 0 0 1 6 12c0-.6.1-1.19.3-1.74V7.62H2.89A10 10 0 0 0 2 12c0 1.61.39 3.14 1.09 4.38l3.21-2.64ZM12 6.06c1.5 0 2.84.52 3.9 1.53l2.92-2.92C17.05 2.99 14.74 2 12 2a10 10 0 0 0-9.11 5.62l3.41 2.64C7.1 7.85 9.35 6.06 12 6.06Z" />
                </svg>
                Đăng nhập Google
              </a>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
