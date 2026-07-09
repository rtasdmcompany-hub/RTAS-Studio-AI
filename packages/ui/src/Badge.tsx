import type { HTMLAttributes } from "react";
import { cn } from "./lib/cn";

export type BadgeVariant = "default" | "accent" | "success" | "warning" | "danger";

export type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  variant?: BadgeVariant;
};

export function Badge({
  variant = "default",
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      {...props}
      className={cn("rtas-ui-badge", `rtas-ui-badge--${variant}`, className)}
    >
      {children}
    </span>
  );
}
