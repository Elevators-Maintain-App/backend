import * as React from "react";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export type AppSelectOption = {
  value: string;
  label: string;
};

export type AppSelectProps = React.SelectHTMLAttributes<HTMLSelectElement> & {
  label?: string;
  error?: string;
  hint?: string;
  options: AppSelectOption[];
  placeholder?: string;
};

const AppSelect = React.forwardRef<HTMLSelectElement, AppSelectProps>(
  (
    {
      className,
      id,
      label,
      error,
      hint,
      options,
      placeholder = "Seleccionar",
      ...props
    },
    ref
  ) => {
    const generatedId = React.useId();
    const selectId = id || generatedId;
    const helperText = error || hint;

    return (
      <div className="space-y-2">
        {label ? <Label htmlFor={selectId}>{label}</Label> : null}
        <select
          ref={ref}
          id={selectId}
          aria-invalid={Boolean(error)}
          aria-describedby={helperText ? `${selectId}-helper` : undefined}
          className={cn(
            "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
            error ? "border-destructive focus-visible:ring-destructive" : null,
            className
          )}
          {...props}
        >
          <option value="">{placeholder}</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {helperText ? (
          <p
            id={`${selectId}-helper`}
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
AppSelect.displayName = "AppSelect";

export { AppSelect };
