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

export type RevenueOpsMetrics = {
  signups: {
    newToday: number;
    newThisWeek: number;
    newThisMonth: number;
    total: number;
  };
  verified: {
    count: number;
    unverified: number;
  };
  unpaid: {
    /** Accounts with tier=free and no active subscription (starting credits 0). */
    freeUnpaid: number;
  };
  paid: {
    activeSubscriptions: number;
    testerAccounts: number;
    standardActive: number;
    premiumActive: number;
    anyPaidSignal: number;
  };
  revenue: {
    mrrUsd: number;
    arrUsd: number;
    /** One-time Tester estimate — NOT included in MRR. */
    testerOneTimeEstimateUsd: number;
    /** Sum of completed BillingTransaction amounts (real ledger when present). */
    ledgerCollectedUsd: number;
  };
  subscriptionStatus: Array<{ status: string; count: number }>;
  creditUsage: {
    totalRemaining: number;
    totalChargedOnJobs: number;
    usersWithZeroCredits: number;
    usersWithCredits: number;
  };
  topPlans: Array<{ plan: string; count: number; mrrContributionUsd: number }>;
  recentTransactions: Array<{
    id: string;
    userId: string;
    provider: string;
    eventType: string;
    status: string;
    amountUsd: number;
    planKey: string | null;
    creditsGranted: number;
    createdAt: string;
  }>;
  supportTickets: {
    /** Feedback + commercial + marketing lead submissions logged (real counts). */
    feedbackSubmissions: number;
    commercialLeads: number;
    marketingLeads: number;
    total: number;
  };
  lifecycleCounts: Array<{ stage: string; count: number }>;
  integrityNote: string;
  generatedAt: string;
};

/**
 * Real RevOps aggregates only. Zeros are valid. Never invent revenue or tickets.
 */
export async function fetchRevenueOpsMetrics(): Promise<RevenueOpsMetrics> {
  if (!isPrismaConfigured()) {
    throw new Error("Database not configured.");
  }

  const now = new Date();
  const todayStart = startOfDay(now);
  const weekStart = new Date(now.getTime() - 7 * MS_DAY);
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

  const [
    totalUsers,
    newToday,
    newThisWeek,
    newThisMonth,
    verifiedCount,
    freeUnpaid,
    activeSubscriptions,
    testerAccounts,
    standardActive,
    premiumActive,
    creditSum,
    creditsCharged,
    zeroCreditUsers,
    usersWithCredits,
    tierGroups,
    recentTx,
    ledgerSum,
    feedbackLogs,
    commercialLogs,
    marketingLeadCount,
    verifiedFreeOnly,
    activatedApprox,
    firstVideoUsers,
    retainedApprox,
    expandedCount,
    churnedApprox,
  ] = await Promise.all([
    prisma.user.count(),
    prisma.user.count({ where: { createdAt: { gte: todayStart } } }),
    prisma.user.count({ where: { createdAt: { gte: weekStart } } }),
    prisma.user.count({ where: { createdAt: { gte: monthStart } } }),
    prisma.user.count({ where: { emailVerified: true } }),
    prisma.user.count({
      where: {
        tier: "free",
        subscriptionActive: false,
      },
    }),
    prisma.user.count({ where: { subscriptionActive: true } }),
    prisma.user.count({ where: { tier: "tester" } }),
    prisma.user.count({ where: { tier: "standard", subscriptionActive: true } }),
    prisma.user.count({ where: { tier: "premium", subscriptionActive: true } }),
    prisma.user.aggregate({ _sum: { credits: true } }),
    prisma.generationJob.aggregate({ _sum: { creditsCharged: true } }),
    prisma.user.count({ where: { credits: { lte: 0 } } }),
    prisma.user.count({ where: { credits: { gt: 0 } } }),
    prisma.user.groupBy({ by: ["tier"], _count: { _all: true } }),
    prisma.billingTransaction.findMany({
      take: 25,
      orderBy: { createdAt: "desc" },
      select: {
        id: true,
        userId: true,
        provider: true,
        eventType: true,
        status: true,
        amountUsd: true,
        planKey: true,
        creditsGranted: true,
        createdAt: true,
      },
    }),
    prisma.billingTransaction.aggregate({
      where: { status: { in: ["completed", "paid", "success"] } },
      _sum: { amountUsd: true },
    }),
    prisma.systemLog.count({ where: { source: "product.feedback" } }),
    prisma.systemLog.count({ where: { source: "commercial.lead" } }),
    (async () => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const client = prisma as any;
        const tableCount =
          client.marketingLead?.count != null
            ? await client.marketingLead.count()
            : 0;
        const logCount = await prisma.systemLog.count({
          where: { source: "marketing.lead" },
        });
        return Math.max(tableCount, logCount);
      } catch {
        return prisma.systemLog
          .count({ where: { source: "marketing.lead" } })
          .catch(() => 0);
      }
    })(),
    prisma.user.count({
      where: { emailVerified: true, tier: "free", subscriptionActive: false },
    }),
    prisma.user.count({
      where: {
        OR: [{ freeTrialUsed: true }, { hasUsedFreeTrial: true }],
      },
    }),
    prisma.user.count({
      where: {
        generationJobs: { some: { status: "COMPLETED" } },
      },
    }),
    prisma.user.count({
      where: {
        OR: [
          { subscriptionActive: true },
          { tier: { in: ["tester", "standard", "premium"] } },
        ],
        generationJobs: { some: { status: "COMPLETED" } },
      },
    }),
    prisma.user.count({
      where: {
        tier: "premium",
        subscriptionActive: true,
      },
    }),
    prisma.user.count({
      where: {
        tier: { in: ["tester", "standard", "premium"] },
        subscriptionActive: false,
        credits: { lte: 0 },
      },
    }),
  ]);

  const mrrUsd =
    standardActive * STANDARD_PRICE_USD + premiumActive * PREMIUM_PRICE_USD;
  const arrUsd = mrrUsd * 12;

  const anyPaidSignal = await prisma.user.count({
    where: {
      OR: [
        { subscriptionActive: true },
        { tier: { in: ["tester", "standard", "premium"] } },
      ],
    },
  });

  // Note: anyPaidSignal is computed after Promise.all; recompute inline above was needed earlier.
  // Kept explicit query for clarity and accuracy.

  const topPlans = [
    {
      plan: "premium",
      count: premiumActive,
      mrrContributionUsd: premiumActive * PREMIUM_PRICE_USD,
    },
    {
      plan: "standard",
      count: standardActive,
      mrrContributionUsd: standardActive * STANDARD_PRICE_USD,
    },
    {
      plan: "tester",
      count: testerAccounts,
      mrrContributionUsd: 0,
    },
    {
      plan: "free",
      count: freeUnpaid,
      mrrContributionUsd: 0,
    },
  ].sort((a, b) => b.count - a.count);

  const subscriptionStatus = [
    { status: "active", count: activeSubscriptions },
    {
      status: "inactive",
      count: Math.max(0, totalUsers - activeSubscriptions),
    },
    ...tierGroups.map((g) => ({
      status: `tier:${g.tier}`,
      count: g._count._all,
    })),
  ];

  // Lifecycle bucket counts from real DB queries (overlapping OK — not a fake funnel %)
  const unverified = Math.max(0, totalUsers - verifiedCount);
  const lifecycleCounts = [
    { stage: "signup_unverified", count: unverified },
    { stage: "verified_free", count: verifiedFreeOnly },
    { stage: "activated_approx", count: activatedApprox },
    { stage: "first_video", count: firstVideoUsers },
    { stage: "paid_signal", count: anyPaidSignal },
    { stage: "retained_paid_with_video", count: retainedApprox },
    { stage: "expanded_premium", count: expandedCount },
    { stage: "churned_or_inactive_paid", count: churnedApprox },
  ].filter((row) => row.count > 0 || totalUsers === 0);

  const marketingLeads =
    typeof marketingLeadCount === "number" ? marketingLeadCount : 0;

  return {
    signups: {
      newToday,
      newThisWeek,
      newThisMonth,
      total: totalUsers,
    },
    verified: {
      count: verifiedCount,
      unverified: Math.max(0, totalUsers - verifiedCount),
    },
    unpaid: { freeUnpaid },
    paid: {
      activeSubscriptions,
      testerAccounts,
      standardActive,
      premiumActive,
      anyPaidSignal,
    },
    revenue: {
      mrrUsd,
      arrUsd,
      testerOneTimeEstimateUsd: testerAccounts * TESTER_PRICE_USD,
      ledgerCollectedUsd: ledgerSum._sum.amountUsd ?? 0,
    },
    subscriptionStatus,
    creditUsage: {
      totalRemaining: creditSum._sum.credits ?? 0,
      totalChargedOnJobs: creditsCharged._sum.creditsCharged ?? 0,
      usersWithZeroCredits: zeroCreditUsers,
      usersWithCredits,
    },
    topPlans,
    recentTransactions: recentTx.map((t) => ({
      ...t,
      createdAt: t.createdAt.toISOString(),
    })),
    supportTickets: {
      feedbackSubmissions: feedbackLogs,
      commercialLeads: commercialLogs,
      marketingLeads,
      total: feedbackLogs + commercialLogs + marketingLeads,
    },
    lifecycleCounts,
    integrityNote:
      "All figures are live database aggregates. MRR = active Standard×$89 + Premium×$249. Tester one-time is excluded from MRR. Zeros mean no data yet — never fabricate.",
    generatedAt: now.toISOString(),
  };
}
