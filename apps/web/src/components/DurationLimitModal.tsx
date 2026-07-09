"use client";

import Link from "next/link";
import { Button, Dialog } from "@rtas/ui";

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
  return (
    <Dialog
      open={open}
      variant="paywall"
      titleId="duration-limit-title"
      onClose={onClose}
      closeOnEscape
    >
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
        <Button variant="paywall" onClick={onRecharge}>
          Recharge account
        </Button>
      ) : null}

      <Link href="/pricing#plans" className="paywall-recharge-link">
        View plans &amp; payment →
      </Link>

      <button type="button" className="paywall-skip-link rtas-ui-focus-ring" onClick={onClose}>
        OK
      </button>
    </Dialog>
  );
}
