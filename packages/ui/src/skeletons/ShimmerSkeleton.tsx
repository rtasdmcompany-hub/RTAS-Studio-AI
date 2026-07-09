import type { ReactNode } from "react";

type SkeletonBarProps = {
  className?: string;
};

export function SkeletonBar({ className = "" }: SkeletonBarProps) {
  return (
    <div
      className={`rtas-motion-pulse rounded-lg bg-ds-surface-glass ${className}`.trim()}
      aria-hidden
    />
  );
}

type GlassSkeletonPanelProps = {
  children: ReactNode;
  className?: string;
  ariaLabel?: string;
};

export function GlassSkeletonPanel({
  children,
  className = "",
  ariaLabel = "Loading content",
}: GlassSkeletonPanelProps) {
  return (
    <div
      className={`rounded-2xl border border-ds-border/40 cinematic-glass-panel p-6 shadow-ds-2xl backdrop-blur-ds-xl ${className}`.trim()}
      aria-busy="true"
      aria-label={ariaLabel}
      role="status"
    >
      {children}
    </div>
  );
}
