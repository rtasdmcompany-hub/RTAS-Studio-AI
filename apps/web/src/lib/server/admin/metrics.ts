import {
  PREMIUM_PRICE_USD,
  STANDARD_PRICE_USD,
  TESTER_PRICE_USD,
} from "@rtas/shared";
import { prisma, isPrismaConfigured } from "@/lib/prisma";

const MS_DAY = 24 * 60 * 60 * 1000;

function startOfDay(d = new Date()): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

export type AdminDashboardMetrics = {
  users: {
    total: number;
    verified: number;
    activeSubscriptions: number;
    newToday: number;
    newThisMonth: number;
  };
  jobs: {
    total: number;
    queued: number;
    running: number;
    completed: number;
    failed: number;
    successRate: number;
    avgGenerationSeconds: number | null;
  };
  credits: {
    totalRemaining: number;
    totalUsedEstimate: number;
  };
  revenue: {
    mrrEstimateUsd: number;
    arrEstimateUsd: number;
    testerPurchasesEstimate: number;
  };
  recentUsers: Array<{
    id: string;
    email: string;
    name: string | null;
    tier: string;
    credits: number;
    createdAt: string;
    subscriptionActive: boolean;
  }>;
  recentJobs: Array<{
    id: string;
    userId: string;
    status: string;
    progressPercent: number;
    durationSeconds: number;
    creditsCharged: number;
    createdAt: string;
    errorMessage: string | null;
  }>;
  recentLogins: Array<{
    id: string;
    message: string;
    createdAt: string;
    metadata: unknown;
  }>;
  systemHealth: {
    database: boolean;
    timestamp: string;
  };
};

export async function fetchAdminDashboardMetrics(): Promise<AdminDashboardMetrics> {
  if (!isPrismaConfigured()) {
    throw new Error("Database not configured.");
  }

  const now = new Date();
  const todayStart = startOfDay(now);
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
  const runningStatuses = [
    "QUEUED",
    "PREPARING",
    "GENERATING",
    "GENERATING_CHUNKS",
    "RENDERING",
    "COMPILING_MEDIA",
    "UPLOADING",
  ] as const;

  const [
    totalUsers,
    verifiedUsers,
    activeSubscriptions,
    newToday,
    newThisMonth,
    totalJobs,
    queuedJobs,
    runningJobs,
    completedJobs,
    failedJobs,
    creditSum,
    creditsUsedSum,
    standardSubs,
    premiumSubs,
    testerTierUsers,
    recentUsers,
    recentJobs,
    recentLogins,
    completedWithTiming,
  ] = await Promise.all([
    prisma.user.count(),
    prisma.user.count({ where: { emailVerified: true } }),
    prisma.user.count({ where: { subscriptionActive: true } }),
    prisma.user.count({ where: { createdAt: { gte: todayStart } } }),
    prisma.user.count({ where: { createdAt: { gte: monthStart } } }),
    prisma.generationJob.count(),
    prisma.generationJob.count({ where: { status: "QUEUED" } }),
    prisma.generationJob.count({
      where: { status: { in: [...runningStatuses] } },
    }),
    prisma.generationJob.count({ where: { status: "COMPLETED" } }),
    prisma.generationJob.count({ where: { status: "FAILED" } }),
    prisma.user.aggregate({ _sum: { credits: true } }),
    prisma.generationJob.aggregate({ _sum: { creditsCharged: true } }),
    prisma.user.count({ where: { tier: "standard", subscriptionActive: true } }),
    prisma.user.count({ where: { tier: "premium", subscriptionActive: true } }),
    prisma.user.count({ where: { tier: "tester" } }),
    prisma.user.findMany({
      take: 12,
      orderBy: { createdAt: "desc" },
      select: {
        id: true,
        email: true,
        name: true,
        tier: true,
        credits: true,
        createdAt: true,
        subscriptionActive: true,
      },
    }),
    prisma.generationJob.findMany({
      take: 20,
      orderBy: { createdAt: "desc" },
      select: {
        id: true,
        userId: true,
        status: true,
        progressPercent: true,
        durationSeconds: true,
        creditsCharged: true,
        createdAt: true,
        errorMessage: true,
      },
    }),
    prisma.systemLog.findMany({
      where: { source: "auth.login" },
      take: 15,
      orderBy: { createdAt: "desc" },
      select: { id: true, message: true, createdAt: true, metadataJson: true },
    }),
    prisma.generationJob.findMany({
      where: {
        status: "COMPLETED",
        startedAt: { not: null },
        completedAt: { not: null },
      },
      take: 200,
      orderBy: { completedAt: "desc" },
      select: { startedAt: true, completedAt: true },
    }),
  ]);

  const finished = completedJobs + failedJobs;
  const successRate = finished > 0 ? completedJobs / finished : 1;

  let avgGenerationSeconds: number | null = null;
  const durations = completedWithTiming
    .map((j) => {
      if (!j.startedAt || !j.completedAt) return null;
      return (j.completedAt.getTime() - j.startedAt.getTime()) / 1000;
    })
    .filter((n): n is number => n !== null && n > 0);
  if (durations.length > 0) {
    avgGenerationSeconds =
      durations.reduce((a, b) => a + b, 0) / durations.length;
  }

  const mrrEstimateUsd =
    standardSubs * STANDARD_PRICE_USD + premiumSubs * PREMIUM_PRICE_USD;
  const arrEstimateUsd = mrrEstimateUsd * 12;

  return {
    users: {
      total: totalUsers,
      verified: verifiedUsers,
      activeSubscriptions,
      newToday,
      newThisMonth,
    },
    jobs: {
      total: totalJobs,
      queued: queuedJobs,
      running: runningJobs,
      completed: completedJobs,
      failed: failedJobs,
      successRate: Math.round(successRate * 1000) / 10,
      avgGenerationSeconds:
        avgGenerationSeconds !== null
          ? Math.round(avgGenerationSeconds * 10) / 10
          : null,
    },
    credits: {
      totalRemaining: creditSum._sum.credits ?? 0,
      totalUsedEstimate: creditsUsedSum._sum.creditsCharged ?? 0,
    },
    revenue: {
      mrrEstimateUsd,
      arrEstimateUsd,
      testerPurchasesEstimate: testerTierUsers * TESTER_PRICE_USD,
    },
    recentUsers: recentUsers.map((u) => ({
      ...u,
      createdAt: u.createdAt.toISOString(),
    })),
    recentJobs: recentJobs.map((j) => ({
      ...j,
      status: String(j.status),
      createdAt: j.createdAt.toISOString(),
    })),
    recentLogins: recentLogins.map((l) => ({
      id: l.id,
      message: l.message,
      createdAt: l.createdAt.toISOString(),
      metadata: l.metadataJson,
    })),
    systemHealth: {
      database: true,
      timestamp: now.toISOString(),
    },
  };
}

export type AnalyticsSeries = {
  dailyUsers: Array<{ date: string; count: number }>;
  dailyGenerations: Array<{ date: string; count: number }>;
  dailyCreditsUsed: Array<{ date: string; credits: number }>;
  jobStatusBreakdown: Array<{ status: string; count: number }>;
  tierBreakdown: Array<{ tier: string; count: number }>;
};

export async function fetchAnalyticsSeries(days = 30): Promise<AnalyticsSeries> {
  if (!isPrismaConfigured()) throw new Error("Database not configured.");

  const since = new Date(Date.now() - days * MS_DAY);

  const [users, jobs, creditsJobs, statusGroups, tierGroups] = await Promise.all([
    prisma.user.findMany({
      where: { createdAt: { gte: since } },
      select: { createdAt: true },
    }),
    prisma.generationJob.findMany({
      where: { createdAt: { gte: since } },
      select: { createdAt: true, status: true, creditsCharged: true },
    }),
    prisma.generationJob.findMany({
      where: { createdAt: { gte: since }, creditsCharged: { gt: 0 } },
      select: { createdAt: true, creditsCharged: true },
    }),
    prisma.generationJob.groupBy({
      by: ["status"],
      _count: { _all: true },
    }),
    prisma.user.groupBy({
      by: ["tier"],
      _count: { _all: true },
    }),
  ]);

  function bucketByDay<T extends { createdAt: Date }>(
    rows: T[],
    value: (row: T) => number
  ) {
    const map = new Map<string, number>();
    for (const row of rows) {
      const key = row.createdAt.toISOString().slice(0, 10);
      map.set(key, (map.get(key) ?? 0) + value(row));
    }
    return [...map.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, count]) => ({ date, count }));
  }

  return {
    dailyUsers: bucketByDay(users, () => 1),
    dailyGenerations: bucketByDay(jobs, () => 1),
    dailyCreditsUsed: bucketByDay(creditsJobs, (j) => j.creditsCharged).map(
      ({ date, count }) => ({ date, credits: count })
    ),
    jobStatusBreakdown: statusGroups.map((g) => ({
      status: String(g.status),
      count: g._count._all,
    })),
    tierBreakdown: tierGroups.map((g) => ({
      tier: g.tier,
      count: g._count._all,
    })),
  };
}
