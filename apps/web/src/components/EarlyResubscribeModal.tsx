"use client";

import { STANDARD_CREDITS, rolloverCredits } from "@rtas/shared";

type Props = {
  open: boolean;
  remainingCredits: number;
  creditsExpireAt: string | null;
  onConfirm: () => void;
  onCancel: () => void;
};

export function EarlyResubscribeModal({
  open,
  remainingCredits,
  creditsExpireAt,
  onConfirm,
  onCancel,
}: Props) {
  if (!open) return null;

  const nextBalance = rolloverCredits(remainingCredits);
  const expiryLabel = creditsExpireAt
    ? new Date(creditsExpireAt).toLocaleDateString()
    : "current period";

  return (
    <div
      className="paywall-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="early-resubscribe-title"
    >
      <div className="paywall-modal">
        <h2 id="early-resubscribe-title" className="paywall-title">
          Extend your subscription?
        </h2>
        <p className="paywall-desc">
          Aap ki current subscription ki mudaat aur credits abhi baaki hain. Kya
          aap naye credits add kar ke apni subscription barhana chahte hain?
        </p>
        <p className="paywall-desc">
          You have <strong>{remainingCredits}</strong> credits remaining (valid
          until <strong>{expiryLabel}</strong>). Renewing now will roll them
          forward into <strong>{nextBalance}</strong> total credits for the next
          month ({STANDARD_CREDITS} new + rollover).
        </p>
        <button type="button" className="paywall-subscribe-btn" onClick={onConfirm}>
          Yes, add credits &amp; extend
        </button>
        <button type="button" className="paywall-skip-link" onClick={onCancel}>
          Not now
        </button>
      </div>
    </div>
  );
}
