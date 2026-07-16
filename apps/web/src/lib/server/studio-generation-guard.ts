import { prisma, isPrismaConfigured } from "@/lib/prisma";
import {
  DEFAULT_VIDEO_PAGE_SIZE,
  MAX_VIDEO_PAGE_SIZE,
  serializeUserVideoAsset,
  type UserVideoAsset,
} from "@rtas/shared";
import { getServerProfile, saveServerProfile } from "@/lib/server/profile-store";

export const MAX_CONCURRENT_TRACKS = 3;

/** Product rule: 1 credit = 1 second of video. */
export function creditsRequiredForDuration(durationSeconds: number): number {
  const seconds = Number.isFinite(durationSeconds) ? durationSeconds : 0;
  return Math.max(1, Math.ceil(seconds));
}

/** @deprecated Prefer creditsRequiredForDuration — kept for older call sites. */
export const CREDITS_PER_RENDER = 5;

export const INSUFFICIENT_CREDITS_MESSAGE =
  "Insufficient generation credits. Please upgrade your studio plan.";

export const MAX_CONCURRENT_TRACKS_MESSAGE =
  "Maximum concurrent rendering tracks reached. Please wait for active videos to complete.";

/** @deprecated Use MAX_CONCURRENT_TRACKS */
export const MAX_CONCURRENT_GENERATIONS = MAX_CONCURRENT_TRACKS;

/** @deprecated Use INSUFFICIENT_CREDITS_MESSAGE */
export const STUDIO_CREDITS_EXHAUSTED_MESSAGE = INSUFFICIENT_CREDITS_MESSAGE;

/** @deprecated Use MAX_CONCURRENT_TRACKS_MESSAGE */
export const STUDIO_GENERATION_LIMIT_MESSAGE = MAX_CONCURRENT_TRACKS_MESSAGE;

const localConcurrentTracks = new Map<string, number>();

function getLocalConcurrentTracks(userId: string): number {
  return localConcurrentTracks.get(userId) ?? 0;
}

function setLocalConcurrentTracks(userId: string, value: number): void {
  localConcurrentTracks.set(userId, Math.max(0, value));
}

export async function getUserRenderingState(userId: string): Promise<{
  credits: number;
  concurrentTracks: number;
}> {
  if (isPrismaConfigured()) {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { credits: true, concurrentTracks: true },
    });
    if (user) {
      return { credits: user.credits, concurrentTracks: user.concurrentTracks };
    }
  }

  const profile = await getServerProfile(userId);
  return {
    credits: profile.credits,
    concurrentTracks: getLocalConcurrentTracks(userId),
  };
}

export async function assertAndAcquireRenderingSlot(
  userId: string,
  options?: {
    previewOnly?: boolean;
    useFreeTrial?: boolean;
    creditsRequired?: number;
  }
): Promise<void> {
  if (options?.previewOnly || options?.useFreeTrial) return;

  const required = Math.max(1, options?.creditsRequired ?? 1);

  if (isPrismaConfigured()) {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { credits: true, concurrentTracks: true },
    });

    if (!user) {
      throw new Error(INSUFFICIENT_CREDITS_MESSAGE);
    }

    if (user.credits < required) {
      throw new Error(INSUFFICIENT_CREDITS_MESSAGE);
    }

    if (user.concurrentTracks >= MAX_CONCURRENT_TRACKS) {
      throw new Error(MAX_CONCURRENT_TRACKS_MESSAGE);
    }

    await prisma.user.update({
      where: { id: userId },
      data: { concurrentTracks: { increment: 1 } },
    });
    return;
  }

  const profile = await getServerProfile(userId);
  if (profile.credits < required) {
    throw new Error(INSUFFICIENT_CREDITS_MESSAGE);
  }

  const tracks = getLocalConcurrentTracks(userId);
  if (tracks >= MAX_CONCURRENT_TRACKS) {
    throw new Error(MAX_CONCURRENT_TRACKS_MESSAGE);
  }

  setLocalConcurrentTracks(userId, tracks + 1);
}

export async function completeRenderingSlot(
  userId: string,
  options?: {
    previewOnly?: boolean;
    useFreeTrial?: boolean;
    creditsToDebit?: number;
  }
): Promise<void> {
  if (options?.previewOnly || options?.useFreeTrial) return;

  const debit = Math.max(1, options?.creditsToDebit ?? CREDITS_PER_RENDER);

  if (isPrismaConfigured()) {
    const user = await prisma.user.update({
      where: { id: userId },
      data: {
        concurrentTracks: { decrement: 1 },
        credits: { decrement: debit },
      },
      select: { credits: true, concurrentTracks: true },
    });

    const profile = await getServerProfile(userId);
    await saveServerProfile({
      ...profile,
      credits: Math.max(0, user.credits),
      updatedAt: new Date().toISOString(),
    });
    return;
  }

  const profile = await getServerProfile(userId);
  const tracks = getLocalConcurrentTracks(userId);
  setLocalConcurrentTracks(userId, tracks - 1);
  await saveServerProfile({
    ...profile,
    credits: Math.max(0, profile.credits - debit),
    updatedAt: new Date().toISOString(),
  });
}

export async function releaseRenderingSlotOnFailure(
  userId: string,
  options?: { previewOnly?: boolean; useFreeTrial?: boolean }
): Promise<void> {
  if (options?.previewOnly || options?.useFreeTrial) return;

  if (isPrismaConfigured()) {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { concurrentTracks: true },
    });
    if (!user || user.concurrentTracks <= 0) return;

    await prisma.user.update({
      where: { id: userId },
      data: { concurrentTracks: { decrement: 1 } },
    });
    return;
  }

  const tracks = getLocalConcurrentTracks(userId);
  if (tracks > 0) {
    setLocalConcurrentTracks(userId, tracks - 1);
  }
}

type GenerationJobStatus =
  | "QUEUED"
  | "GENERATING_CHUNKS"
  | "COMPILING_MEDIA"
  | "COMPLETED"
  | "FAILED";

type GenerationJobRecord = {
  id: string;
  status: GenerationJobStatus;
  userId?: string;
};

function mapPipelineStatusToPrisma(
  status: string
): GenerationJobStatus | null {
  const normalized = status.toLowerCase().replace(/-/g, "_");
  if (normalized === "queued") return "QUEUED";
  if (normalized === "generating_chunks") return "GENERATING_CHUNKS";
  if (normalized === "compiling_media") return "COMPILING_MEDIA";
  if (normalized === "completed") return "COMPLETED";
  if (normalized === "failed") return "FAILED";
  return null;
}

export async function createGenerationJob(input: {
  userId: string;
  prompt?: string | null;
  inputImageUrl?: string | null;
  durationSeconds: number;
  creditsCharged?: number;
  backendJobId?: string | null;
  chunkTotal?: number | null;
  status?: GenerationJobStatus;
}): Promise<GenerationJobRecord | null> {
  if (!isPrismaConfigured()) return null;

  return prisma.generationJob.create({
    data: {
      userId: input.userId,
      status: input.status ?? "QUEUED",
      prompt: input.prompt ?? null,
      inputImageUrl: input.inputImageUrl ?? null,
      durationSeconds: input.durationSeconds,
      creditsCharged:
        input.creditsCharged ?? creditsRequiredForDuration(input.durationSeconds),
      backendJobId: input.backendJobId ?? null,
      chunkTotal: input.chunkTotal ?? null,
      chunksCompleted: 0,
    },
    select: { id: true, status: true, userId: true },
  });
}

export async function updateGenerationJobPipeline(input: {
  jobId: string;
  status: string;
  chunksCompleted?: number;
  chunkTotal?: number;
  chunkManifest?: unknown;
  generatedVideoUrl?: string;
  errorMessage?: string;
  backendJobId?: string;
}): Promise<GenerationJobRecord | null> {
  if (!isPrismaConfigured()) return null;

  const prismaStatus = mapPipelineStatusToPrisma(input.status);
  if (!prismaStatus) return null;

  const data: Record<string, unknown> = {
    status: prismaStatus,
  };

  if (input.chunksCompleted !== undefined) {
    data.chunksCompleted = input.chunksCompleted;
  }
  if (input.chunkTotal !== undefined) {
    data.chunkTotal = input.chunkTotal;
  }
  if (input.chunkManifest !== undefined) {
    data.chunkManifest = input.chunkManifest;
  }
  if (input.generatedVideoUrl !== undefined) {
    data.generatedVideoUrl = input.generatedVideoUrl;
  }
  if (input.errorMessage !== undefined) {
    data.errorMessage = input.errorMessage;
  }
  if (input.backendJobId !== undefined) {
    data.backendJobId = input.backendJobId;
  }
  if (prismaStatus === "COMPLETED" || prismaStatus === "FAILED") {
    data.completedAt = new Date();
  }

  return prisma.generationJob.update({
    where: { id: input.jobId },
    data,
    select: { id: true, status: true, userId: true },
  });
}

export async function getGenerationJobForUser(jobId: string, userId: string) {
  if (!isPrismaConfigured()) return null;

  return prisma.generationJob.findFirst({
    where: { id: jobId, userId },
    select: {
      id: true,
      status: true,
      prompt: true,
      generatedVideoUrl: true,
      durationSeconds: true,
      creditsCharged: true,
      chunkTotal: true,
      chunksCompleted: true,
      chunkManifest: true,
      errorMessage: true,
      backendJobId: true,
      createdAt: true,
      completedAt: true,
    },
  });
}

export async function finalizeGenerationJobSuccess(
  jobId: string,
  generatedVideoUrl: string
): Promise<void> {
  if (!isPrismaConfigured()) return;

  const existing = await prisma.generationJob.findUnique({
    where: { id: jobId },
    select: {
      userId: true,
      status: true,
      creditsCharged: true,
      durationSeconds: true,
    },
  });
  if (!existing) return;

  // Idempotent: already completed jobs must not debit credits again.
  if (existing.status === "COMPLETED") {
    await prisma.generationJob.update({
      where: { id: jobId },
      data: {
        generatedVideoUrl,
        completedAt: new Date(),
        errorMessage: null,
      },
    });
    return;
  }

  await prisma.generationJob.update({
    where: { id: jobId },
    data: {
      status: "COMPLETED",
      generatedVideoUrl,
      completedAt: new Date(),
      errorMessage: null,
    },
  });

  const creditsToDebit =
    existing.creditsCharged > 0
      ? existing.creditsCharged
      : creditsRequiredForDuration(existing.durationSeconds);

  await completeRenderingSlot(existing.userId, { creditsToDebit });
}

export async function finalizeGenerationJobFailure(
  jobId: string,
  errorMessage?: string
): Promise<void> {
  if (!isPrismaConfigured()) return;

  const existing = await prisma.generationJob.findUnique({
    where: { id: jobId },
    select: { userId: true, status: true },
  });
  if (!existing) return;

  // Idempotent: already terminal jobs must not release the slot twice.
  if (existing.status === "FAILED" || existing.status === "COMPLETED") {
    if (existing.status === "FAILED" && errorMessage) {
      await prisma.generationJob.update({
        where: { id: jobId },
        data: { errorMessage },
      });
    }
    return;
  }

  await prisma.generationJob.update({
    where: { id: jobId },
    data: {
      status: "FAILED",
      completedAt: new Date(),
      errorMessage: errorMessage ?? "Video generation failed",
    },
  });

  await releaseRenderingSlotOnFailure(existing.userId);
}

export async function completeGenerationJob(
  jobId: string,
  generatedVideoUrl: string
): Promise<void> {
  if (!isPrismaConfigured()) return;

  await prisma.generationJob.update({
    where: { id: jobId },
    data: {
      status: "COMPLETED",
      generatedVideoUrl,
      completedAt: new Date(),
      errorMessage: null,
    },
  });
}

export async function failGenerationJob(
  jobId: string,
  errorMessage?: string
): Promise<void> {
  if (!isPrismaConfigured()) return;

  await prisma.generationJob.update({
    where: { id: jobId },
    data: {
      status: "FAILED",
      completedAt: new Date(),
      errorMessage: errorMessage ?? "Video generation failed",
    },
  });
}

export async function listRecentGenerationJobs(userId: string, limit = 5) {
  if (!isPrismaConfigured()) return [];

  return prisma.generationJob.findMany({
    where: { userId },
    orderBy: [{ createdAt: "desc" }, { id: "desc" }],
    take: limit,
    select: {
      id: true,
      status: true,
      prompt: true,
      inputImageUrl: true,
      generatedVideoUrl: true,
      durationSeconds: true,
      creditsCharged: true,
      createdAt: true,
    },
  });
}

const generationJobGallerySelect = {
  id: true,
  userId: true,
  status: true,
  prompt: true,
  generatedVideoUrl: true,
  durationSeconds: true,
  creditsCharged: true,
  chunkTotal: true,
  chunksCompleted: true,
  errorMessage: true,
  isPublic: true,
  createdAt: true,
  completedAt: true,
} as const;

export type UserVideoPage = {
  items: UserVideoAsset[];
  nextCursor: string | null;
  hasMore: boolean;
};

/** Indexed, cursor-paginated gallery query scoped to userId FK. */
export async function listUserGenerationJobsPaginated(
  userId: string,
  options: { cursor?: string | null; limit?: number } = {}
): Promise<UserVideoPage> {
  if (!isPrismaConfigured()) {
    return { items: [], nextCursor: null, hasMore: false };
  }

  const limit = Math.min(
    Math.max(options.limit ?? DEFAULT_VIDEO_PAGE_SIZE, 1),
    MAX_VIDEO_PAGE_SIZE
  );

  const rows = await prisma.generationJob.findMany({
    where: { userId },
    orderBy: [{ createdAt: "desc" }, { id: "desc" }],
    take: limit + 1,
    ...(options.cursor
      ? { cursor: { id: options.cursor }, skip: 1 }
      : {}),
    select: generationJobGallerySelect,
  });

  const hasMore = rows.length > limit;
  const slice = hasMore ? rows.slice(0, limit) : rows;
  const items = slice.map((row) => serializeUserVideoAsset(row));
  const nextCursor = hasMore ? (slice[slice.length - 1]?.id ?? null) : null;

  return { items, nextCursor, hasMore };
}

export async function deleteGenerationJobForUser(
  jobId: string,
  userId: string
): Promise<{ deleted: boolean; reason?: string }> {
  if (!isPrismaConfigured()) {
    return { deleted: false, reason: "database_unavailable" };
  }

  const job = await prisma.generationJob.findFirst({
    where: { id: jobId, userId },
    select: { status: true },
  });

  if (!job) {
    return { deleted: false, reason: "not_found" };
  }

  const status = job.status.toUpperCase();
  if (
    status !== "FAILED" &&
    status !== "COMPLETED" &&
    status !== "QUEUED"
  ) {
    return { deleted: false, reason: "job_in_progress" };
  }

  await prisma.generationJob.delete({ where: { id: jobId } });
  return { deleted: true };
}
