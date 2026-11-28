import { useEffect, useId, useRef } from "react";
import { X } from "lucide-react";
import { Alert } from "@/components/ui/alert.tsx";
import { Badge } from "@/components/ui/badge.tsx";
import { Button } from "@/components/ui/button.tsx";
import { cn } from "@/lib/utils.ts";
import type { FileLineItem } from "@/types.ts";

interface CiteDialogProps {
  open: boolean;
  file: string;
  targetLine: number;
  lines: FileLineItem[];
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

export function CiteDialog({
  open,
  file,
  targetLine,
  lines,
  loading,
  error,
  onClose,
}: CiteDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const targetRowRef = useRef<HTMLDivElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open) {
      if (!dialog.open) {
        dialog.showModal();
      }
    } else if (dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const rafId = requestAnimationFrame(() => {
      targetRowRef.current?.scrollIntoView({ block: "center" });
    });
    return () => cancelAnimationFrame(rafId);
  }, [open, lines, targetLine]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleClose = () => {
      onClose();
    };
    dialog.addEventListener("close", handleClose);

    // Fallback bat buoc cho Safari khi trinh duyet chua ho tro closedby="any"
    const supportsClosedBy = "closedBy" in HTMLDialogElement.prototype;
    const handleBackdropClick = (event: MouseEvent) => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      const isInside =
        rect.top <= event.clientY &&
        event.clientY <= rect.top + rect.height &&
        rect.left <= event.clientX &&
        event.clientX <= rect.left + rect.width;
      if (!isInside) {
        dialog.close();
      }
    };

    if (!supportsClosedBy) {
      dialog.addEventListener("click", handleBackdropClick);
    }

    return () => {
      dialog.removeEventListener("close", handleClose);
      if (!supportsClosedBy) {
        dialog.removeEventListener("click", handleBackdropClick);
      }
    };
  }, [onClose]);

  return (
    <dialog
      ref={dialogRef}
      {...({ closedby: "any" } as Record<string, string>)}
      aria-labelledby={titleId}
      className="cite-dialog"
    >
      <div className="dialog-head">
        <div className="flex items-center gap-2 min-w-0">
          <strong id={titleId} className="truncate font-mono text-sm">
            {file}
          </strong>
          <Badge>L{String(targetLine).padStart(2, "0")}</Badge>
        </div>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={() => dialogRef.current?.close()}
        >
          <X aria-hidden="true" className="h-3.5 w-3.5" />
          Đóng
        </Button>
      </div>

      <div className="dialog-body scroller">
        {loading && <p className="px-4 text-xs text-muted-foreground">Đang tải nội dung nguồn…</p>}
        {error && (
          <Alert variant="destructive" className="mx-4 w-auto">
            {error}
          </Alert>
        )}
        {!loading && !error && lines.length === 0 && (
          <p className="px-4 text-xs text-muted-foreground">Không có dòng nào.</p>
        )}
        {!loading &&
          !error &&
          lines.map((item) => {
            const isTarget = item.line === targetLine;
            return (
              <div
                key={item.line}
                ref={isTarget ? targetRowRef : undefined}
                className={cn("code-line", isTarget && "is-target")}
              >
                <span className="code-ln">L{String(item.line).padStart(2, "0")}</span>
                <span className="code-text">{item.text}</span>
              </div>
            );
          })}
      </div>
    </dialog>
  );
}
