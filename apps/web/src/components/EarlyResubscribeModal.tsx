"use client";

import { STANDARD_CREDITS, rolloverCredits } from "@rtas/shared";
import { Button, Dialog } from "@rtas/ui";

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
  const nextBalance = rolloverCredits(remainingCredits);
  const expiryLabel = creditsExpireAt
    ? new Date(creditsExpireAt).toLocaleDateString()
    : "current period";

  return (
    <Dialog
      open={open}
      onClose={onCancel}
      variant="paywall"
      titleId="early-resubscribe-title"
      title="Extend your subscription?"
      description={`Your current subscription period and credits are still active. Would you like to add new credits and extend your subscription now? You have ${remainingCredits} credits remaining (valid until ${expiryLabel}). Renewing now will roll them forward into ${nextBalance} total credits for the next month (${STANDARD_CREDITS} new + rollover).`}
      closeOnEscape
    >
      <Button variant="paywall" onClick={onConfirm}>
        Yes, add credits & extend
      </Button>
      <button type="button" className="paywall-skip-link rtas-ui-focus-ring" onClick={onCancel}>
        Not now
      </button>
    </Dialog>
  );
}
