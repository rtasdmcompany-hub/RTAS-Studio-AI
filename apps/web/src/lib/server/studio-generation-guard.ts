import { prisma, isPrismaConfigured } from "@/lib/prisma";
import {
  DEFAULT_VIDEO_PAGE_SIZE,
  MAX_VIDEO_PAGE_SIZE,
  lifecycleToPrismaStatus,
  normalizeJobLifecycleStatus,
  serializeUserVideoAsset,
  type UserVideoAsset,
} from "@rtas/shared";
import { getServerProfile, saveServerProfile } from "@/lib/server/profile-store";
import { logGeneration } from "@/lib/server/generation-logger";

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
  | "PREPARING"
  | "GENERATING"
  | "GENERATING_CHUNKS"
  | "RENDERING"
  | "COMPILING_MEDIA"
  | "UPLOADING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

type GenerationJobRecord = {
  id: string;
  status: GenerationJobStatus;
  userId?: string;
  projectId?: string | null;
};

function mapPipelineStatusToPrisma(
  status: string
): GenerationJobStatus | null {
  const lifecycle = normalizeJobLifecycleStatus(status);
  const prismaStatus = lifecycleToPrismaStatus(lifecycle) as GenerationJobStatus;
  // Preserve legacy chunk pipeline strings when workers still emit them.
  const raw = status.toLowerCase().replace(/-/g, "_");
  if (raw === "generating_chunks") return "GENERATING_CHUNKS";
  if (raw === "compiling_media") return "COMPILING_MEDIA";
  return prismaStatus;
}

function progressForPrismaStatus(status: GenerationJobStatus): number {
  switch (status) {
    case "QUEUED":
      return 5;
    case "PREPARING":
      return 12;
    case "GENERATING":
    case "GENERATING_CHUNKS":
      return 40;
    case "RENDERING":
    case "COMPILING_MEDIA":
      return 90;
    case "UPLOADING":
      return 96;
    case "COMPLETED":
      return 100;
    default:
      return 0;
  }
}

export async function createStudioProject(input: {
  userId: string;
  title?: string | null;
  prompt?: string | null;
  inputImageUrl?: string | null;
  audioUrl?: string | null;
  settings?: unknown;
  durationSeconds: number;
  creditsUsed?: number;
  provider?: string | null;
  status?: string;
}): Promise<{ id: string } | null> {
  if (!isPrismaConfigured()) return null;

  return prisma.project.create({
    data: {
      userId: input.userId,
      title: input.title ?? null,
      prompt: input.prompt ?? null,
      inputImageUrl: input.inputImageUrl ?? null,
      audioUrl: input.audioUrl ?? null,
      settings: input.settings ?? undefined,
      durationSeconds: input.durationSeconds,
      creditsUsed: input.creditsUsed ?? 0,
      provider: input.provider ?? null,
      status: input.status ?? "queued",
    },
    select: { id: true },
  });
}

export async function createGenerationJob(input: {
  userId: string;
  prompt?: string | null;
  inputImageUrl?: string | null;
  audioUrl?: string | null;
  durationSeconds: number;
  creditsCharged?: number;
  backendJobId?: string | null;
  chunkTotal?: number | null;
  status?: GenerationJobStatus;
  provider?: string | null;
  settings?: unknown;
  projectId?: string | null;
  title?: string | null;
}): Promise<GenerationJobRecord | null> {
  if (!isPrismaConfigured()) return null;

  const creditsCharged =
    input.creditsCharged ?? creditsRequiredForDuration(input.durationSeconds);

  let projectId = input.projectId ?? null;
  if (!projectId) {
    const project = await createStudioProject({
      userId: input.userId,
      title: input.title ?? input.prompt ?? null,
      prompt: input.prompt ?? null,
      inputImageUrl: input.inputImageUrl ?? null,
      audioUrl: input.audioUrl ?? null,
      settings: input.settings,
      durationSeconds: input.durationSeconds,
      creditsUsed: creditsCharged,
      provider: input.provider ?? null,
      status: "queued",
    });
    projectId = project?.id ?? null;
  }

  const job = await prisma.generationJob.create({
    data: {
      userId: input.userId,
      projectId,
      status: input.status ?? "QUEUED",
      prompt: input.prompt ?? null,
      inputImageUrl: input.inputImageUrl ?? null,
      audioUrl: input.audioUrl ?? null,
      durationSeconds: input.durationSeconds,
      creditsCharged,
      creditsDebited: false,
      provider: input.provider ?? null,
      settings: input.settings ?? undefined,
      progressPercent: 5,
      stageLabel: "Queued for GPU worker",
      backendJobId: input.backendJobId ?? null,
      chunkTotal: input.chunkTotal ?? null,
      chunksCompleted: 0,
      startedAt: new Date(),
    },
    select: { id: true, status: true, userId: true, projectId: true },
  });

  if (projectId) {
    await prisma.project.update({
      where: { id: projectId },
      data: { latestJobId: job.id, status: "queued" },
    });
  }

  logGeneration({
    event: "job_created",
    generationId: job.id,
    userId: input.userId,
    projectId,
    credits: creditsCharged,
    durationSeconds: input.durationSeconds,
    provider: input.provider ?? null,
    status: job.status,
  });

  return job;
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
  provider?: string;
  progressPercent?: number;
  stageLabel?: string;
  queuePosition?: number | null;
  estimatedSecondsRemaining?: number | null;
}): Promise<GenerationJobRecord | null> {
  if (!isPrismaConfigured()) return null;

  const prismaStatus = mapPipelineStatusToPrisma(input.status);
  if (!prismaStatus) return null;

  const data: Record<string, unknown> = {
    status: prismaStatus,
    progressPercent:
      input.progressPercent ?? progressForPrismaStatus(prismaStatus),
    stageLabel:
      input.stageLabel ??
      normalizeJobLifecycleStatus(input.status).replace(/_/g, " "),
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
  if (input.provider !== undefined) {
    data.provider = input.provider;
  }
  if (input.queuePosition !== undefined) {
    data.queuePosition = input.queuePosition;
  }
  if (input.estimatedSecondsRemaining !== undefined) {
    data.estimatedSecondsRemaining = input.estimatedSecondsRemaining;
  }
  if (
    prismaStatus === "COMPLETED" ||
    prismaStatus === "FAILED" ||
    prismaStatus === "CANCELLED"
  ) {
    data.completedAt = new Date();
  }
  if (
    prismaStatus === "PREPARING" ||
    prismaStatus === "GENERATING" ||
    prismaStatus === "GENERATING_CHUNKS"
  ) {
    data.startedAt = new Date();
  }

  const job = await prisma.generationJob.update({
    where: { id: input.jobId },
    data,
    select: { id: true, status: true, userId: true, projectId: true },
  });

  if (job.projectId) {
    await prisma.project.update({
      where: { id: job.projectId },
      data: {
        status: normalizeJobLifecycleStatus(prismaStatus),
        ...(input.generatedVideoUrl
          ? { outputUrl: input.generatedVideoUrl }
          : {}),
        ...(input.provider ? { provider: input.provider } : {}),
      },
    });
  }

  return job;
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
      creditsDebited: true,
      provider: true,
      projectId: true,
      progressPercent: true,
      stageLabel: true,
      queuePosition: true,
      estimatedSecondsRemaining: true,
      retryCount: true,
      chunkTotal: true,
      chunksCompleted: true,
      chunkManifest: true,
      errorMessage: true,
      backendJobId: true,
      settings: true,
      inputImageUrl: true,
      audioUrl: true,
      startedAt: true,
      cancelledAt: true,
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
      creditsDebited: true,
      durationSeconds: true,
      projectId: true,
      provider: true,
    },
  });
  if (!existing) return;

  // Idempotent: already debited → never double-charge.
  if (existing.creditsDebited) {
    await prisma.generationJob.update({
      where: { id: jobId },
      data: {
        generatedVideoUrl,
        status: "COMPLETED",
        progressPercent: 100,
        stageLabel: "Render complete",
        completedAt: new Date(),
        errorMessage: null,
      },
    });
    if (existing.projectId) {
      await prisma.project.update({
        where: { id: existing.projectId },
        data: {
          status: "completed",
          outputUrl: generatedVideoUrl,
          creditsUsed: existing.creditsCharged,
        },
      });
    }
    return;
  }

  const creditsToDebit =
    existing.creditsCharged > 0
      ? existing.creditsCharged
      : creditsRequiredForDuration(existing.durationSeconds);

  await prisma.generationJob.update({
    where: { id: jobId },
    data: {
      status: "COMPLETED",
      generatedVideoUrl,
      progressPercent: 100,
      stageLabel: "Render complete",
      completedAt: new Date(),
      errorMessage: null,
      creditsDebited: true,
    },
  });

  await completeRenderingSlot(existing.userId, { creditsToDebit });

  if (existing.projectId) {
    await prisma.project.update({
      where: { id: existing.projectId },
      data: {
        status: "completed",
        outputUrl: generatedVideoUrl,
        creditsUsed: creditsToDebit,
        provider: existing.provider,
      },
    });
  }

  logGeneration({
    event: "job_completed",
    generationId: jobId,
    userId: existing.userId,
    projectId: existing.projectId,
    credits: creditsToDebit,
    provider: existing.provider,
    status: "completed",
  });
}

export async function finalizeGenerationJobFailure(
  jobId: string,
  errorMessage?: string
): Promise<void> {
  if (!isPrismaConfigured()) return;

  const existing = await prisma.generationJob.findUnique({
    where: { id: jobId },
    select: { userId: true, status: true, projectId: true, creditsDebited: true },
  });
  if (!existing) return;

  // Idempotent: already terminal jobs must not release the slot twice.
  if (
    existing.status === "FAILED" ||
    existing.status === "COMPLETED" ||
    existing.status === "CANCELLED"
  ) {
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
      progressPercent: 0,
      stageLabel: "Render failed",
    },
  });

  // Never debit on failure; only release the concurrent slot.
  if (!existing.creditsDebited) {
    await releaseRenderingSlotOnFailure(existing.userId);
  }

  if (existing.projectId) {
    await prisma.project.update({
      where: { id: existing.projectId },
      data: { status: "failed" },
    });
  }

  logGeneration({
    event: "job_failed",
    generationId: jobId,
    userId: existing.userId,
    projectId: existing.projectId,
    failure: errorMessage ?? "Video generation failed",
    status: "failed",
  });
}

export async function cancelGenerationJobForUser(
  jobId: string,
  userId: string
): Promise<{ cancelled: boolean; reason?: string }> {
  if (!isPrismaConfigured()) {
    return { cancelled: false, reason: "database_unavailable" };
  }

  const job = await prisma.generationJob.findFirst({
    where: { id: jobId, userId },
    select: {
      status: true,
      creditsDebited: true,
      projectId: true,
    },
  });

  if (!job) return { cancelled: false, reason: "not_found" };

  const status = job.status.toUpperCase();
  if (status === "COMPLETED" || status === "FAILED" || status === "CANCELLED") {
    return { cancelled: false, reason: "already_terminal" };
  }

  await prisma.generationJob.update({
    where: { id: jobId },
    data: {
      status: "CANCELLED",
      cancelledAt: new Date(),
      completedAt: new Date(),
      errorMessage: "Cancelled by user",
      progressPercent: 0,
      stageLabel: "Cancelled",
    },
  });

  if (!job.creditsDebited) {
    await releaseRenderingSlotOnFailure(userId);
  }

  if (job.projectId) {
    await prisma.project.update({
      where: { id: job.projectId },
      data: { status: "cancelled" },
    });
  }

  logGeneration({
    event: "job_cancelled",
    generationId: jobId,
    userId,
    projectId: job.projectId,
    status: "cancelled",
  });

  return { cancelled: true };
}

export async function duplicateProjectForUser(
  jobId: string,
  userId: string
): Promise<{
  ok: boolean;
  reason?: string;
  project?: {
    id: string;
    prompt: string | null;
    inputImageUrl: string | null;
    audioUrl: string | null;
    settings: unknown;
    durationSeconds: number;
    provider: string | null;
  };
}> {
  if (!isPrismaConfigured()) {
    return { ok: false, reason: "database_unavailable" };
  }

  const source = await prisma.generationJob.findFirst({
    where: { id: jobId, userId },
    select: {
      prompt: true,
      inputImageUrl: true,
      audioUrl: true,
      settings: true,
      durationSeconds: true,
      provider: true,
      projectId: true,
    },
  });

  if (!source) return { ok: false, reason: "not_found" };

  const project = await createStudioProject({
    userId,
    title: source.prompt ? `Copy — ${source.prompt.slice(0, 48)}` : "Duplicated project",
    prompt: source.prompt,
    inputImageUrl: source.inputImageUrl,
    audioUrl: source.audioUrl,
    settings: source.settings ?? undefined,
    durationSeconds: source.durationSeconds,
    provider: source.provider,
    status: "draft",
  });

  if (!project) return { ok: false, reason: "create_failed" };

  return {
    ok: true,
    project: {
      id: project.id,
      prompt: source.prompt,
      inputImageUrl: source.inputImageUrl,
      audioUrl: source.audioUrl,
      settings: source.settings,
      durationSeconds: source.durationSeconds,
      provider: source.provider,
    },
  };
}

export async function listProjectsForUser(
  userId: string,
  limit = 24
): Promise<
  Array<{
    id: string;
    title: string | null;
    prompt: string | null;
    outputUrl: string | null;
    status: string;
    durationSeconds: number;
    creditsUsed: number;
    provider: string | null;
    latestJobId: string | null;
    createdAt: Date;
  }>
> {
  if (!isPrismaConfigured()) return [];

  return prisma.project.findMany({
    where: { userId },
    orderBy: [{ createdAt: "desc" }],
    take: Math.min(Math.max(limit, 1), 50),
    select: {
      id: true,
      title: true,
      prompt: true,
      outputUrl: true,
      status: true,
      durationSeconds: true,
      creditsUsed: true,
      provider: true,
      latestJobId: true,
      createdAt: true,
    },
  });
}

export async function completeGenerationJob(
  jobId: string,
  generatedVideoUrl: string,
  options?: { markCreditsDebited?: boolean; provider?: string | null }
): Promise<void> {
  if (!isPrismaConfigured()) return;

  const job = await prisma.generationJob.update({
    where: { id: jobId },
    data: {
      status: "COMPLETED",
      generatedVideoUrl,
      progressPercent: 100,
      stageLabel: "Render complete",
      completedAt: new Date(),
      errorMessage: null,
      ...(options?.markCreditsDebited ? { creditsDebited: true } : {}),
      ...(options?.provider ? { provider: options.provider } : {}),
    },
    select: { projectId: true, creditsCharged: true, provider: true },
  });

  if (job.projectId) {
    await prisma.project.update({
      where: { id: job.projectId },
      data: {
        status: "completed",
        outputUrl: generatedVideoUrl,
        creditsUsed: job.creditsCharged,
        provider: options?.provider ?? job.provider,
      },
    });
  }
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
  provider: true,
  projectId: true,
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
    status !== "QUEUED" &&
    status !== "CANCELLED"
  ) {
    return { deleted: false, reason: "job_in_progress" };
  }

  await prisma.generationJob.delete({ where: { id: jobId } });
  return { deleted: true };
}
