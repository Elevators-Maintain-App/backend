import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";
import { cn } from "@/lib/utils";

const statusBadgeVariants = cva(
  "inline-flex h-6 items-center rounded-md border px-2 text-xs font-medium",
  {
    variants: {
      tone: {
        neutral: "border-border bg-muted text-muted-foreground",
        success: "border-success/20 bg-success/10 text-success",
        warning: "border-warning/25 bg-warning/15 text-warning-foreground",
        info: "border-info/20 bg-info/10 text-info",
        danger: "border-destructive/20 bg-destructive/10 text-destructive"
      }
    },
    defaultVariants: {
      tone: "neutral"
    }
  }
);

export interface StatusBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof statusBadgeVariants> {}

export function StatusBadge({ className, tone, ...props }: StatusBadgeProps) {
  return (
    <span className={cn(statusBadgeVariants({ tone }), className)} {...props} />
  );
}
