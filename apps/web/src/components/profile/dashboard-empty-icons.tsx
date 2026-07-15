/** Lightweight SVG illustrations for dashboard empty states (no emoji). */

export function EmptyProjectsIcon() {
  return (
    <svg
      className="dashboard-empty-illu"
      viewBox="0 0 80 64"
      width="80"
      height="64"
      aria-hidden
    >
      <rect
        x="8"
        y="12"
        width="64"
        height="40"
        rx="6"
        fill="currentColor"
        opacity="0.08"
      />
      <rect
        x="16"
        y="20"
        width="28"
        height="18"
        rx="3"
        fill="currentColor"
        opacity="0.18"
      />
      <path
        d="M48 28h16M48 34h12M48 40h14"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.35"
      />
      <circle cx="64" cy="18" r="6" fill="currentColor" opacity="0.22" />
    </svg>
  );
}

export function EmptyActivityIcon() {
  return (
    <svg
      className="dashboard-empty-illu"
      viewBox="0 0 80 64"
      width="80"
      height="64"
      aria-hidden
    >
      <circle cx="20" cy="20" r="5" fill="currentColor" opacity="0.28" />
      <circle cx="20" cy="36" r="5" fill="currentColor" opacity="0.16" />
      <circle cx="20" cy="52" r="5" fill="currentColor" opacity="0.1" />
      <path
        d="M32 20h36M32 36h28M32 52h20"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        opacity="0.28"
      />
    </svg>
  );
}

export function EmptyLibraryIcon() {
  return (
    <svg
      className="dashboard-empty-illu"
      viewBox="0 0 80 64"
      width="80"
      height="64"
      aria-hidden
    >
      <rect
        x="18"
        y="10"
        width="44"
        height="44"
        rx="8"
        fill="currentColor"
        opacity="0.08"
      />
      <polygon
        points="34,24 34,46 52,35"
        fill="currentColor"
        opacity="0.28"
      />
    </svg>
  );
}
