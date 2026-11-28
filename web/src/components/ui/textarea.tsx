import type { TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils.ts";

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "flex min-h-[104px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground shadow-2xs placeholder:text-muted-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-ring disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
