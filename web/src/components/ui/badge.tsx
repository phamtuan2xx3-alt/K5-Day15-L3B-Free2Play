import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils.ts";

export const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 font-mono text-[11px] font-semibold tabular-nums transition-colors",
  {
    variants: {
      variant: {
        default: "border-primary/30 bg-primary/10 text-primary",
        secondary: "border-border bg-muted text-muted-foreground",
        destructive: "border-destructive/40 bg-destructive/10 text-destructive",
        success: "border-emerald-700/30 bg-emerald-500/10 text-emerald-800 dark:border-emerald-400/35 dark:text-emerald-300",
        warning: "border-amber-700/35 bg-amber-500/10 text-amber-800 dark:border-amber-400/40 dark:text-amber-300",
        outline: "border-border bg-transparent text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
