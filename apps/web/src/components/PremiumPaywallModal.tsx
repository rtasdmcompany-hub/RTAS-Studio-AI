"use client";

import Link from "next/link";
import {
  PREMIUM_CREDITS,
  PREMIUM_PRICE_USD,
  STANDARD_CREDITS,
  STANDARD_PRICE_USD,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
} from "@rtas/shared";
import { Button, Dialog } from "@rtas/ui";

type Props = {
  open: boolean;
  message?: string;
  onSubscribeTester: () => void;
  onSubscribeStandard: () => void;
  onSubscribePremium: () => void;
  onClose: () => void;
};

export function PremiumPaywallModal({
  open,
  message,
  onSubscribeTester,
  onSubscribeStandard,
  onSubscribePremium,
  onClose,
}: Props) {
  return (
    <Dialog
      open={open}
      variant="paywall"
      titleId="paywall-title"
      contentClassName="paywall-modal paywall-modal--wide"
      onClose={onClose}
      closeOnEscape
    >
      <h2 id="paywall-title" className="paywall-title">
        You have no credits
      </h2>
      <p className="paywall-desc">
        {message ??
          "Please recharge your account to generate videos. Plans start as low as the $5 Tester pass."}
      </p>

      <Button variant="paywall-tester" onClick={onSubscribeTester}>
        Tester — ${TESTER_PRICE_USD} · {TESTER_CREDITS}s · {TESTER_DURATION_DAYS} days · try
        the full studio
      </Button>

      <Button variant="paywall-standard" onClick={onSubscribeStandard}>
        Standard — ${STANDARD_PRICE_USD}/mo · {STANDARD_CREDITS}s · HD · commercial rights
      </Button>

      <Button variant="paywall" onClick={onSubscribePremium}>
        Premium 4K — ${PREMIUM_PRICE_USD}/mo · {PREMIUM_CREDITS}s · 1 month · advanced
        cinematic 4K
      </Button>

      <Link href="/pricing#plans" className="paywall-recharge-link">
        View payment options &amp; recharge →
      </Link>

      <button type="button" className="paywall-skip-link rtas-ui-focus-ring" onClick={onClose}>
        Maybe later
      </button>
    </Dialog>
  );
}
