import * as React from "react";
import { Input, type InputProps } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export type AppInputProps = InputProps & {
  label?: string;
  error?: string;
  hint?: string;
};

const AppInput = React.forwardRef<HTMLInputElement, AppInputProps>(
  ({ className, id, label, error, hint, ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id || generatedId;
    const helperText = error || hint;

    return (
      <div className="space-y-2">
        {label ? <Label htmlFor={inputId}>{label}</Label> : null}
        <Input
          ref={ref}
          id={inputId}
          aria-invalid={Boolean(error)}
          aria-describedby={helperText ? `${inputId}-helper` : undefined}
          className={cn(error ? "border-destructive focus-visible:ring-destructive" : null, className)}
          {...props}
        />
        {helperText ? (
          <p
            id={`${inputId}-helper`}
            className={cn(
              "text-sm",
              error ? "text-destructive" : "text-muted-foreground"
            )}
          >
            {helperText}
          </p>
        ) : null}
      </div>
    );
  }
);
AppInput.displayName = "AppInput";

export { AppInput };
