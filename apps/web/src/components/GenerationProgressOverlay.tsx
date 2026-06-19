"use client";

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

  return (
    <div className="gen-overlay" role="status" aria-live="polite" aria-busy="true">
      <div className="gen-overlay-inner">
        <div className="gen-spinner" aria-hidden />
        <p className="gen-percent">{percent}%</p>
        <div className="gen-bar-track">
          <div
            className="gen-bar-fill"
            style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
          />
        </div>
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
