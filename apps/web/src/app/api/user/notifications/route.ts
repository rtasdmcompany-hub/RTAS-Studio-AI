import { NextResponse } from "next/server";
import {
  checkRateLimitAsync,
  rateLimitResponse,
  requireApiSession,
} from "@/lib/server/api-auth";
import {
  getNotificationPrefs,
  listActiveAnnouncements,
  saveNotificationPrefs,
  type NotificationChannelPrefs,
} from "@/lib/marketing/notifications";

export const runtime = "nodejs";

export async function GET() {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;

  const [prefs, announcements] = await Promise.all([
    getNotificationPrefs(auth.userId),
    listActiveAnnouncements(),
  ]);

  return NextResponse.json({ ok: true, prefs, announcements });
}

export async function PATCH(request: Request) {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;

  const limited = await checkRateLimitAsync(
    `notif-prefs:${auth.userId}`,
    20,
    60_000
  );
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  let body: Partial<NotificationChannelPrefs> = {};
  try {
    body = (await request.json()) as Partial<NotificationChannelPrefs>;
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const prefs = await saveNotificationPrefs(auth.userId, body);
  return NextResponse.json({ ok: true, prefs });
}
