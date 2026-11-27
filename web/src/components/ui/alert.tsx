import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils.ts";

const alertVariants = cva("relative w-full rounded-lg border px-3.5 py-2.5 text-sm", {
  variants: {
    variant: {
      default: "border-border bg-muted/50 text-foreground",
      destructive: "border-destructive/45 bg-destructive/10 text-destructive",
      success: "border-emerald-700/35 bg-emerald-500/10 text-emerald-900 dark:border-emerald-400/35 dark:text-emerald-200",
      info: "border-primary/35 bg-primary/5 text-foreground",
    },
  },
  defaultVariants: {
    variant: "default",
  },
});

export interface AlertProps extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof alertVariants> {}

export function Alert({ className, variant, ...props }: AlertProps) {
  return <div className={cn(alertVariants({ variant }), className)} {...props} />;
}
