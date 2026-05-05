import * as React from "react";
import { Button, type ButtonProps } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type AppButtonProps = ButtonProps;

const AppButton = React.forwardRef<HTMLButtonElement, AppButtonProps>(
  ({ className, ...props }, ref) => {
    return (
      <Button
        ref={ref}
        className={cn("shadow-sm active:translate-y-px", className)}
        {...props}
      />
    );
  }
);
AppButton.displayName = "AppButton";

export { AppButton };
