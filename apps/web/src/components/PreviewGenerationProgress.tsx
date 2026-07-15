"use client";

import { forwardRef } from "react";
import {
  getReportIssueMailto,
  softenGenerationError,
} from "@/lib/generation-error-ui";

type Props = {
  percent: number;
  message: string;
  active: boolean;
  phase?: "running" | "error" | "success";
  patienceMessage?: string;
};

/** Compact progress strip — left column on preview screen. */
export const PreviewGenerationProgress = forwardRef<HTMLDivElement, Props>(
  function PreviewGenerationProgress(
    { percent, message, active, phase = "running", patienceMessage },
    ref
  ) {
    if (!active) return null;

    const clamped = Math.min(100, Math.max(0, percent));
    const isError = phase === "error";
    const softened = isError ? softenGenerationError(message) : null;
    const label = isError
      ? softened?.title ?? "Generation failed"
      : phase === "success"
        ? "Video ready"
        : "Rendering video…";
    const displayMessage = isError
      ? softened?.summary ?? ""
      : message;

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
        {isError && softened?.details ? (
          <details className="preview-progress-details">
            <summary>Technical details</summary>
            <pre className="preview-progress-details__pre">{softened.details}</pre>
          </details>
        ) : null}
        {isError ? (
          <a
            className="preview-progress-report"
            href={getReportIssueMailto(message)}
          >
            Report Issue
          </a>
        ) : null}
        {patienceMessage && phase === "running" ? (
          <p className="preview-progress-patience">{patienceMessage}</p>
        ) : null}
      </div>
    );
  }
);
