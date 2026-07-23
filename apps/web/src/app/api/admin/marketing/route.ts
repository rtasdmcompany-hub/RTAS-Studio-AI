import { NextResponse } from "next/server";
import {
  isAdminAuthorized,
  adminUnauthorizedResponse,
} from "@/lib/server/api-auth";
import { countSegments, SEGMENT_DEFINITIONS } from "@/lib/marketing/segmentation";
import {
  getCampaignQueueSummary,
  listCampaigns,
  listTemplateCatalog,
} from "@/lib/marketing/campaigns";
import { isPrismaConfigured, prisma } from "@/lib/prisma";
import { isEmailDeliveryConfigured, getEmailDeliveryMode } from "@/lib/env";

export const runtime = "nodejs";

export async function GET(request: Request) {
  if (!isAdminAuthorized(request)) return adminUnauthorizedResponse();

  const [segments, campaigns, queue, recentSends, newsletterCount] =
    await Promise.all([
      countSegments(),
      listCampaigns(),
      getCampaignQueueSummary(),
      (async () => {
        if (!isPrismaConfigured()) return [];
        try {
          return await prisma.emailSendLog.findMany({
            orderBy: { createdAt: "desc" },
            take: 25,
            select: {
              id: true,
              templateId: true,
              toEmail: true,
              subject: true,
              status: true,
              provider: true,
              createdAt: true,
            },
          });
        } catch {
          return [];
        }
      })(),
      (async () => {
        if (!isPrismaConfigured()) return 0;
        try {
          return await prisma.newsletterSubscriber.count({
            where: { status: "subscribed" },
          });
        } catch {
          return 0;
        }
      })(),
    ]);

  return NextResponse.json({
    ok: true,
    integrity: {
      note: "Open/click/bounce rates are Not connected until Resend webhooks write metricsConnected=true. Zeroes are real, not estimates.",
      espMetrics: "not_connected",
      emailDeliveryConfigured: isEmailDeliveryConfigured(),
      emailDeliveryMode: getEmailDeliveryMode(),
    },
    templates: listTemplateCatalog(),
    segmentDefinitions: SEGMENT_DEFINITIONS,
    segments,
    campaigns,
    queue,
    newsletterSubscribers: newsletterCount,
    recentSends: recentSends.map((s) => ({
      ...s,
      createdAt: s.createdAt.toISOString(),
      toEmail: s.toEmail.replace(/^(.{2}).*(@.*)$/, "$1***$2"),
    })),
  });
}
