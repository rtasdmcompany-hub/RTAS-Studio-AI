import type { ReactNode } from "react";

type SkeletonBarProps = {
  className?: string;
};

/** Pulsing shimmer bar — base primitive for all skeleton layouts. */
export function SkeletonBar({ className = "" }: SkeletonBarProps) {
  return (
    <div
      className={`animate-pulse rounded-lg bg-white/10 ${className}`.trim()}
      aria-hidden
    />
  );
}

type GlassSkeletonPanelProps = {
  children: ReactNode;
  className?: string;
  ariaLabel?: string;
};

/** Glassmorphic container that preserves layout while data resolves. */
export function GlassSkeletonPanel({
  children,
  className = "",
  ariaLabel = "Loading content",
}: GlassSkeletonPanelProps) {
  return (
    <div
      className={`rounded-2xl border border-white/10 cinematic-glass-panel p-6 shadow-[0_24px_48px_rgba(0,0,0,0.45)] backdrop-blur-xl ${className}`.trim()}
      aria-busy="true"
      aria-label={ariaLabel}
      role="status"
    >
      {children}
    </div>
  );
}
