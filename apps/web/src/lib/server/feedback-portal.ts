/**
 * Phase 13 Sprint 9 — Feedback portal persistence helpers.
 * Real submissions + votes only. Never seed fake vote counts.
 */

import { createHash } from "crypto";
import { prisma, isPrismaConfigured } from "@/lib/prisma";
import { logSystemEvent } from "@/lib/server/audit-log";

export const FEEDBACK_KINDS = [
  "bug",
  "feature",
  "feedback",
  "suggestion",
  "other",
] as const;
export type FeedbackKind = (typeof FEEDBACK_KINDS)[number];

export const FEEDBACK_STATUSES = [
  "received",
  "under_review",
  "planned",
  "in_progress",
  "shipped",
  "closed",
] as const;
export type FeedbackStatus = (typeof FEEDBACK_STATUSES)[number];

export function hashVoterKey(raw: string): string {
  return createHash("sha256").update(raw).digest("hex").slice(0, 40);
}

export type CreateFeedbackInput = {
  kind: FeedbackKind;
  message: string;
  title?: string;
  email?: string;
  rating?: number;
  userId?: string;
  ip?: string;
  source?: string;
};

export async function createCustomerFeedback(input: CreateFeedbackInput) {
  if (!isPrismaConfigured()) {
    return { ok: false as const, error: "Database not configured.", code: "DB_NOT_CONFIGURED" };
  }

  const ipHash = input.ip ? hashVoterKey(`ip:${input.ip}`) : undefined;
  const title =
    (input.title?.trim() || input.message.trim().slice(0, 80)) ?? "Feedback";

  try {
    const row = await prisma.customerFeedback.create({
      data: {
        kind: input.kind,
        title: title.slice(0, 160),
        message: input.message.trim().slice(0, 4000),
        email: input.email?.trim().toLowerCase() || null,
        csatScore:
          typeof input.rating === "number" &&
          input.rating >= 1 &&
          input.rating <= 5
            ? input.rating
            : null,
        userId: input.userId || null,
        ipHash: ipHash || null,
        source: input.source || "/feedback",
        status: "received",
        voteCount: 0,
        isPublic: true,
      },
      select: {
        id: true,
        kind: true,
        title: true,
        status: true,
        voteCount: true,
        createdAt: true,
      },
    });

    await logSystemEvent({
      level: "info",
      source: "product.feedback",
      message: `${input.kind} feedback stored`,
      metadata: {
        id: row.id,
        kind: input.kind,
        rating: input.rating ?? null,
        email: input.email || null,
      },
    });

    return { ok: true as const, item: row };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Persist failed";
    return { ok: false as const, error: message, code: "FEEDBACK_PERSIST_FAILED" };
  }
}

export async function listPublicFeedback(limit = 50) {
  if (!isPrismaConfigured()) return [];
  try {
    return await prisma.customerFeedback.findMany({
      where: { isPublic: true },
      orderBy: [{ voteCount: "desc" }, { createdAt: "desc" }],
      take: Math.min(Math.max(limit, 1), 100),
      select: {
        id: true,
        kind: true,
        title: true,
        message: true,
        status: true,
        voteCount: true,
        createdAt: true,
      },
    });
  } catch {
    return [];
  }
}

export async function voteOnFeedback(feedbackId: string, voterRaw: string) {
  if (!isPrismaConfigured()) {
    return { ok: false as const, error: "Database not configured.", code: "DB_NOT_CONFIGURED" };
  }
  const voterKey = hashVoterKey(voterRaw);
  try {
    const existing = await prisma.feedbackVote.findUnique({
      where: {
        feedbackId_voterKey: { feedbackId, voterKey },
      },
    });
    if (existing) {
      const item = await prisma.customerFeedback.findUnique({
        where: { id: feedbackId },
        select: { id: true, voteCount: true },
      });
      return {
        ok: true as const,
        alreadyVoted: true,
        voteCount: item?.voteCount ?? 0,
      };
    }

    const updated = await prisma.$transaction(async (tx) => {
      await tx.feedbackVote.create({
        data: { feedbackId, voterKey },
      });
      return tx.customerFeedback.update({
        where: { id: feedbackId },
        data: { voteCount: { increment: 1 } },
        select: { id: true, voteCount: true },
      });
    });

    return {
      ok: true as const,
      alreadyVoted: false,
      voteCount: updated.voteCount,
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Vote failed";
    return { ok: false as const, error: message, code: "VOTE_FAILED" };
  }
}
