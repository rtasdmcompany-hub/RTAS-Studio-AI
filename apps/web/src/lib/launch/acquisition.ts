/**
 * Phase 13 Sprint 9 — Customer acquisition funnel aggregates.
 * Real DB counts or zeros. Visitors marked Ready for Integration (no inventing traffic).
 */

import { prisma, isPrismaConfigured } from "@/lib/prisma";

export type AcquisitionMetrics = {
  visitors: {
    count: number | null;
    status: "ready_for_integration" | "live";
    note: string;
  };
  registrations: number;
  verified: number;
  activated: number;
  free: number;
  paid: number;
  enterpriseLeads: number;
  sources: Array<{ source: string; count: number }>;
  funnel: Array<{ stage: string; count: number }>;
  integrityNote: string;
  generatedAt: string;
};

export async function fetchAcquisitionMetrics(): Promise<AcquisitionMetrics> {
  if (!isPrismaConfigured()) {
    throw new Error("Database not configured.");
  }

  const [
    registrations,
    verified,
    activated,
    free,
    paid,
    enterpriseLeads,
    leadSources,
  ] = await Promise.all([
    prisma.user.count(),
    prisma.user.count({ where: { emailVerified: true } }),
    prisma.user.count({
      where: {
        OR: [
          { freeTrialUsed: true },
          { hasUsedFreeTrial: true },
          { generationJobs: { some: {} } },
        ],
      },
    }),
    prisma.user.count({
      where: { tier: "free", subscriptionActive: false },
    }),
    prisma.user.count({
      where: {
        OR: [
          { subscriptionActive: true },
          { tier: { in: ["tester", "standard", "premium"] } },
        ],
      },
    }),
    prisma.enterpriseLead.count().catch(() => 0),
    prisma.enterpriseLead
      .groupBy({
        by: ["source"],
        _count: { _all: true },
      })
      .catch(() => [] as Array<{ source: string | null; _count: { _all: number } }>),
  ]);

  const sources = (leadSources as Array<{ source: string | null; _count: { _all: number } }>)
    .map((row) => ({
      source: row.source?.trim() || "unspecified",
      count: row._count._all,
    }))
    .sort((a, b) => b.count - a.count);

  const funnel = [
    { stage: "visitors", count: 0 },
    { stage: "registrations", count: registrations },
    { stage: "verified", count: verified },
    { stage: "activated", count: activated },
    { stage: "free", count: free },
    { stage: "paid", count: paid },
    { stage: "enterprise_leads", count: enterpriseLeads },
  ];

  return {
    visitors: {
      count: null,
      status: "ready_for_integration",
      note: "Site visitor analytics sink is Ready for Integration (GA4/PostHog). Displayed as null/0 — never invented.",
    },
    registrations,
    verified,
    activated,
    free,
    paid,
    enterpriseLeads,
    sources,
    funnel,
    integrityNote:
      "All counts are live Prisma aggregates or explicit zeros. No fabricated traffic, downloads, or campaign results.",
    generatedAt: new Date().toISOString(),
  };
}
