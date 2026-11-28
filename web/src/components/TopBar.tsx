import type { FormEvent } from "react";
import { RefreshCw, Search } from "lucide-react";
import { BrandWordmark } from "@/components/ScanSidebar.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Input } from "@/components/ui/input.tsx";
import type { SubmissionOption } from "@/types.ts";

interface TopBarProps {
  targetInput: string;
  onTargetInputChange: (val: string) => void;
  submissions: SubmissionOption[];
  scanning: boolean;
  onScan: (target: string, forceRefresh?: boolean) => void;
  onNavigate: (path: string) => void;
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
  showBrandOnDesktop = false,
}: TopBarProps) {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = targetInput.trim();
    if (!trimmed) return;
    onScan(trimmed, false);
  };

  return (
    <header className="min-h-14 border-b border-border bg-card px-4 py-2 sm:px-6 flex items-center">
      <div className="flex w-full flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
        <a
          href="/"
          className={
            showBrandOnDesktop
              ? "inline-flex items-center gap-2.5 text-foreground no-underline shrink-0"
              : "inline-flex items-center gap-2.5 text-foreground no-underline lg:hidden shrink-0"
          }
          onClick={(e) => {
            e.preventDefault();
            onNavigate("/");
          }}
        >
          <img src="/repoksv-logo-120.png" alt="" className="brand-logo" width={32} height={32} />
          <BrandWordmark />
        </a>

        <form
          className="flex flex-1 flex-wrap items-center gap-2 lg:flex-nowrap"
          onSubmit={handleSubmit}
          aria-label="Quét hồ sơ hoặc link GitHub"
        >
          <label htmlFor="repo-target-input" className="skip-link">
            URL GitHub hoặc mã hồ sơ
          </label>
          <div className="relative min-w-0 flex-1 basis-52">
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
              className="pl-8 font-mono text-[13px]"
              value={targetInput}
              onChange={(e) => onTargetInputChange(e.target.value)}
              placeholder="https://github.com/owner/repo hoặc S01–S30…"
            />
          </div>

          <select
            aria-label="Chọn nhanh hồ sơ mẫu S01 đến S30"
            className="h-9 max-w-[175px] truncate rounded-md border border-input bg-background px-2.5 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-ring"
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

          <Button type="submit" disabled={scanning || !targetInput.trim()}>
            {scanning ? "Đang quét…" : "Quét hồ sơ"}
          </Button>

          <Button
            type="button"
            variant="secondary"
            disabled={scanning || !targetInput.trim()}
            onClick={() => onScan(targetInput.trim(), true)}
            title="Bỏ qua cache và kiểm tra lại trực tiếp"
          >
            <RefreshCw aria-hidden="true" className="h-3.5 w-3.5" />
            Quét lại
          </Button>
        </form>
      </div>
    </header>
  );
}
