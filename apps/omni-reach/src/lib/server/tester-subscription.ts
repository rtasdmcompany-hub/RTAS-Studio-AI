import type { SubscriptionActivatedPayload } from "@rtas/shared";
import {
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
} from "@rtas/shared";
import { prisma, isPrismaConfigured } from "@/lib/prisma";

const TESTER_ALLOWED_SECONDS = 30;
export const TESTER_LIMIT_REACHED_MESSAGE =
  "Generation blocked. Tester tier limits reached ($5 for 5 Days / 30s max processing time).";

function testerEndDate(payload: SubscriptionActivatedPayload): Date {
  if (payload.billingPeriodEnd) {
    return new Date(payload.billingPeriodEnd);
  }
  const end = new Date();
  end.setDate(end.getDate() + TESTER_DURATION_DAYS);
  return end;
}

/**
 * Persist the $5 / 5-day Tester plan to Postgres (TesterSubscription table).
 * No-op when DATABASE_URL is not configured.
 */
export async function upsertTesterSubscriptionFromWebhook(
  userId: string,
  payload: SubscriptionActivatedPayload
): Promise<void> {
  if (!isPrismaConfigured()) return;

  const endDate = testerEndDate(payload);
  const sessionId =
    payload.paymentId ??
    payload.externalSubscriptionId ??
    payload.externalCustomerId;

  await prisma.testerSubscription.upsert({
    where: { userId },
    create: {
      userId,
      planType: "TESTER",
      pricePaid: TESTER_PRICE_USD,
      allowedSeconds: TESTER_ALLOWED_SECONDS,
      secondsUsed: 0,
      startDate: new Date(),
      endDate,
      isActive: true,
      stripeSessionId: sessionId || null,
    },
    update: {
      planType: "TESTER",
      pricePaid: TESTER_PRICE_USD,
      allowedSeconds: TESTER_ALLOWED_SECONDS,
      secondsUsed: 0,
      startDate: new Date(),
      endDate,
      isActive: true,
      stripeSessionId: sessionId || undefined,
    },
  });
}

export async function getActiveTesterSubscription(userId: string) {
  if (!isPrismaConfigured()) return null;

  const sub = await getTesterSubscription(userId);

  if (!sub || !sub.isActive) return null;
  if (sub.endDate < new Date()) return null;
  if (sub.secondsUsed >= sub.allowedSeconds) return null;

  return sub;
}

export async function getTesterSubscription(userId: string) {
  if (!isPrismaConfigured()) return null;

  return prisma.testerSubscription.findUnique({
    where: { userId },
  });
}

export async function assertTesterGenerationAllowed(
  userId: string,
  requestedDurationSeconds: number
): Promise<void> {
  if (!isPrismaConfigured()) return;

  const sub = await getTesterSubscription(userId);
  if (!sub) return;

  const remainingSeconds = Math.max(0, sub.allowedSeconds - sub.secondsUsed);
  const expired = sub.endDate <= new Date();
  const inactive = !sub.isActive || expired;

  if (inactive || remainingSeconds <= 0 || requestedDurationSeconds > remainingSeconds) {
    throw new Error(TESTER_LIMIT_REACHED_MESSAGE);
  }
}

export async function incrementTesterSecondsUsed(
  userId: string,
  processedDurationSeconds: number
): Promise<void> {
  if (!isPrismaConfigured()) return;
  if (!Number.isFinite(processedDurationSeconds) || processedDurationSeconds <= 0) return;

  const sub = await getTesterSubscription(userId);
  if (!sub) return;

  const nextSecondsUsed = sub.secondsUsed + Math.max(0, Math.round(processedDurationSeconds));
  const shouldStayActive =
    sub.isActive && sub.endDate > new Date() && nextSecondsUsed < sub.allowedSeconds;

  await prisma.testerSubscription.update({
    where: { userId },
    data: {
      secondsUsed: nextSecondsUsed,
      isActive: shouldStayActive,
    },
  });
}

export async function resetTesterSubscriptionForDev(userId: string) {
  if (!isPrismaConfigured()) return null;

  const sub = await getTesterSubscription(userId);
  if (!sub) return null;

  const endDate = new Date();
  endDate.setDate(endDate.getDate() + TESTER_DURATION_DAYS);

  return prisma.testerSubscription.update({
    where: { userId },
    data: {
      secondsUsed: 0,
      endDate,
      isActive: true,
    },
  });
}
