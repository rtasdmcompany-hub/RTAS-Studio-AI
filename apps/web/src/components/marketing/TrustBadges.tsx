"use client";

import { SITE_TRUST_BADGES } from "@/lib/site-links";

type Props = {
  className?: string;
  /** Limit how many badges to show (default: all) */
  limit?: number;
  compact?: boolean;
};

export function TrustBadges({ className = "", limit, compact = false }: Props) {
  const items =
    typeof limit === "number"
      ? SITE_TRUST_BADGES.slice(0, Math.max(1, limit))
      : SITE_TRUST_BADGES;

  return (
    <ul
      className={`rtas-trust-badges${compact ? " rtas-trust-badges--compact" : ""}${className ? ` ${className}` : ""}`}
      aria-label="Trust and security"
    >
      {items.map((badge) => (
        <li key={badge.id} className="rtas-trust-badge">
          <span className="rtas-trust-badge__mark" aria-hidden />
          <span className="rtas-trust-badge__copy">
            <span className="rtas-trust-badge__label">{badge.label}</span>
            {!compact ? (
              <span className="rtas-trust-badge__desc">{badge.description}</span>
            ) : null}
          </span>
        </li>
      ))}
    </ul>
  );
}
