import type { GeneratedVideo, UserVideoAsset } from "@rtas/shared";
import { prismaStatusToPipeline, userVideoAssetTitle } from "@rtas/shared";

/** Unified row for gallery UI (server job and/or localStorage video). */
export type GalleryDisplayItem = UserVideoAsset & {
  previewOnly?: boolean;
  simulationMode?: boolean;
  canDownload?: boolean;
};

export function generatedVideoToDisplayItem(
  video: GeneratedVideo
): GalleryDisplayItem {
  const pipelineStatus =
    video.status === "ready"
      ? "completed"
      : video.status === "failed"
        ? "failed"
        : video.status === "queued"
          ? "queued"
          : "generating_chunks";

  return {
    id: video.id,
    userId: video.userId,
    title: video.title,
    pipelineStatus,
    statusLabel:
      pipelineStatus === "completed"
        ? "Render complete"
        : pipelineStatus === "failed"
          ? "Render failed"
          : "Processing",
    videoUrl: video.videoUrl ?? null,
    durationSeconds: video.durationSeconds,
    creditsCharged: video.creditsUsed,
    chunkTotal: null,
    chunksCompleted: null,
    errorMessage: video.status === "failed" ? "Generation failed" : null,
    isPublic: Boolean(video.isPublic),
    createdAt: video.createdAt,
    completedAt: video.status === "ready" ? video.createdAt : null,
    previewOnly: video.previewOnly,
    simulationMode: video.simulationMode,
    canDownload: video.canDownload,
  };
}

export function userVideoAssetToGeneratedVideo(
  item: GalleryDisplayItem,
  fallbackUserId?: string
): GeneratedVideo {
  const legacyStatus =
    item.pipelineStatus === "completed"
      ? "ready"
      : item.pipelineStatus === "failed"
        ? "failed"
        : item.pipelineStatus === "queued"
          ? "queued"
          : "processing";

  return {
    id: item.id,
    userId: item.userId || fallbackUserId || "",
    title: item.title,
    category: "story",
    mode: "prompt",
    visualStyle: "avatar",
    durationSeconds: item.durationSeconds,
    creditsUsed: item.creditsCharged,
    previewOnly: item.previewOnly ?? false,
    canDownload: item.canDownload ?? item.pipelineStatus === "completed",
    status: legacyStatus,
    videoUrl: item.videoUrl ?? undefined,
    simulationMode: item.simulationMode,
    isPublic: item.isPublic,
    createdAt: item.createdAt,
  };
}

export function mergeServerAssetsWithLocal(
  server: UserVideoAsset[],
  local: GeneratedVideo[]
): GalleryDisplayItem[] {
  const byId = new Map<string, GalleryDisplayItem>();

  for (const video of local) {
    byId.set(video.id, generatedVideoToDisplayItem(video));
  }

  for (const asset of server) {
    const existing = byId.get(asset.id);
    if (existing) {
      byId.set(asset.id, {
        ...asset,
        previewOnly: existing.previewOnly,
        simulationMode: existing.simulationMode,
        canDownload: existing.canDownload,
        videoUrl: asset.videoUrl ?? existing.videoUrl,
      });
    } else {
      byId.set(asset.id, asset);
    }
  }

  return Array.from(byId.values()).sort(
    (a, b) =>
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );
}

export function prismaJobRowToDisplayItem(row: {
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
}): GalleryDisplayItem {
  const pipelineStatus = prismaStatusToPipeline(row.status);
  return {
    id: row.id,
    userId: row.userId,
    title: userVideoAssetTitle(row.prompt),
    pipelineStatus,
    statusLabel:
      pipelineStatus === "completed"
        ? "Render complete"
        : pipelineStatus === "failed"
          ? "Render failed"
          : "Processing",
    videoUrl: row.generatedVideoUrl ?? null,
    durationSeconds: row.durationSeconds,
    creditsCharged: row.creditsCharged,
    chunkTotal: row.chunkTotal ?? null,
    chunksCompleted: row.chunksCompleted ?? null,
    errorMessage: row.errorMessage ?? null,
    isPublic: Boolean(row.isPublic),
    createdAt:
      row.createdAt instanceof Date
        ? row.createdAt.toISOString()
        : row.createdAt,
    completedAt: row.completedAt
      ? row.completedAt instanceof Date
        ? row.completedAt.toISOString()
        : row.completedAt
      : null,
  };
}
