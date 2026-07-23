/**
 * Phase 13 Sprint 7 — Executive BI aggregates.
 * Real database counts only. Zeros are valid. Never invent revenue or growth.
 */

import {
  PREMIUM_PRICE_USD,
  STANDARD_PRICE_USD,
  TESTER_PRICE_USD,
} from "@rtas/shared";
import { prisma, isPrismaConfigured } from "@/lib/prisma";
import { getEnterpriseDashboardMetrics } from "@/lib/enterprise/crm";
import { fetchAdminDashboardMetrics } from "@/lib/server/admin/metrics";
import { fetchRevenueOpsMetrics } from "@/lib/server/admin/revenue-metrics";

const MS_DAY = 24 * 60 * 60 * 1000;

const RUNNING_STATUSES = [
  "QUEUED",
  "PREPARING",
  "GENERATING",
  "GENERATING_CHUNKS",
  "RENDERING",
  "COMPILING_MEDIA",
  "UPLOADING",
] as const;

export type PeriodKey = "daily" | "weekly" | "monthly" | "quarterly" | "yearly";

function startOfDay(d = new Date()): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function periodBounds(period: PeriodKey, now = new Date()): {
  currentStart: Date;
  previousStart: Date;
  previousEnd: Date;
  label: string;
} {
  const today = startOfDay(now);
  switch (period) {
    case "daily": {
      const currentStart = today;
      const previousStart = new Date(today.getTime() - MS_DAY);
      return {
        currentStart,
        previousStart,
        previousEnd: currentStart,
        label: "Day",
      };
    }
    case "weekly": {
      const currentStart = new Date(today.getTime() - 7 * MS_DAY);
      const previousStart = new Date(today.getTime() - 14 * MS_DAY);
      return {
        currentStart,
        previousStart,
        previousEnd: currentStart,
        label: "7 days",
      };
    }
    case "monthly": {
      const currentStart = new Date(now.getFullYear(), now.getMonth(), 1);
      const previousStart = new Date(now.getFullYear(), now.getMonth() - 1, 1);
      return {
        currentStart,
        previousStart,
        previousEnd: currentStart,
        label: "Month-to-date",
      };
    }
    case "quarterly": {
      const q = Math.floor(now.getMonth() / 3);
      const currentStart = new Date(now.getFullYear(), q * 3, 1);
      const previousStart = new Date(now.getFullYear(), q * 3 - 3, 1);
      return {
        currentStart,
        previousStart,
        previousEnd: currentStart,
        label: "Quarter-to-date",
      };
    }
    case "yearly": {
      const currentStart = new Date(now.getFullYear(), 0, 1);
      const previousStart = new Date(now.getFullYear() - 1, 0, 1);
      return {
        currentStart,
        previousStart,
        previousEnd: currentStart,
        label: "Year-to-date",
      };
    }
  }
}

function pctChange(current: number, previous: number): number | null {
  if (previous === 0) return current === 0 ? 0 : null;
  return Math.round(((current - previous) / previous) * 1000) / 10;
}

function safeDiv(n: number, d: number): number | null {
  if (d <= 0) return null;
  return Math.round((n / d) * 1000) / 10;
}

export type ExecutiveKpis = {
  mrrUsd: number;
  arrUsd: number;
  newUsers: number;
  activeUsersProxy: number;
  paidUsers: number;
  enterpriseLeads: number;
  generationsTotal: number;
  generationsToday: number;
  creditRemaining: number;
  creditConsumed: number;
  revenueByPlan: Array<{
    plan: string;
    activeCount: number;
    mrrContributionUsd: number;
    note: string;
  }>;
  growth: {
    newUsersToday: number;
    newUsersThisMonth: number;
    signupToPaidPct: number | null;
    activationPct: number | null;
  };
  conversion: {
    verifiedPct: number | null;
    paidOfVerifiedPct: number | null;
  };
  churn: {
    cancelledApprox: number;
    churnRatePct: number | null;
    note: string;
  };
  ltv: {
    estimateUsd: number | null;
    note: string;
  };
  arpu: {
    paidUsd: number | null;
    allUsersUsd: number | null;
  };
  systemHealth: {
    database: boolean;
    queueDepth: number;
    runningJobs: number;
    failedJobs24h: number;
    successRatePct: number;
    avgGenerationSeconds: number | null;
    gpuUtilization: "N/A";
    timestamp: string;
  };
  integrityNote: string;
  generatedAt: string;
  dataGaps: string[];
};

export async function fetchExecutiveKpis(): Promise<ExecutiveKpis> {
  if (!isPrismaConfigured()) {
    throw new Error("Database not configured.");
  }

  const now = new Date();
  const todayStart = startOfDay(now);
  const dayAgo = new Date(now.getTime() - MS_DAY);
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
  const activeProxySince = new Date(now.getTime() - 30 * MS_DAY);

  const [
    ops,
    rev,
    enterprise,
    generationsToday,
    activeUsersProxy,
    cancelledApprox,
    failedJobs24h,
    queued,
    running,
  ] = await Promise.all([
    fetchAdminDashboardMetrics(),
    fetchRevenueOpsMetrics(),
    getEnterpriseDashboardMetrics(),
    prisma.generationJob.count({ where: { createdAt: { gte: todayStart } } }),
    prisma.user.count({
      where: {
        OR: [
          { generationJobs: { some: { createdAt: { gte: activeProxySince } } } },
          { updatedAt: { gte: activeProxySince } },
        ],
      },
    }),
    prisma.user.count({
      where: {
        subscriptionActive: false,
        NOT: { paymentProvider: null },
      },
    }),
    prisma.generationJob.count({
      where: { status: "FAILED", createdAt: { gte: dayAgo } },
    }),
    prisma.generationJob.count({ where: { status: "QUEUED" } }),
    prisma.generationJob.count({
      where: { status: { in: [...RUNNING_STATUSES] } },
    }),
  ]);

  const paidUsers = rev.paid.anyPaidSignal;
  const totalUsers = rev.signups.total;
  const verified = rev.verified.count;
  const firstVideo = rev.lifecycleCounts.find((l) => l.stage === "first_video")
    ?.count ?? 0;

  const mrrUsd = rev.revenue.mrrUsd;
  const paidActive =
    rev.paid.standardActive + rev.paid.premiumActive ||
    rev.paid.activeSubscriptions;

  const arpuPaid =
    paidActive > 0 ? Math.round((mrrUsd / paidActive) * 100) / 100 : null;
  const arpuAll =
    totalUsers > 0 ? Math.round((mrrUsd / totalUsers) * 100) / 100 : null;

  // Simple LTV proxy: ARPU / monthly churn rate when measurable; else N/A.
  const churnDenom = paidUsers + cancelledApprox;
  const churnRatePct = safeDiv(cancelledApprox, churnDenom);
  let ltvEstimate: number | null = null;
  let ltvNote =
    "LTV requires stable churn history. Shown only when paid ARPU and a non-zero cancelled cohort exist.";
  if (arpuPaid !== null && churnRatePct !== null && churnRatePct > 0) {
    const monthlyChurn = churnRatePct / 100;
    ltvEstimate = Math.round((arpuPaid / monthlyChurn) * 100) / 100;
    ltvNote =
      "Proxy LTV = paid ARPU ÷ (cancelled / (paid+cancelled)). Not investor-grade cohort LTV.";
  } else if (arpuPaid !== null) {
    ltvNote =
      "Paid ARPU available; churn cohort too thin for LTV — marked N/A.";
  }

  const dataGaps: string[] = [
    "GPU utilization is not instrumented — shown as N/A.",
    "Session analytics (DAU from auth sessions) not stored — active users use 30d generation/update proxy.",
    "Marketing CAC / ad spend not in DB — not shown.",
  ];
  if (rev.revenue.ledgerCollectedUsd === 0 && mrrUsd === 0) {
    dataGaps.push(
      "Billing ledger and active recurring subscriptions are currently empty (zeros are real)."
    );
  }

  return {
    mrrUsd,
    arrUsd: rev.revenue.arrUsd,
    newUsers: rev.signups.newThisMonth,
    activeUsersProxy,
    paidUsers,
    enterpriseLeads: enterprise.totalLeads,
    generationsTotal: ops.jobs.total,
    generationsToday,
    creditRemaining: ops.credits.totalRemaining,
    creditConsumed: ops.credits.totalUsedEstimate,
    revenueByPlan: [
      {
        plan: "premium",
        activeCount: rev.paid.premiumActive,
        mrrContributionUsd: rev.paid.premiumActive * PREMIUM_PRICE_USD,
        note: `$${PREMIUM_PRICE_USD}/mo list × active`,
      },
      {
        plan: "standard",
        activeCount: rev.paid.standardActive,
        mrrContributionUsd: rev.paid.standardActive * STANDARD_PRICE_USD,
        note: `$${STANDARD_PRICE_USD}/mo list × active`,
      },
      {
        plan: "tester",
        activeCount: rev.paid.testerAccounts,
        mrrContributionUsd: 0,
        note: `$${TESTER_PRICE_USD} one-time — excluded from MRR (est. $${rev.paid.testerAccounts * TESTER_PRICE_USD})`,
      },
    ],
    growth: {
      newUsersToday: rev.signups.newToday,
      newUsersThisMonth: rev.signups.newThisMonth,
      signupToPaidPct: safeDiv(paidUsers, totalUsers),
      activationPct: safeDiv(firstVideo, totalUsers),
    },
    conversion: {
      verifiedPct: safeDiv(verified, totalUsers),
      paidOfVerifiedPct: safeDiv(paidUsers, verified),
    },
    churn: {
      cancelledApprox,
      churnRatePct,
      note: "Cancelled ≈ users with paymentProvider set and subscriptionActive=false. Not MoR-native churn.",
    },
    ltv: {
      estimateUsd: ltvEstimate,
      note: ltvNote,
    },
    arpu: {
      paidUsd: arpuPaid,
      allUsersUsd: arpuAll,
    },
    systemHealth: {
      database: true,
      queueDepth: queued,
      runningJobs: running,
      failedJobs24h,
      successRatePct: ops.jobs.successRate,
      avgGenerationSeconds: ops.jobs.avgGenerationSeconds,
      gpuUtilization: "N/A",
      timestamp: now.toISOString(),
    },
    integrityNote:
      "All figures are live Prisma aggregates. MRR = Standard×$89 + Premium×$249 for subscriptionActive accounts. Zeros mean no rows yet — never fabricated.",
    generatedAt: now.toISOString(),
    dataGaps,
  };
}

export type RevenuePeriodReport = {
  period: PeriodKey;
  label: string;
  current: {
    start: string;
    end: string;
    signups: number;
    generations: number;
    creditsCharged: number;
    ledgerRevenueUsd: number;
    paymentFailures: number;
  };
  previous: {
    start: string;
    end: string;
    signups: number;
    generations: number;
    creditsCharged: number;
    ledgerRevenueUsd: number;
    paymentFailures: number;
  };
  deltaPct: {
    signups: number | null;
    generations: number | null;
    creditsCharged: number | null;
    ledgerRevenueUsd: number | null;
  };
  mrrSnapshotUsd: number;
  integrityNote: string;
};

export async function fetchRevenuePeriodReport(
  period: PeriodKey
): Promise<RevenuePeriodReport> {
  if (!isPrismaConfigured()) throw new Error("Database not configured.");

  const now = new Date();
  const bounds = periodBounds(period, now);

  async function slice(from: Date, to: Date) {
    const [signups, generations, credits, ledger, failures] = await Promise.all([
      prisma.user.count({
        where: { createdAt: { gte: from, lt: to } },
      }),
      prisma.generationJob.count({
        where: { createdAt: { gte: from, lt: to } },
      }),
      prisma.generationJob.aggregate({
        where: { createdAt: { gte: from, lt: to } },
        _sum: { creditsCharged: true },
      }),
      prisma.billingTransaction.aggregate({
        where: {
          createdAt: { gte: from, lt: to },
          status: { in: ["completed", "paid", "success"] },
        },
        _sum: { amountUsd: true },
      }),
      prisma.billingTransaction.count({
        where: {
          createdAt: { gte: from, lt: to },
          OR: [
            { status: { in: ["failed", "error", "declined"] } },
            { eventType: { contains: "fail" } },
            { eventType: { contains: "payment_failed" } },
          ],
        },
      }),
    ]);
    return {
      start: from.toISOString(),
      end: to.toISOString(),
      signups,
      generations,
      creditsCharged: credits._sum.creditsCharged ?? 0,
      ledgerRevenueUsd: ledger._sum.amountUsd ?? 0,
      paymentFailures: failures,
    };
  }

  const [current, previous, mrr] = await Promise.all([
    slice(bounds.currentStart, now),
    slice(bounds.previousStart, bounds.previousEnd),
    fetchRevenueOpsMetrics(),
  ]);

  return {
    period,
    label: bounds.label,
    current,
    previous,
    deltaPct: {
      signups: pctChange(current.signups, previous.signups),
      generations: pctChange(current.generations, previous.generations),
      creditsCharged: pctChange(current.creditsCharged, previous.creditsCharged),
      ledgerRevenueUsd: pctChange(
        current.ledgerRevenueUsd,
        previous.ledgerRevenueUsd
      ),
    },
    mrrSnapshotUsd: mrr.revenue.mrrUsd,
    integrityNote:
      "Period revenue uses BillingTransaction sums when present; MRR snapshot is list-price × active Standard/Premium. Empty periods return zeros.",
  };
}

export type CustomerAnalytics = {
  registrations: {
    total: number;
    today: number;
    week: number;
    month: number;
    verified: number;
    unverified: number;
  };
  activation: {
    usersWithCompletedVideo: number;
    activationRatePct: number | null;
  };
  retention: {
    active30dProxy: number;
    note: string;
  };
  upgrades: {
    standardActive: number;
    premiumActive: number;
    note: string;
  };
  cancellations: {
    cancelledApprox: number;
    note: string;
  };
  sessions: {
    status: "N/A";
    note: string;
  };
  projects: number;
  videosCompleted: number;
  credits: {
    remaining: number;
    charged: number;
    usersWithZero: number;
  };
  generatedAt: string;
};

export async function fetchCustomerAnalytics(): Promise<CustomerAnalytics> {
  if (!isPrismaConfigured()) throw new Error("Database not configured.");

  const now = new Date();
  const today = startOfDay(now);
  const week = new Date(now.getTime() - 7 * MS_DAY);
  const month = new Date(now.getFullYear(), now.getMonth(), 1);
  const activeSince = new Date(now.getTime() - 30 * MS_DAY);

  const [
    total,
    todayCount,
    weekCount,
    monthCount,
    verified,
    withVideo,
    active30d,
    standard,
    premium,
    cancelled,
    projects,
    videosCompleted,
    creditSum,
    charged,
    zeroCredits,
  ] = await Promise.all([
    prisma.user.count(),
    prisma.user.count({ where: { createdAt: { gte: today } } }),
    prisma.user.count({ where: { createdAt: { gte: week } } }),
    prisma.user.count({ where: { createdAt: { gte: month } } }),
    prisma.user.count({ where: { emailVerified: true } }),
    prisma.user.count({
      where: { generationJobs: { some: { status: "COMPLETED" } } },
    }),
    prisma.user.count({
      where: {
        generationJobs: { some: { createdAt: { gte: activeSince } } },
      },
    }),
    prisma.user.count({
      where: { tier: "standard", subscriptionActive: true },
    }),
    prisma.user.count({
      where: { tier: "premium", subscriptionActive: true },
    }),
    prisma.user.count({
      where: {
        subscriptionActive: false,
        NOT: { paymentProvider: null },
      },
    }),
    prisma.project.count(),
    prisma.generationJob.count({ where: { status: "COMPLETED" } }),
    prisma.user.aggregate({ _sum: { credits: true } }),
    prisma.generationJob.aggregate({ _sum: { creditsCharged: true } }),
    prisma.user.count({ where: { credits: { lte: 0 } } }),
  ]);

  return {
    registrations: {
      total,
      today: todayCount,
      week: weekCount,
      month: monthCount,
      verified,
      unverified: Math.max(0, total - verified),
    },
    activation: {
      usersWithCompletedVideo: withVideo,
      activationRatePct: safeDiv(withVideo, total),
    },
    retention: {
      active30dProxy: active30d,
      note: "Proxy: distinct users with ≥1 GenerationJob in last 30 days (not session-based).",
    },
    upgrades: {
      standardActive: standard,
      premiumActive: premium,
      note: "Active Standard/Premium counts — upgrade path events not stored as a separate ledger.",
    },
    cancellations: {
      cancelledApprox: cancelled,
      note: "paymentProvider set + subscriptionActive=false.",
    },
    sessions: {
      status: "N/A",
      note: "No first-party session store; browser analytics vendors optional / detect-only.",
    },
    projects,
    videosCompleted,
    credits: {
      remaining: creditSum._sum.credits ?? 0,
      charged: charged._sum.creditsCharged ?? 0,
      usersWithZero: zeroCredits,
    },
    generatedAt: now.toISOString(),
  };
}

export type AiUsageAnalytics = {
  generationsPerDay: Array<{ date: string; count: number }>;
  avgRenderSeconds: number | null;
  gpuUtilization: "N/A";
  queue: { queued: number; running: number };
  creditsChargedPeriod: number;
  popularProviders: Array<{ provider: string; count: number }>;
  failureRatePct: number | null;
  retryJobs: number;
  retryRatePct: number | null;
  totalJobsPeriod: number;
  completed: number;
  failed: number;
  periodDays: number;
  generatedAt: string;
  dataGaps: string[];
};

export async function fetchAiUsageAnalytics(
  days = 30
): Promise<AiUsageAnalytics> {
  if (!isPrismaConfigured()) throw new Error("Database not configured.");

  const clamped = Math.min(90, Math.max(7, days));
  const since = new Date(Date.now() - clamped * MS_DAY);

  const [
    jobs,
    completedTiming,
    queued,
    running,
    completed,
    failed,
    retryJobs,
    providerGroups,
    credits,
  ] = await Promise.all([
    prisma.generationJob.findMany({
      where: { createdAt: { gte: since } },
      select: { createdAt: true },
    }),
    prisma.generationJob.findMany({
      where: {
        status: "COMPLETED",
        startedAt: { not: null },
        completedAt: { not: null },
        createdAt: { gte: since },
      },
      take: 500,
      orderBy: { completedAt: "desc" },
      select: { startedAt: true, completedAt: true },
    }),
    prisma.generationJob.count({ where: { status: "QUEUED" } }),
    prisma.generationJob.count({
      where: { status: { in: [...RUNNING_STATUSES] } },
    }),
    prisma.generationJob.count({
      where: { status: "COMPLETED", createdAt: { gte: since } },
    }),
    prisma.generationJob.count({
      where: { status: "FAILED", createdAt: { gte: since } },
    }),
    prisma.generationJob.count({
      where: { retryCount: { gt: 0 }, createdAt: { gte: since } },
    }),
    prisma.generationJob.groupBy({
      by: ["provider"],
      where: { createdAt: { gte: since } },
      _count: { _all: true },
    }),
    prisma.generationJob.aggregate({
      where: { createdAt: { gte: since } },
      _sum: { creditsCharged: true },
    }),
  ]);

  const dayMap = new Map<string, number>();
  for (const j of jobs) {
    const key = j.createdAt.toISOString().slice(0, 10);
    dayMap.set(key, (dayMap.get(key) ?? 0) + 1);
  }
  const generationsPerDay = [...dayMap.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({ date, count }));

  const durations = completedTiming
    .map((j) => {
      if (!j.startedAt || !j.completedAt) return null;
      return (j.completedAt.getTime() - j.startedAt.getTime()) / 1000;
    })
    .filter((n): n is number => n !== null && n > 0);
  const avgRenderSeconds =
    durations.length > 0
      ? Math.round(
          (durations.reduce((a, b) => a + b, 0) / durations.length) * 10
        ) / 10
      : null;

  const finished = completed + failed;
  const totalJobsPeriod = jobs.length;

  return {
    generationsPerDay,
    avgRenderSeconds,
    gpuUtilization: "N/A",
    queue: { queued, running },
    creditsChargedPeriod: credits._sum.creditsCharged ?? 0,
    popularProviders: providerGroups
      .map((g) => ({
        provider: g.provider ?? "(unset)",
        count: g._count._all,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 12),
    failureRatePct: safeDiv(failed, finished),
    retryJobs,
    retryRatePct: safeDiv(retryJobs, totalJobsPeriod),
    totalJobsPeriod,
    completed,
    failed,
    periodDays: clamped,
    generatedAt: new Date().toISOString(),
    dataGaps: [
      "GPU utilization not measurable from app DB.",
      "Popular templates: GenerationJob has no dedicated templateId field — provider breakdown used instead.",
    ],
  };
}

export type BusinessAnalyticsCenter = {
  revenue: Awaited<ReturnType<typeof fetchRevenueOpsMetrics>>;
  customer: CustomerAnalytics;
  usage: {
    creditRemaining: number;
    creditCharged: number;
    jobsTotal: number;
    projects: number;
  };
  generation: AiUsageAnalytics;
  infrastructure: ExecutiveKpis["systemHealth"];
  support: {
    feedbackSubmissions: number;
    commercialLeadLogs: number;
    marketingLeads: number;
    total: number;
    note: string;
  };
  enterprise: Awaited<ReturnType<typeof getEnterpriseDashboardMetrics>>;
  marketing: {
    marketingLeads: number;
    commercialLeads: number;
    newsletterSubscribers: number | null;
    note: string;
  };
  generatedAt: string;
};

export async function fetchBusinessAnalyticsCenter(): Promise<BusinessAnalyticsCenter> {
  const [revenue, customer, generation, kpis, enterprise] = await Promise.all([
    fetchRevenueOpsMetrics(),
    fetchCustomerAnalytics(),
    fetchAiUsageAnalytics(30),
    fetchExecutiveKpis(),
    getEnterpriseDashboardMetrics(),
  ]);

  let newsletter: number | null = null;
  try {
    newsletter = await prisma.newsletterSubscriber.count({
      where: { status: "subscribed" },
    });
  } catch {
    newsletter = null;
  }

  let marketingLeads = 0;
  try {
    marketingLeads = await prisma.marketingLead.count();
  } catch {
    marketingLeads = await prisma.systemLog
      .count({ where: { source: "marketing.lead" } })
      .catch(() => 0);
  }

  return {
    revenue,
    customer,
    usage: {
      creditRemaining: customer.credits.remaining,
      creditCharged: customer.credits.charged,
      jobsTotal: generation.totalJobsPeriod,
      projects: customer.projects,
    },
    generation,
    infrastructure: kpis.systemHealth,
    support: {
      feedbackSubmissions: revenue.supportTickets.feedbackSubmissions,
      commercialLeadLogs: revenue.supportTickets.commercialLeads,
      marketingLeads: revenue.supportTickets.marketingLeads,
      total: revenue.supportTickets.total,
      note: "Support ticket system not separate — counts from SystemLog + MarketingLead.",
    },
    enterprise,
    marketing: {
      marketingLeads,
      commercialLeads: revenue.supportTickets.commercialLeads,
      newsletterSubscribers: newsletter,
      note: "No ad-platform spend imported. Funnel events may exist only in structured logs.",
    },
    generatedAt: new Date().toISOString(),
  };
}
