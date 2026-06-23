import { prisma, isPrismaConfigured } from "@/lib/prisma";
import { readJsonDocument, writeJsonDocument } from "@/lib/server/persistent-store";
import type { PublicSharePayload } from "@/lib/share-types";

export type { PublicSharePayload } from "@/lib/share-types";

const STORE_NAME = "public-shares";

type ShareMap = Record<string, PublicSharePayload & { userId: string }>;

export type PublishShareInput = {
  userId: string;
  videoId: string;
  title: string;
  prompt?: string | null;
  videoUrl: string;
  durationSeconds: number;
  category: string;
  visualStyle: string;
  mode: string;
};

async function readShareMap(): Promise<ShareMap> {
  return readJsonDocument<ShareMap>(STORE_NAME, {});
}

async function writeShareMap(map: ShareMap): Promise<void> {
  await writeJsonDocument(STORE_NAME, map);
}

function toPublicPayload(record: {
  id: string;
  shareTitle: string | null;
  prompt: string | null;
  generatedVideoUrl: string | null;
  durationSeconds: number;
  isPublic: boolean;
  publishedAt: Date | null;
  category?: string;
  visualStyle?: string;
  mode?: string;
}): PublicSharePayload | null {
  if (!record.isPublic || !record.generatedVideoUrl) return null;

  return {
    id: record.id,
    title: record.shareTitle ?? "RTAS Studio AI Video",
    prompt: record.prompt,
    videoUrl: record.generatedVideoUrl,
    durationSeconds: record.durationSeconds,
    category: record.category ?? "story",
    visualStyle: record.visualStyle ?? "avatar",
    mode: record.mode ?? "prompt",
    isPublic: true,
    publishedAt: (record.publishedAt ?? new Date()).toISOString(),
  };
}

export async function getPublicShare(videoId: string): Promise<PublicSharePayload | null> {
  if (isPrismaConfigured()) {
    const job = await prisma.generationJob.findFirst({
      where: { id: videoId, isPublic: true, status: "COMPLETED" },
      select: {
        id: true,
        shareTitle: true,
        prompt: true,
        generatedVideoUrl: true,
        durationSeconds: true,
        isPublic: true,
        publishedAt: true,
      },
    });

    if (job) {
      return toPublicPayload({
        ...job,
        category: "story",
        visualStyle: "avatar",
        mode: "prompt",
      });
    }
  }

  const map = await readShareMap();
  const entry = map[videoId];
  if (!entry?.isPublic) return null;

  const { userId: _userId, ...publicEntry } = entry;
  return publicEntry;
}

export async function publishPublicShare(
  input: PublishShareInput
): Promise<PublicSharePayload> {
  const publishedAt = new Date();
  const prompt = input.prompt?.trim() || null;

  if (isPrismaConfigured()) {
    const existing = await prisma.generationJob.findUnique({
      where: { id: input.videoId },
      select: { userId: true },
    });

    if (existing && existing.userId !== input.userId) {
      throw new Error("You can only share videos you created.");
    }

    const job = await prisma.generationJob.upsert({
      where: { id: input.videoId },
      create: {
        id: input.videoId,
        userId: input.userId,
        status: "COMPLETED",
        prompt,
        shareTitle: input.title,
        generatedVideoUrl: input.videoUrl,
        durationSeconds: input.durationSeconds,
        isPublic: true,
        publishedAt,
        completedAt: publishedAt,
      },
      update: {
        prompt,
        shareTitle: input.title,
        generatedVideoUrl: input.videoUrl,
        durationSeconds: input.durationSeconds,
        isPublic: true,
        publishedAt,
        status: "COMPLETED",
        completedAt: publishedAt,
      },
      select: {
        id: true,
        shareTitle: true,
        prompt: true,
        generatedVideoUrl: true,
        durationSeconds: true,
        isPublic: true,
        publishedAt: true,
      },
    });

    const payload = toPublicPayload({
      ...job,
      category: input.category,
      visualStyle: input.visualStyle,
      mode: input.mode,
    });

    if (!payload) {
      throw new Error("Unable to publish share link.");
    }

    return payload;
  }

  const map = await readShareMap();
  const existing = map[input.videoId];
  if (existing && existing.userId !== input.userId) {
    throw new Error("You can only share videos you created.");
  }

  const payload: PublicSharePayload = {
    id: input.videoId,
    title: input.title,
    prompt,
    videoUrl: input.videoUrl,
    durationSeconds: input.durationSeconds,
    category: input.category,
    visualStyle: input.visualStyle,
    mode: input.mode,
    isPublic: true,
    publishedAt: publishedAt.toISOString(),
  };

  map[input.videoId] = { ...payload, userId: input.userId };
  await writeShareMap(map);
  return payload;
}
