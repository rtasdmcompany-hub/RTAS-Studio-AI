/**
 * Canonical Sprint 2 job lifecycle for RTAS AI Orchestrator.
 * Maps cleanly to Prisma GenerationJobStatus + legacy pipeline strings.
 */

export const JOB_LIFECYCLE_STATUSES = [
  "queued",
  "preparing",
  "generating",
  "rendering",
  "uploading",
  "completed",
  "failed",
  "cancelled",
] as const;

export type JobLifecycleStatus = (typeof JOB_LIFECYCLE_STATUSES)[number];

/** Active (non-terminal) statuses that should keep the client polling. */
export const ACTIVE_JOB_STATUSES = [
  "queued",
  "preparing",
  "generating",
  "rendering",
  "uploading",
] as const satisfies readonly JobLifecycleStatus[];

export type ActiveJobStatus = (typeof ACTIVE_JOB_STATUSES)[number];

export function isActiveJobStatus(status: string): status is ActiveJobStatus {
  return (ACTIVE_JOB_STATUSES as readonly string[]).includes(
    status.toLowerCase()
  );
}

export function isTerminalJobStatus(status: string): boolean {
  const s = status.toLowerCase();
  return s === "completed" || s === "failed" || s === "cancelled";
}

/** Normalize Prisma / webhook / legacy pipeline strings → lifecycle status. */
export function normalizeJobLifecycleStatus(status: string): JobLifecycleStatus {
  const s = status.toLowerCase().replace(/-/g, "_");
  switch (s) {
    case "queued":
      return "queued";
    case "preparing":
      return "preparing";
    case "generating":
    case "generating_chunks":
      return "generating";
    case "rendering":
    case "compiling_media":
      return "rendering";
    case "uploading":
      return "uploading";
    case "completed":
      return "completed";
    case "failed":
      return "failed";
    case "cancelled":
    case "canceled":
      return "cancelled";
    default:
      return "queued";
  }
}

export function jobLifecycleLabel(status: JobLifecycleStatus): string {
  switch (status) {
    case "queued":
      return "Queued for GPU worker";
    case "preparing":
      return "Preparing assets";
    case "generating":
      return "Generating video";
    case "rendering":
      return "Rendering / stitching";
    case "uploading":
      return "Uploading output";
    case "completed":
      return "Render complete";
    case "failed":
      return "Render failed";
    case "cancelled":
      return "Cancelled";
    default:
      return "Processing";
  }
}

/** Map lifecycle → Prisma GenerationJobStatus enum value. */
export function lifecycleToPrismaStatus(
  status: JobLifecycleStatus | string
): string {
  const s = normalizeJobLifecycleStatus(status);
  switch (s) {
    case "queued":
      return "QUEUED";
    case "preparing":
      return "PREPARING";
    case "generating":
      return "GENERATING";
    case "rendering":
      return "RENDERING";
    case "uploading":
      return "UPLOADING";
    case "completed":
      return "COMPLETED";
    case "failed":
      return "FAILED";
    case "cancelled":
      return "CANCELLED";
    default:
      return "QUEUED";
  }
}

/** Progress percent + ETA estimate from job row fields. */
export function computeJobProgress(input: {
  status: string;
  progressPercent?: number | null;
  chunkTotal?: number | null;
  chunksCompleted?: number | null;
  durationSeconds?: number | null;
  startedAt?: Date | string | null;
}): {
  percent: number;
  stage: JobLifecycleStatus;
  stageLabel: string;
  estimatedSecondsRemaining: number | null;
} {
  const stage = normalizeJobLifecycleStatus(input.status);
  const stageLabel = jobLifecycleLabel(stage);

  if (typeof input.progressPercent === "number" && input.progressPercent > 0) {
    const percent = Math.min(100, Math.max(0, Math.round(input.progressPercent)));
    return {
      percent: stage === "completed" ? 100 : percent,
      stage,
      stageLabel,
      estimatedSecondsRemaining: estimateRemaining(
        percent,
        input.durationSeconds,
        input.startedAt
      ),
    };
  }

  let percent = 5;
  if (stage === "queued") percent = 5;
  else if (stage === "preparing") percent = 12;
  else if (stage === "generating") {
    if (input.chunkTotal && input.chunkTotal > 0) {
      const done = input.chunksCompleted ?? 0;
      percent = Math.min(88, Math.round(15 + (done / input.chunkTotal) * 70));
    } else {
      percent = 40;
    }
  } else if (stage === "rendering") percent = 90;
  else if (stage === "uploading") percent = 96;
  else if (stage === "completed") percent = 100;
  else if (stage === "failed" || stage === "cancelled") percent = 0;

  return {
    percent,
    stage,
    stageLabel,
    estimatedSecondsRemaining: estimateRemaining(
      percent,
      input.durationSeconds,
      input.startedAt
    ),
  };
}

function estimateRemaining(
  percent: number,
  durationSeconds?: number | null,
  startedAt?: Date | string | null
): number | null {
  if (percent <= 0 || percent >= 100) return null;
  const duration = Number(durationSeconds ?? 0);
  if (!startedAt || !Number.isFinite(duration) || duration <= 0) {
    // Rough heuristic: ~4s wall time per output second remaining.
    const remainingWork = ((100 - percent) / 100) * duration * 4;
    return remainingWork > 0 ? Math.ceil(remainingWork) : null;
  }
  const started =
    startedAt instanceof Date ? startedAt.getTime() : Date.parse(String(startedAt));
  if (!Number.isFinite(started)) return null;
  const elapsedSec = Math.max(1, (Date.now() - started) / 1000);
  const totalEstimate = elapsedSec / (percent / 100);
  return Math.max(0, Math.ceil(totalEstimate - elapsedSec));
}

/** Retry policy — only retry transient provider/network failures. */
export type RetryableFailureCode =
  | "network_timeout"
  | "webhook_timeout"
  | "provider_unavailable"
  | "rate_limit"
  | "cancelled"
  | "permanent";

export function classifyGenerationFailure(message: string): RetryableFailureCode {
  const m = message.toLowerCase();
  if (m.includes("cancel")) return "cancelled";
  if (m.includes("rate limit") || m.includes("429") || m.includes("too many")) {
    return "rate_limit";
  }
  if (
    m.includes("timeout") ||
    m.includes("timed out") ||
    m.includes("etimedout") ||
    m.includes("econnreset")
  ) {
    return m.includes("webhook") ? "webhook_timeout" : "network_timeout";
  }
  if (
    m.includes("unavailable") ||
    m.includes("503") ||
    m.includes("502") ||
    m.includes("connection")
  ) {
    return "provider_unavailable";
  }
  return "permanent";
}

export function shouldRetryGenerationFailure(
  code: RetryableFailureCode,
  retryCount: number,
  maxRetries = 2
): boolean {
  if (retryCount >= maxRetries) return false;
  return (
    code === "network_timeout" ||
    code === "webhook_timeout" ||
    code === "provider_unavailable" ||
    code === "rate_limit"
  );
}
