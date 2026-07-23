/**
 * Marketing campaign catalog — real DB rows + planned stubs.
 * Metrics are 0 / "Not connected" until ESP webhooks write them.
 */

import { isPrismaConfigured, prisma } from "@/lib/prisma";
import { EMAIL_TEMPLATE_REGISTRY } from "@/lib/marketing/email-templates";

export type CampaignStatus =
  | "draft"
  | "scheduled"
  | "queued"
  | "sending"
  | "sent"
  | "cancelled"
  | "planned";

export type CampaignMetrics = {
  subscribers: number;
  sent: number;
  opens: number | null;
  clicks: number | null;
  bounces: number | null;
  unsubscribes: number;
  metricsSource: "database" | "not_connected";
};

export type CampaignRow = {
  id: string;
  name: string;
  templateId: string;
  status: CampaignStatus;
  segmentId: string | null;
  scheduledAt: string | null;
  queuedCount: number;
  metrics: CampaignMetrics;
  note?: string;
};

/** Seed catalog for ops UI when DB has no campaigns yet. */
export const PLANNED_CAMPAIGNS: CampaignRow[] = [
  {
    id: "planned-weekly",
    name: "Weekly Studio Updates",
    templateId: "weekly_updates",
    status: "planned",
    segmentId: "newsletter_subscribers",
    scheduledAt: null,
    queuedCount: 0,
    metrics: {
      subscribers: 0,
      sent: 0,
      opens: null,
      clicks: null,
      bounces: null,
      unsubscribes: 0,
      metricsSource: "not_connected",
    },
    note: "Planned — not scheduled. Open/click require Resend webhook.",
  },
  {
    id: "planned-features",
    name: "Feature Announcements",
    templateId: "feature_announcements",
    status: "planned",
    segmentId: "paid",
    scheduledAt: null,
    queuedCount: 0,
    metrics: {
      subscribers: 0,
      sent: 0,
      opens: null,
      clicks: null,
      bounces: null,
      unsubscribes: 0,
      metricsSource: "not_connected",
    },
    note: "Planned — ops-triggered when shipping meaningful features.",
  },
  {
    id: "planned-release",
    name: "Release Notes Digest",
    templateId: "release_notes",
    status: "planned",
    segmentId: "newsletter_subscribers",
    scheduledAt: null,
    queuedCount: 0,
    metrics: {
      subscribers: 0,
      sent: 0,
      opens: null,
      clicks: null,
      bounces: null,
      unsubscribes: 0,
      metricsSource: "not_connected",
    },
    note: "Planned — align with /help/changelog publishes.",
  },
  {
    id: "planned-newsletter",
    name: "RTAS Newsletter",
    templateId: "newsletter",
    status: "planned",
    segmentId: "newsletter_subscribers",
    scheduledAt: null,
    queuedCount: 0,
    metrics: {
      subscribers: 0,
      sent: 0,
      opens: null,
      clicks: null,
      bounces: null,
      unsubscribes: 0,
      metricsSource: "not_connected",
    },
    note: "Planned — marketing calendar.",
  },
];

export async function listCampaigns(): Promise<CampaignRow[]> {
  if (!isPrismaConfigured()) {
    return PLANNED_CAMPAIGNS;
  }

  try {
    const rows = await prisma.marketingCampaign.findMany({
      orderBy: { updatedAt: "desc" },
      take: 50,
    });

    const mapped: CampaignRow[] = rows.map((r) => {
      const opensConnected = r.opensCount >= 0 && r.metricsConnected;
      return {
        id: r.id,
        name: r.name,
        templateId: r.templateId,
        status: r.status as CampaignStatus,
        segmentId: r.segmentId,
        scheduledAt: r.scheduledAt?.toISOString() ?? null,
        queuedCount: r.queuedCount,
        metrics: {
          subscribers: r.subscriberCount,
          sent: r.sentCount,
          opens: opensConnected ? r.opensCount : null,
          clicks: opensConnected ? r.clicksCount : null,
          bounces: opensConnected ? r.bouncesCount : null,
          unsubscribes: r.unsubCount,
          metricsSource: r.metricsConnected ? "database" : "not_connected",
        },
        note: r.notes || undefined,
      };
    });

    if (mapped.length === 0) return PLANNED_CAMPAIGNS;
    return mapped;
  } catch {
    return PLANNED_CAMPAIGNS;
  }
}

export async function getCampaignQueueSummary(): Promise<{
  queued: number;
  scheduled: number;
  sending: number;
}> {
  if (!isPrismaConfigured()) {
    return { queued: 0, scheduled: 0, sending: 0 };
  }
  try {
    const [queued, scheduled, sending] = await Promise.all([
      prisma.marketingCampaign.count({ where: { status: "queued" } }),
      prisma.marketingCampaign.count({ where: { status: "scheduled" } }),
      prisma.marketingCampaign.count({ where: { status: "sending" } }),
    ]);
    return { queued, scheduled, sending };
  } catch {
    return { queued: 0, scheduled: 0, sending: 0 };
  }
}

export function listTemplateCatalog() {
  return EMAIL_TEMPLATE_REGISTRY;
}
