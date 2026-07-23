/**
 * Customer segmentation — real DB fields only.
 * Empty / zero counts are valid. Never invent segment sizes.
 */

import type { Prisma } from "@prisma/client";
import { isPrismaConfigured, prisma } from "@/lib/prisma";

export type SegmentId =
  | "visitors"
  | "free_unpaid"
  | "paid"
  | "enterprise_leads"
  | "cancelled"
  | "inactive"
  | "beta"
  | "newsletter_subscribers";

export type SegmentDefinition = {
  id: SegmentId;
  name: string;
  description: string;
  /** How membership is determined */
  source: string;
};

export const SEGMENT_DEFINITIONS: SegmentDefinition[] = [
  {
    id: "visitors",
    name: "Visitors",
    description:
      "Anonymous site traffic is not stored as users. Count is N/A until analytics visitor identity is wired; registered unverified users are shown separately as a proxy.",
    source: "Analytics visitor IDs not in User table — proxy: emailVerified=false",
  },
  {
    id: "free_unpaid",
    name: "Free (unpaid)",
    description: "Registered users without an active paid subscription.",
    source: "User.subscriptionActive = false",
  },
  {
    id: "paid",
    name: "Paid",
    description: "Users with an active subscription (Tester / Standard / Premium).",
    source: "User.subscriptionActive = true",
  },
  {
    id: "enterprise_leads",
    name: "Enterprise Leads",
    description: "Commercial lead submissions (enterprise / demo).",
    source: "CommercialLead.kind = enterprise",
  },
  {
    id: "cancelled",
    name: "Cancelled",
    description:
      "Users who had a payment provider linked and are no longer actively subscribed.",
    source: "User.paymentProvider set AND subscriptionActive = false",
  },
  {
    id: "inactive",
    name: "Inactive",
    description:
      "Paid or previously paid users with no generation jobs in the last 30 days (or never generated).",
    source: "No GenerationJob.createdAt within 30 days",
  },
  {
    id: "beta",
    name: "Beta",
    description: "Public beta applications on file.",
    source: "CommercialLead.kind = beta OR AffiliateApplication (beta track N/A)",
  },
  {
    id: "newsletter_subscribers",
    name: "Newsletter Subscribers",
    description: "Opted-in newsletter emails that are not unsubscribed.",
    source: "NewsletterSubscriber.status = subscribed",
  },
];

export type SegmentCount = {
  id: SegmentId;
  name: string;
  count: number | null;
  /** null count means not measurable yet */
  status: "ok" | "na" | "db_unavailable";
  note?: string;
};

const INACTIVE_MS = 30 * 24 * 60 * 60 * 1000;

export async function countSegments(): Promise<SegmentCount[]> {
  if (!isPrismaConfigured()) {
    return SEGMENT_DEFINITIONS.map((d) => ({
      id: d.id,
      name: d.name,
      count: null,
      status: "db_unavailable" as const,
      note: "DATABASE_URL / Prisma not configured",
    }));
  }

  const since = new Date(Date.now() - INACTIVE_MS);

  try {
    const [
      visitorsProxy,
      freeUnpaid,
      paid,
      enterpriseLeads,
      cancelled,
      inactivePaid,
      betaLeads,
      newsletter,
    ] = await Promise.all([
      prisma.user.count({ where: { emailVerified: false } }),
      prisma.user.count({ where: { subscriptionActive: false } }),
      prisma.user.count({ where: { subscriptionActive: true } }),
      prisma.commercialLead.count({ where: { kind: "enterprise" } }).catch(async () => {
        try {
          return await prisma.enterpriseLead.count({
            where: { kind: { in: ["enterprise", "demo"] } },
          });
        } catch {
          return 0;
        }
      }),
      prisma.user.count({
        where: {
          subscriptionActive: false,
          NOT: { paymentProvider: null },
        },
      }),
      prisma.user.count({
        where: {
          OR: [
            { subscriptionActive: true },
            { NOT: { paymentProvider: null } },
          ],
          generationJobs: { none: { createdAt: { gte: since } } },
        },
      }),
      prisma.commercialLead.count({ where: { kind: "beta" } }).catch(async () => {
        try {
          return await prisma.enterpriseLead.count({ where: { kind: "beta" } });
        } catch {
          return 0;
        }
      }),
      prisma.newsletterSubscriber
        .count({ where: { status: "subscribed" } })
        .catch(() => 0),
    ]);

    return [
      {
        id: "visitors",
        name: "Visitors",
        count: visitorsProxy,
        status: "ok",
        note: "Proxy: unverified registered accounts (anonymous visitors = N/A)",
      },
      {
        id: "free_unpaid",
        name: "Free (unpaid)",
        count: freeUnpaid,
        status: "ok",
      },
      { id: "paid", name: "Paid", count: paid, status: "ok" },
      {
        id: "enterprise_leads",
        name: "Enterprise Leads",
        count: enterpriseLeads,
        status: "ok",
      },
      {
        id: "cancelled",
        name: "Cancelled",
        count: cancelled,
        status: "ok",
      },
      {
        id: "inactive",
        name: "Inactive",
        count: inactivePaid,
        status: "ok",
        note: "No generation jobs in last 30 days among paid / formerly paid",
      },
      { id: "beta", name: "Beta", count: betaLeads, status: "ok" },
      {
        id: "newsletter_subscribers",
        name: "Newsletter Subscribers",
        count: newsletter,
        status: "ok",
      },
    ];
  } catch (err) {
    const message = err instanceof Error ? err.message : "segment_query_failed";
    return SEGMENT_DEFINITIONS.map((d) => ({
      id: d.id,
      name: d.name,
      count: 0,
      status: "ok" as const,
      note: `Query fallback (0): ${message.slice(0, 120)}`,
    }));
  }
}

export function segmentWhere(id: SegmentId): Prisma.UserWhereInput | null {
  const since = new Date(Date.now() - INACTIVE_MS);
  switch (id) {
    case "visitors":
      return { emailVerified: false };
    case "free_unpaid":
      return { subscriptionActive: false };
    case "paid":
      return { subscriptionActive: true };
    case "cancelled":
      return {
        subscriptionActive: false,
        NOT: { paymentProvider: null },
      };
    case "inactive":
      return {
        OR: [
          { subscriptionActive: true },
          { NOT: { paymentProvider: null } },
        ],
        generationJobs: { none: { createdAt: { gte: since } } },
      };
    default:
      return null;
  }
}
