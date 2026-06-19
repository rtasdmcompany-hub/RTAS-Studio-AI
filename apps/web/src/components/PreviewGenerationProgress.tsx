"use client";

import { forwardRef } from "react";

type Props = {
  percent: number;
  message: string;
  active: boolean;
  phase?: "running" | "error" | "success";
  patienceMessage?: string;
};

function friendlyProgressMessage(raw: string, isError: boolean): string {
  if (!raw) return "";
  if (!isError) return raw;

  const lower = raw.toLowerCase();
  if (lower.includes("duration") && lower.includes("literal_error")) {
    return "Cloud render could not read video length. Restart the API (start-studio.cmd), pick your length again, and retry.";
  }
  if (lower.includes("insufficient fal.ai balance")) {
    return "Fal.ai balance is low. Add credit at fal.ai/dashboard/billing, restart the API, then try again.";
  }
  if (raw.length > 180) {
    return raw.split("\n")[0]?.slice(0, 160) ?? "Generation failed. Please check your inputs and try again.";
  }
  return raw;
}

/** Compact progress strip — left column on preview screen. */
export const PreviewGenerationProgress = forwardRef<HTMLDivElement, Props>(
  function PreviewGenerationProgress(
    { percent, message, active, phase = "running", patienceMessage },
    ref
  ) {
    if (!active) return null;

    const clamped = Math.min(100, Math.max(0, percent));
    const isError = phase === "error";
    const label = isError
      ? "Generation failed"
      : phase === "success"
        ? "Video ready"
        : "Rendering video…";
    const displayMessage = friendlyProgressMessage(message, isError);

    return (
      <div
        ref={ref}
        className={`preview-progress${isError ? " preview-progress--error" : ""}`}
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Video generation progress"
      >
        <div className="preview-progress-header">
          <span className="preview-progress-label">
            {!isError ? <span className="preview-progress-pulse" aria-hidden /> : null}
            {label}
          </span>
          <span className="preview-progress-percent">{clamped}%</span>
        </div>
        <div className="preview-progress-track">
          <div
            className="preview-progress-fill"
            style={{ width: `${clamped}%` }}
          />
        </div>
        {displayMessage ? (
          <p className="preview-progress-message">{displayMessage}</p>
        ) : null}
        {patienceMessage && phase === "running" ? (
          <p className="preview-progress-patience">{patienceMessage}</p>
        ) : null}
      </div>
    );
  }
);
