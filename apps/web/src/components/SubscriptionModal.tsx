"use client";

import { MONTHLY_CREDITS, MONTHLY_PRICE_USD } from "@rtas/shared";
import { Button, Dialog, DialogActions } from "@rtas/ui";

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
  return (
    <Dialog
      open={open}
      onClose={onClose}
      variant="modal"
      title="Free credit used"
      description={`Your complimentary 30-second video has been used. Subscribe to continue creating and downloading videos. $${MONTHLY_PRICE_USD}/month — ${MONTHLY_CREDITS} credits. This video needs ${creditsRequired} credits (50 per 5 minutes). Unused credits expire at month end; resubscribe early to keep remaining credits.`}
      closeOnEscape
    >
      <DialogActions>
        <Button variant="primary" onClick={onSubscribe}>
          Subscribe now
        </Button>
        <button type="button" className="skip-link rtas-ui-focus-ring" onClick={onSkip}>
          Skip for next time — preview only (watermarked, not downloadable)
        </button>
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
}
