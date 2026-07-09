import type { Platform } from "@rtas/types";

type Props = {
  platform: Platform;
  className?: string;
};

export function PlatformIcon({ platform, className = "platform-icon" }: Props) {
  const common = {
    className,
    viewBox: "0 0 24 24",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg",
    "aria-hidden": true as const,
  };

  switch (platform) {
    case "YOUTUBE":
      return (
        <svg {...common}>
          <rect x="2" y="5" width="20" height="14" rx="4" fill="#ff0000" fillOpacity="0.9" />
          <path d="M10 9.5v5l5-2.5-5-2.5z" fill="#fff" />
        </svg>
      );
    case "TIKTOK":
      return (
        <svg {...common}>
          <path
            d="M16.5 5.5v2.2a4.8 4.8 0 0 0 3.5 1.5v2.8a7.6 7.6 0 0 1-3.5-.9v5.4a5.2 5.2 0 1 1-5.2-5.2h.8v2.8a2.4 2.4 0 1 0 1.7 2.3V5.5h2.7z"
            fill="#25f4ee"
          />
          <path
            d="M15.7 6.3v2a4.8 4.8 0 0 0 3.3 1.3v2.5a7.2 7.2 0 0 1-3.3-.8v5.1a5.2 5.2 0 1 1-4.8-5.1h.7v2.6a2.4 2.4 0 1 0 1.6 2.2V6.3h2.5z"
            fill="#fe2c55"
            fillOpacity="0.85"
          />
        </svg>
      );
    case "INSTAGRAM":
      return (
        <svg {...common}>
          <defs>
            <linearGradient id="ig-grad" x1="4" y1="20" x2="20" y2="4">
              <stop stopColor="#f58529" />
              <stop offset="0.5" stopColor="#dd2a7b" />
              <stop offset="1" stopColor="#8134af" />
            </linearGradient>
          </defs>
          <rect x="3" y="3" width="18" height="18" rx="5" stroke="url(#ig-grad)" strokeWidth="2" />
          <circle cx="12" cy="12" r="4.2" stroke="url(#ig-grad)" strokeWidth="2" />
          <circle cx="17.2" cy="6.8" r="1.2" fill="#d62976" />
        </svg>
      );
    case "FACEBOOK":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" fill="#1877f2" />
          <path
            d="M13.6 8h1.8V5.8h-1.8c-2.2 0-3.5 1.3-3.5 3.6V11H7.5v2.3h2.1V19h2.4v-5.7h2.1l.4-2.3h-2.5v-1.4c0-.7.5-1.3 1.6-1.3z"
            fill="#fff"
          />
        </svg>
      );
    case "X":
      return (
        <svg {...common}>
          <rect x="3" y="3" width="18" height="18" rx="4" fill="#0f1419" stroke="#cbd5e1" strokeWidth="1.2" />
          <path
            d="M8 8l8 8M16 8l-8 8"
            stroke="#f0f2f8"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      );
    case "LINKEDIN":
      return (
        <svg {...common}>
          <rect x="3" y="3" width="18" height="18" rx="3" fill="#0a66c2" />
          <path
            d="M8 10v7M8 7.2v.8M12 17v-4.2c0-1.4.9-2.3 2.2-2.3s2 1 2 2.4V17M12 10v7"
            stroke="#fff"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    default:
      return null;
  }
}
