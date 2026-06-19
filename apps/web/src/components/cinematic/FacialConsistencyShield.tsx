"use client";

type Props = {
  className?: string;
  /** Premium golden glow on the final identity-lock step */
  premium?: boolean;
  showTagline?: boolean;
};

/** Holographic USP badge — guaranteed facial consistency. */
export function FacialConsistencyShield({
  className = "",
  premium = false,
  showTagline = false,
}: Props) {
  return (
    <div className="shashka-face-shield-wrap">
      <div
        className={`shashka-face-shield${premium ? " shashka-face-shield--premium" : ""} ${className}`.trim()}
        role="status"
        aria-label="Guaranteed 100% genuine facial consistency enabled"
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
          <span className="shashka-face-shield__percent">100%</span>
          <span className="shashka-face-shield__label">Genuine Facial Consistency</span>
        </div>
      </div>
      {showTagline ? (
        <p className="shashka-face-shield-tagline">
          Guaranteed 100% Genuine Facial Consistency
        </p>
      ) : null}
    </div>
  );
}
