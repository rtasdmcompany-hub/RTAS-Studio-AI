/**
 * Notification preferences + system announcements for in-app Notification Center.
 */

import { isPrismaConfigured, prisma } from "@/lib/prisma";

export type NotificationChannelPrefs = {
  emailTransactional: boolean;
  emailMarketing: boolean;
  emailBilling: boolean;
  emailProduct: boolean;
  inAppAnnouncements: boolean;
  inAppSecurity: boolean;
  inAppBilling: boolean;
  inAppMaintenance: boolean;
};

export const DEFAULT_NOTIFICATION_PREFS: NotificationChannelPrefs = {
  emailTransactional: true,
  emailMarketing: false,
  emailBilling: true,
  emailProduct: true,
  inAppAnnouncements: true,
  inAppSecurity: true,
  inAppBilling: true,
  inAppMaintenance: true,
};

export type InAppAnnouncement = {
  id: string;
  kind: "announcement" | "maintenance" | "security" | "billing" | "product";
  title: string;
  body: string;
  href: string | null;
  createdAt: string;
  active: boolean;
};

/** Static fallbacks when DB has no rows — not fabricated engagement metrics. */
export const STATIC_ANNOUNCEMENTS: InAppAnnouncement[] = [
  {
    id: "static-getting-started",
    kind: "product",
    title: "Getting started",
    body: "Open Studio, set duration, and generate — 1 credit = 1 second.",
    href: "/how-to-use",
    createdAt: new Date(0).toISOString(),
    active: true,
  },
  {
    id: "static-engage",
    kind: "announcement",
    title: "Engagement Center",
    body: "Tips, tutorials, KB, and community links in one place.",
    href: "/engage",
    createdAt: new Date(0).toISOString(),
    active: true,
  },
];

export async function getNotificationPrefs(
  userId: string
): Promise<NotificationChannelPrefs> {
  if (!isPrismaConfigured()) return { ...DEFAULT_NOTIFICATION_PREFS };
  try {
    const row = await prisma.marketingNotificationPreference.findUnique({
      where: { userId },
    });
    if (!row) return { ...DEFAULT_NOTIFICATION_PREFS };
    return {
      emailTransactional: row.emailTransactional,
      emailMarketing: row.emailMarketing,
      emailBilling: row.emailBilling,
      emailProduct: row.emailProduct,
      inAppAnnouncements: row.inAppAnnouncements,
      inAppSecurity: row.inAppSecurity,
      inAppBilling: row.inAppBilling,
      inAppMaintenance: row.inAppMaintenance,
    };
  } catch {
    return { ...DEFAULT_NOTIFICATION_PREFS };
  }
}

export async function saveNotificationPrefs(
  userId: string,
  prefs: Partial<NotificationChannelPrefs>
): Promise<NotificationChannelPrefs> {
  const current = await getNotificationPrefs(userId);
  const next = { ...current, ...prefs, emailTransactional: true };
  if (!isPrismaConfigured()) return next;
  try {
    await prisma.marketingNotificationPreference.upsert({
      where: { userId },
      create: { userId, ...next },
      update: next,
    });
  } catch {
    /* prefer in-memory defaults if migration not applied */
  }
  return next;
}

export async function listActiveAnnouncements(): Promise<InAppAnnouncement[]> {
  if (!isPrismaConfigured()) return STATIC_ANNOUNCEMENTS;
  try {
    const rows = await prisma.systemAnnouncement.findMany({
      where: {
        active: true,
        OR: [{ endsAt: null }, { endsAt: { gt: new Date() } }],
      },
      orderBy: { createdAt: "desc" },
      take: 20,
    });
    if (rows.length === 0) return STATIC_ANNOUNCEMENTS;
    return rows.map((r) => ({
      id: r.id,
      kind: r.kind as InAppAnnouncement["kind"],
      title: r.title,
      body: r.body,
      href: r.href || null,
      createdAt: r.createdAt.toISOString(),
      active: r.active,
    }));
  } catch {
    return STATIC_ANNOUNCEMENTS;
  }
}
