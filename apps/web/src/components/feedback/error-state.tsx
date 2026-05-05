import { AlertTriangle } from "lucide-react";
import * as React from "react";
import { AppButton } from "@/components/ui/app-button";
import { AppCard, AppCardContent } from "@/components/ui/app-card";

type ErrorStateProps = {
  title?: string;
  description: string;
  onRetry?: () => void;
};

export function ErrorState({
  title = "No pudimos cargar la informacion",
  description,
  onRetry
}: ErrorStateProps) {
  return (
    <AppCard>
      <AppCardContent className="flex flex-col gap-4 py-8">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-destructive/10 text-destructive">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold">{title}</h2>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              {description}
            </p>
          </div>
        </div>
        {onRetry ? (
          <AppButton className="w-fit" variant="outline" onClick={onRetry}>
            Reintentar
          </AppButton>
        ) : null}
      </AppCardContent>
    </AppCard>
  );
}
