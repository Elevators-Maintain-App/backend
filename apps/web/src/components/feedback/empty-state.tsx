import * as React from "react";
import { AppCard, AppCardContent } from "@/components/ui/app-card";
import { cn } from "@/lib/utils";

type EmptyStateProps = {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
};

export function EmptyState({
  title,
  description,
  action,
  className
}: EmptyStateProps) {
  return (
    <AppCard className={cn("border-dashed", className)}>
      <AppCardContent className="flex flex-col items-center justify-center gap-3 py-10 text-center">
        <h2 className="text-base font-semibold">{title}</h2>
        {description ? (
          <p className="max-w-md text-sm leading-6 text-muted-foreground">
            {description}
          </p>
        ) : null}
        {action}
      </AppCardContent>
    </AppCard>
  );
}
