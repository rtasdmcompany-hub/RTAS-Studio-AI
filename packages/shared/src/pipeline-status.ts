/** Long-render pipeline states — aliases into Sprint 2 job lifecycle. */

import {
  jobLifecycleLabel,
  normalizeJobLifecycleStatus,
  type JobLifecycleStatus,
} from "./job-orchestrator";

export const PIPELINE_STATUSES = [
  "queued",
  "preparing",
  "generating",
  "generating_chunks",
  "rendering",
  "compiling_media",
  "uploading",
  "completed",
  "failed",
  "cancelled",
] as const;

export type PipelineStatus = (typeof PIPELINE_STATUSES)[number];

export type ChunkManifestEntry = {
  index: number;
  durationSec: number;
  status: "pending" | "generating" | "completed" | "failed";
  falUrl?: string;
  localPath?: string;
  error?: string;
};

export function pipelineStatusLabel(status: PipelineStatus | string): string {
  const lifecycle = normalizeJobLifecycleStatus(status) as JobLifecycleStatus;
  return jobLifecycleLabel(lifecycle);
}

export {
  ACTIVE_JOB_STATUSES,
  computeJobProgress,
  isActiveJobStatus,
  isTerminalJobStatus,
  normalizeJobLifecycleStatus,
  type JobLifecycleStatus,
} from "./job-orchestrator";
