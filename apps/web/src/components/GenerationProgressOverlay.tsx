"use client";

import { ProgressBar } from "@rtas/ui";

type Props = {
  percent: number;
  message: string;
  visible: boolean;
  stageIndex?: number;
  patienceMessage?: string;
};

const STAGE_LABELS = ["Engine", "Identity", "Frames", "Render"] as const;

export function GenerationProgressOverlay({
  percent,
  message,
  visible,
  stageIndex = 0,
  patienceMessage,
}: Props) {
  if (!visible) return null;

  const clamped = Math.min(100, Math.max(0, percent));

  return (
    <div className="gen-overlay" role="status" aria-live="polite" aria-busy="true">
      <div className="gen-overlay-inner">
        <div className="gen-spinner rtas-ui-spinner rtas-ui-spinner--lg" aria-hidden />
        <p className="gen-percent">{clamped}%</p>
        <ProgressBar
          value={clamped}
          max={100}
          label={`Generation progress ${clamped}%`}
          className="gen-progress"
        />
        <p className="gen-message">{message}</p>
        {patienceMessage ? (
          <p className="gen-patience-message">{patienceMessage}</p>
        ) : null}
        <ul className="gen-stages">
          {STAGE_LABELS.map((label, i) => {
            const done =
              percent >= (i === 0 ? 20 : i === 1 ? 50 : i === 2 ? 80 : 100);
            const active = i === stageIndex && percent < 100;
            return (
              <li
                key={label}
                className={[done ? "done" : "", active ? "active" : ""]
                  .filter(Boolean)
                  .join(" ")}
              >
                {label}
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
