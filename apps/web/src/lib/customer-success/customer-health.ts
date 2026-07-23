/**
 * Customer Health Dashboard — computed from the signed-in user's real data only.
 * Risk levels are rule-based heuristics, not ML predictions or fabricated scores.
 */

import { isPrismaConfigured, prisma } from "@/lib/prisma";
import {
  buildChurnSignals,
  type ChurnSignal,
  type RiskLevel,
} from "@/lib/customer-success/churn-prevention";

export type UsageTrendPoint = {
  date: string;
  generations: number;
  creditsCharged: number;
};

export type CustomerHealthSnapshot = {
  userId: string;
  email: string | null;
  accountAgeDays: number;
  createdAt: string;
  emailVerified: boolean;
  subscription: {
    tier: string;
    active: boolean;
    renewsAt: string | null;
    creditsExpireAt: string | null;
  };
  credits: number;
  projectCount: number;
  videoCount: number;
  completedVideoCount: number;
  openTicketCount: number;
  totalTicketCount: number;
  lastLoginAt: string | null;
  lastGenerationAt: string | null;
  usageTrend: UsageTrendPoint[];
  riskLevel: RiskLevel;
  riskScore: number;
  signals: ChurnSignal[];
  recommendations: string[];
  computedAt: string;
};

function daysBetween(from: Date, to: Date): number {
  return Math.max(0, Math.floor((to.getTime() - from.getTime()) / 86_400_000));
}

function startOfUtcDay(d: Date): Date {
  return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
}

export async function getCustomerHealth(
  userId: string
): Promise<CustomerHealthSnapshot | null> {
  if (!isPrismaConfigured()) return null;

  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: {
      id: true,
      email: true,
      emailVerified: true,
      createdAt: true,
      lastLoginAt: true,
      tier: true,
      credits: true,
      subscriptionActive: true,
      subscriptionRenewsAt: true,
      creditsExpireAt: true,
    },
  });
  if (!user) return null;

  const now = new Date();
  const trendStart = new Date(now.getTime() - 13 * 86_400_000);
  trendStart.setUTCHours(0, 0, 0, 0);

  const [
    projectCount,
    videoCount,
    completedVideoCount,
    openTicketCount,
    totalTicketCount,
    latestJob,
    recentJobs,
    failedPaymentCount,
  ] = await Promise.all([
    prisma.project.count({ where: { userId } }),
    prisma.generationJob.count({ where: { userId } }),
    prisma.generationJob.count({
      where: { userId, status: "COMPLETED" },
    }),
    prisma.supportTicket.count({
      where: {
        userId,
        status: { in: ["open", "in_progress", "waiting_on_customer"] },
      },
    }),
    prisma.supportTicket.count({ where: { userId } }),
    prisma.generationJob.findFirst({
      where: { userId },
      orderBy: { createdAt: "desc" },
      select: { createdAt: true },
    }),
    prisma.generationJob.findMany({
      where: { userId, createdAt: { gte: trendStart } },
      select: { createdAt: true, creditsCharged: true },
      orderBy: { createdAt: "asc" },
    }),
    prisma.billingTransaction.count({
      where: {
        userId,
        OR: [
          { status: { in: ["failed", "payment_failed", "past_due"] } },
          { eventType: { contains: "payment_failed" } },
          { eventType: { contains: "subscription.canceled" } },
        ],
      },
    }),
  ]);

  const usageMap = new Map<string, UsageTrendPoint>();
  for (let i = 0; i < 14; i++) {
    const d = new Date(trendStart.getTime() + i * 86_400_000);
    const key = startOfUtcDay(d).toISOString().slice(0, 10);
    usageMap.set(key, { date: key, generations: 0, creditsCharged: 0 });
  }
  for (const job of recentJobs) {
    const key = startOfUtcDay(job.createdAt).toISOString().slice(0, 10);
    const row = usageMap.get(key);
    if (row) {
      row.generations += 1;
      row.creditsCharged += job.creditsCharged ?? 0;
    }
  }
  const usageTrend = Array.from(usageMap.values());

  const lastGen = latestJob?.createdAt ?? null;
  const lastActivity = [user.lastLoginAt, lastGen]
    .filter(Boolean)
    .sort((a, b) => (b as Date).getTime() - (a as Date).getTime())[0] as
    | Date
    | undefined;

  const { riskLevel, riskScore, signals, recommendations } = buildChurnSignals({
    now,
    createdAt: user.createdAt,
    lastLoginAt: user.lastLoginAt,
    lastGenerationAt: lastGen,
    lastActivityAt: lastActivity ?? null,
    credits: user.credits,
    tier: user.tier,
    subscriptionActive: user.subscriptionActive,
    creditsExpireAt: user.creditsExpireAt,
    emailVerified: user.emailVerified,
    projectCount,
    completedVideoCount,
    openTicketCount,
    failedPaymentCount,
    recentGenerationCount: recentJobs.length,
  });

  return {
    userId: user.id,
    email: user.email,
    accountAgeDays: daysBetween(user.createdAt, now),
    createdAt: user.createdAt.toISOString(),
    emailVerified: user.emailVerified,
    subscription: {
      tier: user.tier,
      active: user.subscriptionActive,
      renewsAt: user.subscriptionRenewsAt?.toISOString() ?? null,
      creditsExpireAt: user.creditsExpireAt?.toISOString() ?? null,
    },
    credits: user.credits,
    projectCount,
    videoCount,
    completedVideoCount,
    openTicketCount,
    totalTicketCount,
    lastLoginAt: user.lastLoginAt?.toISOString() ?? null,
    lastGenerationAt: lastGen?.toISOString() ?? null,
    usageTrend,
    riskLevel,
    riskScore,
    signals,
    recommendations,
    computedAt: now.toISOString(),
  };
}
