"use client";

import { ProgressBar } from "@rtas/ui";
import {
  GENERATION_PROGRESS_STAGES,
  isProgressStageDone,
} from "@/lib/generation-progress-stages";

type Props = {
  percent: number;
  message: string;
  visible: boolean;
  stageIndex?: number;
  patienceMessage?: string;
};

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
        <ul className="gen-stages" aria-label="Generation stages">
          {GENERATION_PROGRESS_STAGES.map((stage, i) => {
            const done = isProgressStageDone(i, clamped);
            const active = i === stageIndex && clamped < 100;
            return (
              <li
                key={stage.id}
                className={[done ? "done" : "", active ? "active" : ""]
                  .filter(Boolean)
                  .join(" ")}
              >
                {stage.shortLabel}
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
