import type { FormEvent } from "react";
import { Menu, RefreshCw, Search } from "lucide-react";
import { BrandWordmark } from "@/components/ScanSidebar.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Input } from "@/components/ui/input.tsx";
import { cn } from "@/lib/utils.ts";
import type { SubmissionOption } from "@/types.ts";

interface TopBarProps {
  targetInput: string;
  onTargetInputChange: (val: string) => void;
  submissions: SubmissionOption[];
  scanning: boolean;
  onScan: (target: string, forceRefresh?: boolean) => void;
  onNavigate: (path: string) => void;
  onOpenMobileMenu?: () => void;
  showBrandOnDesktop?: boolean;
}

function formatOptionLabel(sub: SubmissionOption): string {
  const raw = (sub.title || sub.label || "").trim();
  if (!raw) return sub.id;
  return raw.length > 18 ? `${sub.id} · ${raw.slice(0, 17)}…` : `${sub.id} · ${raw}`;
}

export function TopBar({
  targetInput,
  onTargetInputChange,
  submissions,
  scanning,
  onScan,
  onNavigate,
  onOpenMobileMenu,
  showBrandOnDesktop = false,
}: TopBarProps) {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = targetInput.trim();
    if (!trimmed) return;
    onScan(trimmed, false);
  };

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-card/95 px-3.5 py-2 backdrop-blur-sm lg:static lg:min-h-14 lg:bg-card lg:px-6 lg:backdrop-blur-none flex items-center">
      <form
        className="grid w-full grid-cols-[auto_minmax(0,1fr)] items-center gap-x-2 gap-y-2 lg:flex lg:items-center lg:gap-3"
        onSubmit={handleSubmit}
        aria-label="Quét hồ sơ hoặc link GitHub"
      >
        {/* Row 1 Left: Hamburger (mobile) + Brand */}
        <div
          className={cn(
            "flex min-w-0 items-center gap-1.5 lg:order-1 shrink-0",
            !showBrandOnDesktop && "lg:hidden",
          )}
        >
          {onOpenMobileMenu ? (
            <button
              type="button"
              onClick={onOpenMobileMenu}
              aria-label="Mở menu điều hướng"
              className="inline-flex h-10 w-10 -ml-1.5 shrink-0 items-center justify-center rounded-md text-foreground hover:bg-accent active:scale-95 lg:hidden cursor-pointer"
            >
              <Menu aria-hidden="true" className="h-5 w-5" />
            </button>
          ) : null}

          <a
            href="/"
            className="inline-flex items-center gap-2 text-foreground no-underline shrink-0"
            onClick={(e) => {
              e.preventDefault();
              onNavigate("/");
            }}
          >
            <img src="/repoksv-logo-120.png" alt="" className="brand-logo" width={28} height={28} />
            <BrandWordmark />
          </a>
        </div>

        {/* Row 1 Right (mobile) / Beside input (desktop): Sample S01-S30 select */}
        <select
          aria-label="Chọn nhanh hồ sơ mẫu S01 đến S30"
          className="col-start-2 justify-self-end h-9 max-w-[150px] truncate rounded-md border border-input bg-background px-2 text-sm text-foreground lg:order-3 lg:max-w-[175px] lg:justify-self-auto focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-ring"
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
            <option key={sub.id} value={sub.id} title={sub.title || sub.label || sub.id}>
              {formatOptionLabel(sub)}
            </option>
          ))}
        </select>

        {/* Row 2 (mobile) / Center flex-1 (desktop): Search input + Submit + Refresh */}
        <div className="col-span-2 flex w-full items-center gap-1.5 lg:order-2 lg:flex-1 lg:min-w-0">
          <label htmlFor="repo-target-input" className="skip-link">
            URL GitHub hoặc mã hồ sơ
          </label>
          <div className="relative min-w-0 flex-1">
            <Search
              aria-hidden="true"
              className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            />
            <Input
              id="repo-target-input"
              name="target"
              type="text"
              autoComplete="off"
              spellCheck={false}
              className="h-10 lg:h-9 pl-8 font-mono text-base lg:text-[13px]"
              value={targetInput}
              onChange={(e) => onTargetInputChange(e.target.value)}
              placeholder="https://github.com/owner/repo hoặc S01–S30…"
            />
          </div>

          <Button
            type="submit"
            disabled={scanning || !targetInput.trim()}
            className="h-10 lg:h-9 shrink-0 px-3 sm:px-4"
          >
            {scanning ? (
              <>
                Đang<span className="hidden sm:inline"> quét</span>…
              </>
            ) : (
              <>
                Quét<span className="hidden sm:inline"> hồ sơ</span>
              </>
            )}
          </Button>

          <Button
            type="button"
            variant="secondary"
            aria-label="Quét lại"
            disabled={scanning || !targetInput.trim()}
            onClick={() => onScan(targetInput.trim(), true)}
            title="Bỏ qua cache và kiểm tra lại trực tiếp"
            className="h-10 w-10 p-0 sm:w-auto sm:px-3 lg:h-9 shrink-0"
          >
            <RefreshCw aria-hidden="true" className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Quét lại</span>
          </Button>
        </div>
      </form>
    </header>
  );
}
