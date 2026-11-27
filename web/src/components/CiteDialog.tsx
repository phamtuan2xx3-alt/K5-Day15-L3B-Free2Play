import { useEffect, useId, useRef } from "react";
import type { FileLineItem } from "../types.ts";

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
        <div>
          <strong id={titleId}>{file}</strong>{" "}
          <span className="stamp stamp-navy">L{String(targetLine).padStart(2, "0")}</span>
        </div>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => dialogRef.current?.close()}
        >
          Đóng
        </button>
      </div>

      <div className="dialog-body scroller">
        {loading && <p style={{ paddingInline: "1.15rem" }}>Đang tải nội dung nguồn…</p>}
        {error && (
          <div className="alert alert-error" style={{ marginInline: "1.15rem" }}>
            {error}
          </div>
        )}
        {!loading && !error && lines.length === 0 && (
          <p style={{ paddingInline: "1.15rem" }}>Không có dòng nào để hiển thị.</p>
        )}
        {!loading &&
          !error &&
          lines.map((item) => {
            const isTarget = item.line === targetLine;
            return (
              <div
                key={item.line}
                ref={isTarget ? targetRowRef : undefined}
                className={`code-line${isTarget ? " is-target" : ""}`}
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
