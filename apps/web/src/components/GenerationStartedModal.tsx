"use client";

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
  if (!open) return null;

  return (
    <div
      className="paywall-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="gen-started-title"
    >
      <div className="paywall-modal paywall-modal--wide">
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
        <button type="button" className="paywall-subscribe-btn" onClick={onClose}>
          Got it — continue
        </button>
      </div>
    </div>
  );
}
