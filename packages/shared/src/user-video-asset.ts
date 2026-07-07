import type { PipelineStatus } from "./pipeline-status";
import { pipelineStatusLabel } from "./pipeline-status";

/** Pipeline states that should trigger background refresh polling. */
export const ACTIVE_PIPELINE_STATUSES = [
  "queued",
  "generating_chunks",
  "compiling_media",
] as const satisfies readonly PipelineStatus[];

export type ActivePipelineStatus = (typeof ACTIVE_PIPELINE_STATUSES)[number];

export function isActivePipelineStatus(
  status: PipelineStatus
): status is ActivePipelineStatus {
  return (ACTIVE_PIPELINE_STATUSES as readonly string[]).includes(status);
}

export function prismaStatusToPipeline(status: string): PipelineStatus {
  switch (status.toUpperCase()) {
    case "QUEUED":
      return "queued";
    case "GENERATING_CHUNKS":
      return "generating_chunks";
    case "COMPILING_MEDIA":
      return "compiling_media";
    case "COMPLETED":
      return "completed";
    case "FAILED":
      return "failed";
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
  if (asset.pipelineStatus === "queued") return 8;
  if (asset.pipelineStatus === "compiling_media") return 93;
  if (asset.pipelineStatus === "completed") return 100;
  if (asset.pipelineStatus === "failed") return 0;
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
