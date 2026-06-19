"use client";

import { MONTHLY_CREDITS, MONTHLY_PRICE_USD } from "@rtas/shared";

type Props = {
  open: boolean;
  creditsRequired: number;
  onSubscribe: () => void;
  onSkip: () => void;
  onClose: () => void;
};

export function SubscriptionModal({
  open,
  creditsRequired,
  onSubscribe,
  onSkip,
  onClose,
}: Props) {
  if (!open) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal">
        <h3>Free credit used</h3>
        <p>
          Your complimentary 30-second video has been used. Subscribe to
          continue creating and downloading videos.
        </p>
        <p>
          <strong>${MONTHLY_PRICE_USD}/month</strong> — {MONTHLY_CREDITS}{" "}
          credits. This video needs <strong>{creditsRequired}</strong> credits
          (50 per 5 minutes). Unused credits expire at month end; resubscribe
          early to keep remaining credits.
        </p>
        <div className="modal-actions">
          <button type="button" className="btn-primary" onClick={onSubscribe}>
            Subscribe now
          </button>
          <button type="button" className="skip-link" onClick={onSkip}>
            Skip for next time — preview only (watermarked, not downloadable)
          </button>
          <button type="button" className="btn-ghost" onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
