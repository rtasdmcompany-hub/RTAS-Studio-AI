/**
 * Personal data export / deletion-request helpers for GDPR/CCPA readiness.
 * Never include password hashes, tokens, or full payment card data.
 */

import { isPrismaConfigured, prisma } from "@/lib/prisma";
import { getNotificationPrefs } from "@/lib/marketing/notifications";
import { getServerProfile } from "@/lib/server/profile-store";

export type PersonalDataExport = {
  exportedAt: string;
  formatVersion: "1.0";
  notice: string;
  account: Record<string, unknown>;
  notificationPreferences: Record<string, unknown>;
  projects: Array<Record<string, unknown>>;
  generationJobs: Array<Record<string, unknown>>;
  supportTickets: Array<Record<string, unknown>>;
};

export async function buildPersonalDataExport(
  userId: string
): Promise<PersonalDataExport> {
  const profile = await getServerProfile(userId);
  const prefs = await getNotificationPrefs(userId);

  const account: Record<string, unknown> = {
    id: profile.id,
    email: profile.email,
    name: profile.name,
    tier: profile.tier,
    credits: profile.credits,
    creditsExpireAt: profile.creditsExpireAt,
    subscriptionActive: profile.subscriptionActive,
    subscriptionRenewsAt: profile.subscriptionRenewsAt,
    paymentProvider: profile.paymentProvider ?? null,
    externalCustomerId: profile.externalCustomerId ?? null,
    externalSubscriptionId: profile.externalSubscriptionId ?? null,
    createdAt: profile.createdAt,
    updatedAt: profile.updatedAt,
  };

  let projects: Array<Record<string, unknown>> = [];
  let generationJobs: Array<Record<string, unknown>> = [];
  let supportTickets: Array<Record<string, unknown>> = [];

  if (isPrismaConfigured()) {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        emailVerified: true,
        provider: true,
        lastLoginAt: true,
        image: true,
      },
    });
    if (user) {
      account.emailVerified = user.emailVerified;
      account.authProvider = user.provider;
      account.lastLoginAt = user.lastLoginAt?.toISOString() ?? null;
      account.image = user.image;
    }

    const [projectRows, jobRows, ticketRows] = await Promise.all([
      prisma.project.findMany({
        where: { userId },
        orderBy: { createdAt: "desc" },
        take: 200,
        select: {
          id: true,
          title: true,
          prompt: true,
          status: true,
          durationSeconds: true,
          creditsUsed: true,
          provider: true,
          outputUrl: true,
          createdAt: true,
          updatedAt: true,
        },
      }),
      prisma.generationJob.findMany({
        where: { userId },
        orderBy: { createdAt: "desc" },
        take: 200,
        select: {
          id: true,
          status: true,
          prompt: true,
          durationSeconds: true,
          creditsCharged: true,
          provider: true,
          generatedVideoUrl: true,
          errorMessage: true,
          createdAt: true,
          updatedAt: true,
        },
      }),
      prisma.supportTicket.findMany({
        where: { userId },
        orderBy: { createdAt: "desc" },
        take: 50,
        select: {
          id: true,
          ticketNumber: true,
          category: true,
          priority: true,
          subject: true,
          description: true,
          status: true,
          createdAt: true,
          updatedAt: true,
        },
      }),
    ]);

    projects = projectRows.map((p) => ({
      ...p,
      createdAt: p.createdAt.toISOString(),
      updatedAt: p.updatedAt.toISOString(),
    }));
    generationJobs = jobRows.map((j) => ({
      ...j,
      status: String(j.status),
      createdAt: j.createdAt.toISOString(),
      updatedAt: j.updatedAt.toISOString(),
    }));
    supportTickets = ticketRows.map((t) => ({
      ...t,
      createdAt: t.createdAt.toISOString(),
      updatedAt: t.updatedAt.toISOString(),
    }));
  }

  return {
    exportedAt: new Date().toISOString(),
    formatVersion: "1.0",
    notice:
      "This export contains account and studio metadata held by RTAS Studio AI. Password hashes and payment card numbers are never included. Billing receipts may also exist with our Merchant of Record (Paddle).",
    account,
    notificationPreferences: prefs as unknown as Record<string, unknown>,
    projects,
    generationJobs,
    supportTickets,
  };
}
