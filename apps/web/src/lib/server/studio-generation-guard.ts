import { prisma, isPrismaConfigured } from "@/lib/prisma";
import { getServerProfile, saveServerProfile } from "@/lib/server/profile-store";

export const MAX_CONCURRENT_TRACKS = 3;
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
  options?: { previewOnly?: boolean; useFreeTrial?: boolean }
): Promise<void> {
  if (options?.previewOnly || options?.useFreeTrial) return;

  if (isPrismaConfigured()) {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { credits: true, concurrentTracks: true },
    });

    if (!user) {
      throw new Error(INSUFFICIENT_CREDITS_MESSAGE);
    }

    if (user.credits <= 0) {
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
  if (profile.credits <= 0) {
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
  options?: { previewOnly?: boolean; useFreeTrial?: boolean }
): Promise<void> {
  if (options?.previewOnly || options?.useFreeTrial) return;

  if (isPrismaConfigured()) {
    const user = await prisma.user.update({
      where: { id: userId },
      data: {
        concurrentTracks: { decrement: 1 },
        credits: { decrement: CREDITS_PER_RENDER },
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
    credits: Math.max(0, profile.credits - CREDITS_PER_RENDER),
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

type GenerationJobRecord = {
  id: string;
  status: "QUEUED" | "PROCESSING" | "COMPLETED" | "FAILED";
};

export async function createGenerationJob(input: {
  userId: string;
  prompt?: string | null;
  inputImageUrl?: string | null;
  durationSeconds: number;
  creditsCharged?: number;
}): Promise<GenerationJobRecord | null> {
  if (!isPrismaConfigured()) return null;

  return prisma.generationJob.create({
    data: {
      userId: input.userId,
      status: "PROCESSING",
      prompt: input.prompt ?? null,
      inputImageUrl: input.inputImageUrl ?? null,
      durationSeconds: input.durationSeconds,
      creditsCharged: input.creditsCharged ?? CREDITS_PER_RENDER,
    },
    select: { id: true, status: true },
  });
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
    },
  });
}

export async function failGenerationJob(jobId: string): Promise<void> {
  if (!isPrismaConfigured()) return;

  await prisma.generationJob.update({
    where: { id: jobId },
    data: {
      status: "FAILED",
      completedAt: new Date(),
    },
  });
}

export async function listRecentGenerationJobs(userId: string, limit = 5) {
  if (!isPrismaConfigured()) return [];

  return prisma.generationJob.findMany({
    where: { userId },
    orderBy: { createdAt: "desc" },
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
