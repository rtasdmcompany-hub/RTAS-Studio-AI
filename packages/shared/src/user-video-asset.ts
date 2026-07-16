import type { PipelineStatus } from "./pipeline-status";
import { pipelineStatusLabel } from "./pipeline-status";
import {
  isActiveJobStatus,
  normalizeJobLifecycleStatus,
} from "./job-orchestrator";

/** Pipeline states that should trigger background refresh polling. */
export const ACTIVE_PIPELINE_STATUSES = [
  "queued",
  "preparing",
  "generating",
  "generating_chunks",
  "rendering",
  "compiling_media",
  "uploading",
] as const satisfies readonly PipelineStatus[];

export type ActivePipelineStatus = (typeof ACTIVE_PIPELINE_STATUSES)[number];

export function isActivePipelineStatus(
  status: PipelineStatus | string
): status is ActivePipelineStatus {
  return isActiveJobStatus(normalizeJobLifecycleStatus(status));
}

export function prismaStatusToPipeline(status: string): PipelineStatus {
  const lifecycle = normalizeJobLifecycleStatus(status);
  switch (lifecycle) {
    case "queued":
      return "queued";
    case "preparing":
      return "preparing";
    case "generating":
      return "generating";
    case "rendering":
      return "rendering";
    case "uploading":
      return "uploading";
    case "completed":
      return "completed";
    case "failed":
      return "failed";
    case "cancelled":
      return "cancelled";
    default:
      return "queued";
  }
}

/** Server-backed gallery row (GenerationJob). */
export interface UserVideoAsset {
  id: string;
  userId: string;
  title: string;
  pipelineStatus: PipelineStatus;
  statusLabel: string;
  videoUrl: string | null;
  durationSeconds: number;
  creditsCharged: number;
  chunkTotal: number | null;
  chunksCompleted: number | null;
  errorMessage: string | null;
  isPublic: boolean;
  provider?: string | null;
  projectId?: string | null;
  createdAt: string;
  completedAt: string | null;
}

export function userVideoAssetTitle(prompt: string | null | undefined): string {
  const trimmed = (prompt ?? "").trim();
  if (!trimmed) return "Untitled render";
  return trimmed.length > 72 ? `${trimmed.slice(0, 69)}…` : trimmed;
}

export function pipelineProgressPercent(asset: Pick<
  UserVideoAsset,
  "pipelineStatus" | "chunkTotal" | "chunksCompleted"
>): number {
  const lifecycle = normalizeJobLifecycleStatus(asset.pipelineStatus);
  if (lifecycle === "queued") return 8;
  if (lifecycle === "preparing") return 12;
  if (lifecycle === "rendering") return 93;
  if (lifecycle === "uploading") return 96;
  if (lifecycle === "completed") return 100;
  if (lifecycle === "failed" || lifecycle === "cancelled") return 0;
  if (asset.chunkTotal && asset.chunkTotal > 0) {
    const done = asset.chunksCompleted ?? 0;
    return Math.min(92, Math.round(12 + (done / asset.chunkTotal) * 80));
  }
  return 35;
}

export function serializeUserVideoAsset(input: {
  id: string;
  userId: string;
  status: string;
  prompt?: string | null;
  generatedVideoUrl?: string | null;
  durationSeconds: number;
  creditsCharged: number;
  chunkTotal?: number | null;
  chunksCompleted?: number | null;
  errorMessage?: string | null;
  isPublic?: boolean;
  provider?: string | null;
  projectId?: string | null;
  createdAt: Date | string;
  completedAt?: Date | string | null;
}): UserVideoAsset {
  const pipelineStatus = prismaStatusToPipeline(input.status);
  return {
    id: input.id,
    userId: input.userId,
    title: userVideoAssetTitle(input.prompt),
    pipelineStatus,
    statusLabel: pipelineStatusLabel(pipelineStatus),
    videoUrl: input.generatedVideoUrl ?? null,
    durationSeconds: input.durationSeconds,
    creditsCharged: input.creditsCharged,
    chunkTotal: input.chunkTotal ?? null,
    chunksCompleted: input.chunksCompleted ?? null,
    errorMessage: input.errorMessage ?? null,
    isPublic: Boolean(input.isPublic),
    provider: input.provider ?? null,
    projectId: input.projectId ?? null,
    createdAt:
      input.createdAt instanceof Date
        ? input.createdAt.toISOString()
        : input.createdAt,
    completedAt: input.completedAt
      ? input.completedAt instanceof Date
        ? input.completedAt.toISOString()
        : input.completedAt
      : null,
  };
}

export const DEFAULT_VIDEO_PAGE_SIZE = 24;
export const MAX_VIDEO_PAGE_SIZE = 50;
