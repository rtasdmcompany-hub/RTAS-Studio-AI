"use client";

import Link from "next/link";

type Props = {
  open: boolean;
  message: string;
  maxAllowedSeconds?: number;
  onClose: () => void;
  onRecharge?: () => void;
};

export function DurationLimitModal({
  open,
  message,
  maxAllowedSeconds,
  onClose,
  onRecharge,
}: Props) {
  if (!open) return null;

  return (
    <div
      className="paywall-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="duration-limit-title"
    >
      <div className="paywall-modal">
        <h2 id="duration-limit-title" className="paywall-title">
          Video length not allowed
        </h2>
        <p className="paywall-desc">{message}</p>
        {maxAllowedSeconds !== undefined && maxAllowedSeconds > 0 ? (
          <p className="paywall-desc">
            Maximum you can select right now:{" "}
            <strong>{maxAllowedSeconds} seconds</strong>.
          </p>
        ) : null}

        {onRecharge ? (
          <button type="button" className="paywall-subscribe-btn" onClick={onRecharge}>
            Recharge account
          </button>
        ) : null}

        <Link href="/pricing#plans" className="paywall-recharge-link">
          View plans &amp; payment →
        </Link>

        <button type="button" className="paywall-skip-link" onClick={onClose}>
          OK
        </button>
      </div>
    </div>
  );
}
