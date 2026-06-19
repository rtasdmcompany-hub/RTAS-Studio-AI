"use client";

import type { UserProfile } from "@rtas/shared";
import { FREE_TRIAL_DURATION_SECONDS } from "@rtas/shared";
import { isStudioOwner } from "@/lib/customer-messages";

type Props = {
  profile: UserProfile;
  backendOnline: boolean | null;
  premiumPipeline: boolean;
  statusText: string;
  apiBase: string;
  falBillingBlocked?: boolean;
  onTrialSkip?: () => void;
  diagnosticLock?: boolean;
};

export function StudioDiagnosticsHud({
  profile,
  backendOnline,
  premiumPipeline,
  statusText,
  apiBase,
  falBillingBlocked = false,
  onTrialSkip,
  diagnosticLock = false,
}: Props) {
  const owner = isStudioOwner(profile);
  const trialState = profile.freeTrialUsed
    ? "Used"
    : profile.subscriptionActive
      ? "Premium"
      : "Available";

  return (
    <aside
      className="shashka-hud"
      aria-label="Studio diagnostics"
      data-locked={diagnosticLock ? "true" : undefined}
    >
      <div className="shashka-hud__scan" aria-hidden />
      <header className="shashka-hud__title">Owner diagnostics</header>

      <dl className="shashka-hud__grid">
        <div className="shashka-hud__row shashka-hud__row--gold">
          <dt>Premium Pipeline</dt>
          <dd>{premiumPipeline ? "ACTIVE" : "PREVIEW"}</dd>
        </div>
        <div className="shashka-hud__row shashka-hud__row--green">
          <dt>Credits</dt>
          <dd>{profile.credits}</dd>
        </div>
        <div className="shashka-hud__row">
          <dt>Trial Verify</dt>
          <dd>{trialState}</dd>
        </div>
        <div className="shashka-hud__row">
          <dt>API</dt>
          <dd>
            {backendOnline === null
              ? "CHECK…"
              : backendOnline
                ? "ONLINE"
                : "OFFLINE"}
          </dd>
        </div>
        {owner && falBillingBlocked ? (
          <div className="shashka-hud__row shashka-hud__row--warn">
            <dt>Fal Guard</dt>
            <dd>PAUSED</dd>
          </div>
        ) : null}
      </dl>

      <p className="shashka-hud__status" title={statusText}>
        {statusText}
      </p>
      <p className="shashka-hud__api" title={apiBase}>
        {apiBase.replace(/^https?:\/\//, "")}
      </p>

      {!profile.subscriptionActive && !profile.freeTrialUsed && onTrialSkip ? (
        <button
          type="button"
          className="shashka-hud__skip"
          onClick={onTrialSkip}
          disabled={diagnosticLock}
        >
          Trial Verify · Skip ({FREE_TRIAL_DURATION_SECONDS}s preview)
        </button>
      ) : null}

      {diagnosticLock ? (
        <p className="shashka-hud__seal" role="status">
          Verification lock — controls disabled
        </p>
      ) : (
        <p className="shashka-hud__seal shashka-hud__seal--ready">
          Quality seal verified
        </p>
      )}
    </aside>
  );
}
