"use client";

import { Dialog } from "@rtas/ui";
import { Button } from "@rtas/ui";

type Props = {
  open: boolean;
  title: string;
  message: string;
  minMinutes: number;
  maxMinutes: number;
  segmentCount?: number;
  onClose: () => void;
};

export function GenerationStartedModal({
  open,
  title,
  message,
  minMinutes,
  maxMinutes,
  segmentCount,
  onClose,
}: Props) {
  return (
    <Dialog
      open={open}
      variant="paywall"
      titleId="gen-started-title"
      contentClassName="paywall-modal paywall-modal--wide"
      onClose={onClose}
      closeOnEscape
    >
      <h2 id="gen-started-title" className="paywall-title">
        {title}
      </h2>
      <p className="paywall-desc">{message}</p>
      {segmentCount && segmentCount > 1 ? (
        <p className="paywall-desc">
          Building <strong>{segmentCount}</strong> segments (15s each), then stitching
          your full video automatically.
        </p>
      ) : null}
      <p className="paywall-desc">
        Estimated time:{" "}
        <strong>
          {minMinutes}–{maxMinutes} minutes
        </strong>
        . You can keep working — we&apos;ll email you and show a notification when
        your video is ready.
      </p>
      <Button variant="paywall" onClick={onClose}>
        Got it — continue
      </Button>
    </Dialog>
  );
}
