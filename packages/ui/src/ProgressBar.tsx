import type { HTMLAttributes } from "react";
import { cn } from "./lib/cn";

export type ProgressBarProps = HTMLAttributes<HTMLDivElement> & {
  value: number;
  max?: number;
  label?: string;
  showLabel?: boolean;
  variant?: "default" | "lavender";
};

export function ProgressBar({
  value,
  max = 100,
  label,
  showLabel = false,
  variant = "default",
  className,
  ...props
}: ProgressBarProps) {
  const clamped = Math.min(max, Math.max(0, value));
  const pct = max > 0 ? Math.round((clamped / max) * 100) : 0;
  const ariaLabel = label ?? `Progress ${pct}%`;

  return (
    <div className={cn("rtas-ui-field", className)}>
      {showLabel && label ? (
        <div className="rtas-ui-label flex justify-between">
          <span>{label}</span>
          <span>{pct}%</span>
        </div>
      ) : null}
      <div
        {...props}
        className={cn(
          "rtas-ui-progress",
          variant === "lavender" && "rtas-ui-progress--lavender",
        )}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={clamped}
        aria-label={ariaLabel}
      >
        <div className="rtas-ui-progress__bar" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
