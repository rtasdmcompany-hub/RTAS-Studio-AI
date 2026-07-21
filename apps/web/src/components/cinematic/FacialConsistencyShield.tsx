"use client";

type Props = {
  className?: string;
  /** Premium golden glow on the final Identity Preservation step */
  premium?: boolean;
  showTagline?: boolean;
  /** Face match confidence 0–100. Defaults from hasReference when omitted. */
  faceMatchPercent?: number;
  /** Identity pipeline strength 0–1 (e.g. 0.85). */
  identityStrength?: number;
  /** Whether a face reference asset is present. */
  hasReference?: boolean;
  /** Show short identity best-practice tips (face-lock step). */
  showTips?: boolean;
};

const BEST_PRACTICES = [
  "Front-facing, eyes open, even lighting",
  "One clear identity reference — avoid group photos",
  "No sunglasses, masks, or heavy filters",
];

function clampPercent(n: number): number {
  return Math.max(0, Math.min(100, Math.round(n)));
}

function resolveMatchPercent(
  faceMatchPercent: number | undefined,
  hasReference: boolean | undefined
): number {
  if (typeof faceMatchPercent === "number" && Number.isFinite(faceMatchPercent)) {
    return clampPercent(faceMatchPercent);
  }
  return hasReference ? 100 : 92;
}

function resolveStrengthLabel(identityStrength: number | undefined): string {
  const raw =
    typeof identityStrength === "number" && Number.isFinite(identityStrength)
      ? identityStrength
      : 0.85;
  const pct = clampPercent(raw <= 1 ? raw * 100 : raw);
  if (pct >= 90) return `Identity strength ${pct}% · Preserved`;
  if (pct >= 70) return `Identity strength ${pct}% · Strong`;
  return `Identity strength ${pct}% · Moderate`;
}

/** Holographic USP badge — Authorized Identity Consistency. */
export function FacialConsistencyShield({
  className = "",
  premium = false,
  showTagline = false,
  faceMatchPercent,
  identityStrength,
  hasReference,
  showTips = false,
}: Props) {
  const matchPct = resolveMatchPercent(faceMatchPercent, hasReference);
  const strengthLabel = resolveStrengthLabel(identityStrength);
  const confidenceLabel = hasReference === false ? "Awaiting reference" : "Identity confidence";
  const tipsVisible = showTips || premium;

  return (
    <div className="shashka-face-shield-wrap">
      <div
        className={`shashka-face-shield${premium ? " shashka-face-shield--premium" : ""} ${className}`.trim()}
        role="status"
        aria-label={`${matchPct}% identity match. ${strengthLabel}. ${confidenceLabel}.`}
      >
        <div className="shashka-face-shield__glow" aria-hidden />
        <svg
          className="shashka-face-shield__icon"
          viewBox="0 0 64 72"
          aria-hidden
          focusable="false"
        >
          <path
            d="M32 4 L56 16 V38 C56 54 44 66 32 68 C20 66 8 54 8 38 V16 Z"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
          />
          <path
            d="M22 36 L29 44 L44 26"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <div className="shashka-face-shield__copy">
          <span className="shashka-face-shield__percent">{matchPct}%</span>
          <span className="shashka-face-shield__label">Authorized Identity Consistency</span>
          <span className="shashka-face-shield__metrics">
            <span className="shashka-face-shield__metric">
              Identity match {matchPct}%
            </span>
            <span className="shashka-face-shield__metric-sep" aria-hidden>
              ·
            </span>
            <span className="shashka-face-shield__metric">{strengthLabel}</span>
          </span>
          {hasReference === false ? (
            <span className="shashka-face-shield__status">
              Upload an identity reference photo to maximize consistency
            </span>
          ) : (
            <span className="shashka-face-shield__status">{confidenceLabel}</span>
          )}
        </div>
      </div>
      {showTagline ? (
        <p className="shashka-face-shield-tagline">
          Authorized Identity Consistency across every shot
        </p>
      ) : null}
      {tipsVisible ? (
        <ul className="shashka-face-shield__tips" aria-label="Identity Preservation best practices">
          {BEST_PRACTICES.map((tip) => (
            <li key={tip}>{tip}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
