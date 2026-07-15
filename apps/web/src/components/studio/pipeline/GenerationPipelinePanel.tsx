"use client";

import { forwardRef, useEffect, useMemo, useState } from "react";
import { estimateProcessingWindow } from "@rtas/shared";
import { Button } from "@rtas/ui";
import {
  GENERATION_PROGRESS_STAGES,
  isProgressStageDone,
  pipelineRailIndexFromPercent,
} from "@/lib/generation-progress-stages";
import {
  getReportIssueMailto,
  softenGenerationError,
} from "@/lib/generation-error-ui";

export type PipelinePhase = "running" | "error" | "success" | "cancelled";

export type PipelineStep = {
  id: string;
  label: string;
  description: string;
};

const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: "assets",
    label: "Assets",
    description: "Preparing assets and uploading securely",
  },
  {
    id: "plan",
    label: "Plan",
    description: "Prompt analysis, storyboard, and scene planning",
  },
  {
    id: "render",
    label: "Render",
    description: "Rendering, upscaling, audio sync, and encoding",
  },
  {
    id: "deliver",
    label: "Deliver",
    description: "Finalizing and preparing your preview",
  },
];

const STAGE_EXPLANATIONS: Record<number, string> = {
  0: "Preparing and uploading your assets so the render can begin.",
  1: "Analyzing your prompt, building a storyboard, and planning scenes.",
  2: "Rendering frames, upscaling, syncing audio, and encoding. Longer clips spend more time here.",
  3: "Finalizing the file and getting your preview ready for playback.",
};

type Props = {
  percent: number;
  message: string;
  active: boolean;
  phase?: PipelinePhase;
  stageIndex?: number;
  durationSeconds?: number;
  segmentCount?: number;
  startedAt?: number | null;
  queueActive?: number;
  queueMax?: number;
  /** Display-only model label (no backend change). */
  modelLabel?: string;
  videoTitle?: string | null;
  canDownload?: boolean;
  downloadUrl?: string | null;
  onCancel?: () => void;
  onRetry?: () => void;
  onDismiss?: () => void;
  retryLoading?: boolean;
  onPreview?: () => void;
  onDownload?: () => void;
  onRegenerate?: () => void;
  onEditPrompt?: () => void;
  onCreateVariation?: () => void;
};

function stepIndexFromPercent(percent: number): number {
  return pipelineRailIndexFromPercent(percent);
}

function formatClock(totalSec: number): string {
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function formatDurationLabel(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s ? `${m}m ${s}s` : `${m}m`;
}

export const GenerationPipelinePanel = forwardRef<HTMLDivElement, Props>(
  function GenerationPipelinePanel(
    {
      percent,
      message,
      active,
      phase = "running",
      stageIndex = 0,
      durationSeconds = 30,
      segmentCount = 1,
      startedAt,
      queueActive = 0,
      queueMax = 3,
      modelLabel = "RTAS Cinematic Engine",
      videoTitle,
      canDownload = false,
      downloadUrl,
      onCancel,
      onRetry,
      onDismiss,
      retryLoading = false,
      onPreview,
      onDownload,
      onRegenerate,
      onEditPrompt,
      onCreateVariation,
    },
    ref
  ) {
    const [elapsedSec, setElapsedSec] = useState(0);

    useEffect(() => {
      if (!active || !startedAt) {
        return;
      }
      if (phase !== "running") {
        setElapsedSec(Math.floor((Date.now() - startedAt) / 1000));
        return;
      }
      const tick = () => setElapsedSec(Math.floor((Date.now() - startedAt) / 1000));
      tick();
      const id = window.setInterval(tick, 1000);
      return () => window.clearInterval(id);
    }, [active, phase, startedAt]);

    const clamped = Math.min(100, Math.max(0, percent));
    const isError = phase === "error";
    const isSuccess = phase === "success";
    const isCancelled = phase === "cancelled";
    const currentStep = stepIndexFromPercent(clamped);
    const activeStep = PIPELINE_STEPS[currentStep] ?? PIPELINE_STEPS[0];

    const eta = useMemo(
      () => estimateProcessingWindow(durationSeconds, { segmentCount }),
      [durationSeconds, segmentCount]
    );

    const remaining = useMemo(() => {
      if (phase !== "running" || clamped >= 95) return null;
      const midMinutes = (eta.minMinutes + eta.maxMinutes) / 2;
      const totalEstSec = midMinutes * 60;
      if (clamped >= 8) {
        const projected = Math.round((elapsedSec / Math.max(clamped, 1)) * 100);
        const blended = Math.round(totalEstSec * 0.45 + projected * 0.55);
        const left = Math.max(15, blended - elapsedSec);
        return left;
      }
      return Math.max(30, Math.round(totalEstSec - elapsedSec));
    }, [phase, clamped, eta.minMinutes, eta.maxMinutes, elapsedSec]);

    const etaLabel =
      phase === "running" && remaining != null
        ? `About ${formatClock(remaining)} remaining · ${eta.minMinutes}–${eta.maxMinutes} min estimate`
        : null;

    const elapsedLabel =
      phase === "running" && elapsedSec > 0
        ? `${formatClock(elapsedSec)} elapsed`
        : isSuccess && elapsedSec > 0
          ? `Completed in ${formatClock(elapsedSec)}`
          : null;

    const queuePosition =
      queueMax > 0 && queueActive >= queueMax
        ? Math.max(1, queueActive - queueMax + 1)
        : phase === "running" && queueActive > 0
          ? 1
          : 0;

    const inQueue = phase === "running" && currentStep <= 1;
    const showQueuePosition =
      phase === "running" && queueMax > 0 && (inQueue || queueActive >= queueMax);

    if (!active) return null;

    const softenedError = isError ? softenGenerationError(message) : null;
    const displayMessage = isError
      ? softenedError?.summary ?? ""
      : message;

    const headline = isError
      ? softenedError?.title ?? "Generation failed"
      : isSuccess
        ? "Your video is ready"
        : isCancelled
          ? "Continuing in the background"
          : inQueue
            ? "You are in the queue"
            : "Rendering your video";
    const progressExplanation =
      phase === "running"
        ? STAGE_EXPLANATIONS[currentStep] ?? activeStep.description
        : null;

    const successSummary = isSuccess
      ? [
          videoTitle?.trim() || "Untitled render",
          formatDurationLabel(durationSeconds),
          segmentCount > 1 ? `${segmentCount} segments` : null,
          modelLabel,
        ]
          .filter(Boolean)
          .join(" · ")
      : null;

    return (
      <div
        ref={ref}
        className={`gen-pipeline${isError ? " gen-pipeline--error" : ""}${isSuccess ? " gen-pipeline--success" : ""}${isCancelled ? " gen-pipeline--cancelled" : ""}${phase === "running" ? " gen-pipeline--running" : ""}`}
        role="region"
        aria-label="Generation pipeline"
        aria-live="polite"
      >
        <div className="gen-pipeline__header">
          <div className="gen-pipeline__title-row">
            {phase === "running" ? (
              <span className="gen-pipeline__pulse" aria-hidden />
            ) : isSuccess ? (
              <span className="gen-pipeline__check" aria-hidden>
                ✓
              </span>
            ) : null}
            <h3 className="gen-pipeline__title">{headline}</h3>
          </div>
          <div className="gen-pipeline__meta">
            <span className="gen-pipeline__percent">{clamped}%</span>
            {elapsedLabel ? <span className="gen-pipeline__elapsed">{elapsedLabel}</span> : null}
            {etaLabel ? <span className="gen-pipeline__eta">{etaLabel}</span> : null}
          </div>
        </div>

        <div
          className="gen-pipeline__track"
          role="progressbar"
          aria-valuenow={clamped}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Generation progress"
        >
          <div className="gen-pipeline__fill" style={{ width: `${clamped}%` }} />
        </div>

        {phase === "running" && remaining != null ? (
          <div className="gen-pipeline__eta-bar" aria-hidden>
            <div
              className="gen-pipeline__eta-fill"
              style={{
                width: `${Math.min(100, Math.max(4, (elapsedSec / (elapsedSec + remaining)) * 100))}%`,
              }}
            />
          </div>
        ) : null}

        {phase === "running" ? (
          <div className="gen-pipeline__confidence" aria-label="Generation status details">
            <div className="gen-pipeline__confidence-grid">
              <div className="gen-pipeline__confidence-item">
                <span className="gen-pipeline__confidence-label">Current stage</span>
                <span className="gen-pipeline__confidence-value">
                  {activeStep.label}
                  <span className="gen-pipeline__confidence-sub">
                    {currentStep + 1}/{PIPELINE_STEPS.length}
                  </span>
                </span>
              </div>
              <div className="gen-pipeline__confidence-item">
                <span className="gen-pipeline__confidence-label">Estimated time</span>
                <span className="gen-pipeline__confidence-value">
                  {remaining != null
                    ? `~${formatClock(remaining)}`
                    : `${eta.minMinutes}–${eta.maxMinutes} min`}
                  <span className="gen-pipeline__confidence-sub">
                    {eta.minMinutes}–{eta.maxMinutes} min window
                  </span>
                </span>
              </div>
              <div className="gen-pipeline__confidence-item">
                <span className="gen-pipeline__confidence-label">AI model</span>
                <span className="gen-pipeline__confidence-value">{modelLabel}</span>
              </div>
              {showQueuePosition ? (
                <div className="gen-pipeline__confidence-item">
                  <span className="gen-pipeline__confidence-label">Queue position</span>
                  <span className="gen-pipeline__confidence-value">
                    {queueActive >= queueMax
                      ? `Position #${queuePosition}`
                      : "Active slot"}
                    <span className="gen-pipeline__confidence-sub">
                      {queueActive}/{queueMax} rendering
                    </span>
                  </span>
                </div>
              ) : (
                <div className="gen-pipeline__confidence-item">
                  <span className="gen-pipeline__confidence-label">Queue</span>
                  <span className="gen-pipeline__confidence-value">
                    Your job is running
                    <span className="gen-pipeline__confidence-sub">
                      {queueActive}/{queueMax} active
                    </span>
                  </span>
                </div>
              )}
            </div>
            {progressExplanation ? (
              <p className="gen-pipeline__explain">{progressExplanation}</p>
            ) : null}
          </div>
        ) : null}

        <ol className="gen-pipeline__steps" aria-label="Pipeline steps">
          {PIPELINE_STEPS.map((step, index) => {
            const done = index < currentStep || isSuccess;
            const current = index === currentStep && phase === "running";
            return (
              <li
                key={step.id}
                className={[
                  "gen-pipeline__step",
                  done ? "gen-pipeline__step--done" : "",
                  current ? "gen-pipeline__step--active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                title={step.description}
              >
                <span className="gen-pipeline__step-dot" aria-hidden />
                <span className="gen-pipeline__step-label">{step.label}</span>
              </li>
            );
          })}
        </ol>

        {phase === "running" || isSuccess ? (
          <ul className="gen-pipeline__substages" aria-label="Generation stages">
            {GENERATION_PROGRESS_STAGES.map((stage, i) => {
              const done = isSuccess || isProgressStageDone(i, clamped);
              const activeStage =
                !isSuccess && i === stageIndex && clamped < 100;
              return (
                <li
                  key={stage.id}
                  className={[
                    done ? "done" : "",
                    activeStage ? "active" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  {stage.shortLabel}
                </li>
              );
            })}
          </ul>
        ) : null}

        {queueMax > 0 && phase === "running" ? (
          <div
            className={[
              "gen-pipeline__queue",
              inQueue ? "gen-pipeline__queue--waiting" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            aria-label="Render queue"
          >
            <span className="gen-pipeline__queue-label">Queue</span>
            <div className="gen-pipeline__queue-slots">
              {Array.from({ length: queueMax }).map((_, i) => (
                <span
                  key={i}
                  className={[
                    "gen-pipeline__queue-slot",
                    i < Math.min(queueActive, queueMax)
                      ? "gen-pipeline__queue-slot--busy"
                      : "",
                    i === Math.min(queueActive, queueMax) - 1 && phase === "running"
                      ? "gen-pipeline__queue-slot--yours"
                      : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  aria-hidden
                />
              ))}
            </div>
            <span className="gen-pipeline__queue-meta">
              {queueActive}/{queueMax} active
              {queuePosition > 0 && queueActive >= queueMax
                ? ` · position #${queuePosition}`
                : " · your job"}
            </span>
          </div>
        ) : null}

        {isError && softenedError ? (
          <div className="gen-pipeline__error" role="alert">
            {displayMessage ? (
              <p className="gen-pipeline__message">{displayMessage}</p>
            ) : null}
            {softenedError.details ? (
              <details className="gen-pipeline__error-details">
                <summary>Technical details</summary>
                <pre className="gen-pipeline__error-pre">{softenedError.details}</pre>
              </details>
            ) : null}
          </div>
        ) : displayMessage && !isSuccess ? (
          <p className="gen-pipeline__message">{displayMessage}</p>
        ) : null}

        {phase === "running" && clamped < 100 ? (
          <p className="gen-pipeline__patience">
            You can leave this page — we will notify you when your video is ready.
            Press Esc to stop waiting in this browser session.
          </p>
        ) : null}

        {isSuccess ? (
          <div className="gen-pipeline__success-card">
            <p className="gen-pipeline__success-kicker">Ready</p>
            <p className="gen-pipeline__success-summary">{successSummary}</p>
            <p className="gen-pipeline__success-note">
              Preview is ready. Download the MP4 when you are satisfied, or refine the prompt for
              another take.
            </p>
            <div className="gen-pipeline__success-actions">
              {onPreview ? (
                <Button variant="lavender" size="sm" onClick={onPreview}>
                  Play preview
                </Button>
              ) : null}
              {onDownload && canDownload && downloadUrl ? (
                <Button variant="secondary" size="sm" onClick={onDownload}>
                  Download MP4
                </Button>
              ) : null}
              {onRegenerate ? (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onRegenerate}
                  loading={retryLoading}
                >
                  {retryLoading ? "Regenerating…" : "Regenerate"}
                </Button>
              ) : null}
              {onEditPrompt ? (
                <Button variant="ghost" size="sm" onClick={onEditPrompt}>
                  Edit again
                </Button>
              ) : null}
              {onCreateVariation ? (
                <Button variant="ghost" size="sm" onClick={onCreateVariation}>
                  Create similar
                </Button>
              ) : null}
            </div>
          </div>
        ) : null}

        <div className="gen-pipeline__actions">
          {phase === "running" && onCancel ? (
            <Button variant="ghost" size="sm" onClick={onCancel}>
              Cancel
            </Button>
          ) : null}
          {isError && onRetry ? (
            <Button variant="lavender" size="sm" onClick={onRetry} loading={retryLoading}>
              {retryLoading ? "Resuming…" : "Resume"}
            </Button>
          ) : null}
          {isError ? (
            <a
              className="gen-pipeline__report-link"
              href={getReportIssueMailto(message)}
            >
              Report Issue
            </a>
          ) : null}
          {(isSuccess || isCancelled || isError) && onDismiss ? (
            <Button variant="ghost" size="sm" onClick={onDismiss}>
              Dismiss
            </Button>
          ) : null}
        </div>
      </div>
    );
  }
);
