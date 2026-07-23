import { NextResponse } from "next/server";
import { sendEmail } from "@/lib/server/mailer";
import {
  checkRateLimitAsync,
  rateLimitResponse,
  requireApiSession,
} from "@/lib/server/api-auth";
import { renderVideoReadyEmail } from "@/lib/marketing/email-templates";
import { getNotificationPrefs } from "@/lib/marketing/notifications";

type Body = {
  title?: string;
  videoUrl?: string;
  durationSeconds?: number;
};

export async function POST(request: Request) {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;

  const email = auth.session.user?.email?.trim();
  if (!email) {
    return NextResponse.json(
      { error: "Signed-in account has no email address." },
      { status: 400 }
    );
  }

  const limited = await checkRateLimitAsync(`notify:${auth.userId}`, 5, 60_000);
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  const prefs = await getNotificationPrefs(auth.userId);
  if (!prefs.emailProduct) {
    return NextResponse.json({
      ok: true,
      skipped: true,
      reason: "product_email_disabled",
    });
  }

  let body: Body = {};
  try {
    body = (await request.json()) as Body;
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const title = body.title?.trim() || "Your video";
  const durationLabel = body.durationSeconds
    ? `${body.durationSeconds} seconds`
    : "your requested length";
  const appUrl = (process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000").replace(
    /\/$/,
    ""
  );
  const studioUrl = `${appUrl}/studio`;
  const videoLink = body.videoUrl?.trim();
  const safeVideoLink =
    videoLink &&
    (videoLink.startsWith("/") ||
      videoLink.startsWith(`${appUrl}/`) ||
      videoLink === appUrl)
      ? videoLink.startsWith("/")
        ? `${appUrl}${videoLink}`
        : videoLink
      : studioUrl;

  const rendered = renderVideoReadyEmail({
    name: auth.session.user?.name || undefined,
    title,
    durationLabel,
    watchUrl: safeVideoLink,
  });

  const result = await sendEmail({
    to: email,
    subject: rendered.subject,
    html: rendered.html,
    text: rendered.text,
  });

  return NextResponse.json({
    ok: result.ok,
    provider: result.provider,
    devPreviewPath: result.devPreviewPath,
    error: result.error,
    templateId: rendered.templateId,
  });
}
