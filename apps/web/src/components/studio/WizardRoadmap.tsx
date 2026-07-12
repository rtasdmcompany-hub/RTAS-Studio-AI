"use client";

type WizardRoadmapProps = {
  labels: string[];
  /** 0-based current wizard step (setup = 0) */
  currentStep: number;
};

/**
 * Compact roadmap so users always see the full Studio workflow ahead.
 */
export function WizardRoadmap({ labels, currentStep }: WizardRoadmapProps) {
  if (labels.length === 0) return null;

  return (
    <nav className="studio-wizard-roadmap" aria-label="Studio workflow steps">
      <ol className="studio-wizard-roadmap__list">
        {labels.map((label, index) => {
          const done = index < currentStep;
          const active = index === currentStep;
          return (
            <li
              key={`${index}-${label}`}
              className={`studio-wizard-roadmap__item${
                done ? " studio-wizard-roadmap__item--done" : ""
              }${active ? " studio-wizard-roadmap__item--active" : ""}`}
            >
              <span className="studio-wizard-roadmap__index" aria-hidden>
                {done ? "✓" : index + 1}
              </span>
              <span className="studio-wizard-roadmap__label">{label}</span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
