"use client";

type WizardRoadmapProps = {
  labels: string[];
  /** 0-based current wizard step (setup = 0) */
  currentStep: number;
  /** Optional estimated minutes remaining for the full workflow */
  estimatedMinutes?: number | null;
  /** Jump back to a completed step (index < currentStep) */
  onStepSelect?: (index: number) => void;
};

/**
 * Compact roadmap so users always see the full Studio workflow ahead.
 */
export function WizardRoadmap({
  labels,
  currentStep,
  estimatedMinutes,
  onStepSelect,
}: WizardRoadmapProps) {
  if (labels.length === 0) return null;

  const remaining = Math.max(0, labels.length - currentStep - 1);
  const showEta =
    typeof estimatedMinutes === "number" &&
    Number.isFinite(estimatedMinutes) &&
    estimatedMinutes > 0;

  return (
    <nav className="studio-wizard-roadmap" aria-label="Studio workflow steps">
      <ol className="studio-wizard-roadmap__list">
        {labels.map((label, index) => {
          const done = index < currentStep;
          const active = index === currentStep;
          const future = index > currentStep;
          const canSelect = done && Boolean(onStepSelect);

          return (
            <li
              key={`${index}-${label}`}
              className={`studio-wizard-roadmap__item${
                done ? " studio-wizard-roadmap__item--done" : ""
              }${active ? " studio-wizard-roadmap__item--active" : ""}${
                future ? " studio-wizard-roadmap__item--future" : ""
              }`}
            >
              {canSelect ? (
                <button
                  type="button"
                  className="studio-wizard-roadmap__button"
                  onClick={() => onStepSelect?.(index)}
                  aria-label={`Go back to ${label}`}
                >
                  <span className="studio-wizard-roadmap__index" aria-hidden>
                    ✓
                  </span>
                  <span className="studio-wizard-roadmap__label">{label}</span>
                </button>
              ) : (
                <span
                  className="studio-wizard-roadmap__static"
                  aria-current={active ? "step" : undefined}
                  aria-disabled={future || undefined}
                >
                  <span className="studio-wizard-roadmap__index" aria-hidden>
                    {done ? "✓" : index + 1}
                  </span>
                  <span className="studio-wizard-roadmap__label">{label}</span>
                </span>
              )}
            </li>
          );
        })}
      </ol>
      {showEta ? (
        <p className="studio-wizard-roadmap__eta" aria-live="polite">
          About {estimatedMinutes} min remaining
          {remaining > 0 ? ` · ${remaining} step${remaining === 1 ? "" : "s"} left` : ""}
        </p>
      ) : null}
    </nav>
  );
}
