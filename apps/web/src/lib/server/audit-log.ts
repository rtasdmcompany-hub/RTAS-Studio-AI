import { prisma, isPrismaConfigured } from "@/lib/prisma";
import type { Prisma } from "@prisma/client";

export type SystemLogInput = {
  level?: "info" | "warn" | "error";
  source: string;
  message: string;
  metadata?: Record<string, unknown>;
};

/** Persist operational events for admin monitoring (production audit trail). */
export async function logSystemEvent(input: SystemLogInput): Promise<void> {
  if (!isPrismaConfigured()) return;
  try {
    await prisma.systemLog.create({
      data: {
        level: input.level ?? "info",
        source: input.source,
        message: input.message,
        metadataJson: (input.metadata ?? undefined) as Prisma.InputJsonValue | undefined,
      },
    });
  } catch {
    /* non-blocking — never fail user flows for logging */
  }
}

export async function logLoginActivity(input: {
  userId?: string;
  email?: string;
  provider: string;
  ip?: string;
  userAgent?: string;
  success: boolean;
}): Promise<void> {
  await logSystemEvent({
    level: input.success ? "info" : "warn",
    source: "auth.login",
    message: input.success
      ? `Sign-in succeeded (${input.provider})`
      : `Sign-in blocked (${input.provider})`,
    metadata: {
      userId: input.userId,
      email: input.email,
      provider: input.provider,
      ip: input.ip,
      userAgent: input.userAgent?.slice(0, 200),
      success: input.success,
    },
  });

  if (input.success && input.userId && isPrismaConfigured()) {
    try {
      await prisma.user.update({
        where: { id: input.userId },
        data: { lastLoginAt: new Date() },
      });
    } catch {
      /* non-blocking */
    }
  }
}

export async function logAdminActivity(input: {
  actorId: string;
  action: string;
  detail?: string;
  metadata?: Record<string, unknown>;
}): Promise<void> {
  if (!isPrismaConfigured()) return;
  try {
    await prisma.adminActivity.create({
      data: {
        actorId: input.actorId,
        action: input.action,
        detail: input.detail,
        metadataJson: (input.metadata ?? undefined) as Prisma.InputJsonValue | undefined,
      },
    });
  } catch {
    /* ignore */
  }
}
