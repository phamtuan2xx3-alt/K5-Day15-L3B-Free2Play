import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils.ts";

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-md text-sm font-medium cursor-pointer touch-manipulation active:scale-[0.98] transition-[transform,border-color,opacity] duration-150 ease-[cubic-bezier(0.23,1,0.32,1)] disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-xs",
        secondary: "bg-card text-foreground border border-border hover:bg-accent hover:text-accent-foreground shadow-xs",
        outline: "border border-border bg-transparent text-foreground hover:bg-accent hover:text-accent-foreground",
        ghost: "text-muted-foreground hover:bg-accent hover:text-foreground",
        destructive: "border border-destructive/40 bg-destructive/10 text-destructive hover:bg-destructive/15",
        teal: "border border-emerald-700/35 bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 dark:border-emerald-400/40 hover:bg-emerald-500/15",
      },
      size: {
        default: "h-9 px-3.5 py-2",
        sm: "h-8 rounded-md px-2.5 text-xs",
        lg: "h-10 rounded-md px-5",
        icon: "h-8 w-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, type = "button", ...props }: ButtonProps) {
  return <button type={type} className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
