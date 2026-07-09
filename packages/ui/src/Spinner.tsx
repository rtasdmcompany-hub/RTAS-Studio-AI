import { cn } from "./lib/cn";

export type SpinnerProps = {
  size?: "sm" | "md" | "lg";
  label?: string;
  className?: string;
};

export function Spinner({ size = "md", label, className }: SpinnerProps) {
  const sizeClass =
    size === "sm" ? "rtas-ui-spinner--sm" : size === "lg" ? "rtas-ui-spinner--lg" : undefined;

  return (
    <span
      className={cn("rtas-ui-spinner", sizeClass, className)}
      role="status"
      aria-label={label ?? "Loading"}
    />
  );
}

export type LoadingOverlayProps = {
  label?: string;
  className?: string;
};

export function LoadingOverlay({ label = "Loading…", className }: LoadingOverlayProps) {
  return (
    <div className={cn("rtas-ui-loading-overlay", className)} role="status" aria-live="polite">
      <Spinner size="lg" />
      <span>{label}</span>
    </div>
  );
}
