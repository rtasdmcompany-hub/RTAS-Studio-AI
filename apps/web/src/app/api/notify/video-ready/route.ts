import { NextResponse } from "next/server";
import { PRODUCT_NAME } from "@rtas/shared";
import { sendEmail } from "@/lib/server/mailer";
import {
  checkRateLimit,
  rateLimitResponse,
  requireApiSession,
} from "@/lib/server/api-auth";

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

  const limited = checkRateLimit(`notify:${auth.userId}`, 5, 60_000);
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

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
  // Only allow same-origin or relative video links to avoid open-redirect phishing.
  const safeVideoLink =
    videoLink &&
    (videoLink.startsWith("/") || videoLink.startsWith(`${appUrl}/`) || videoLink === appUrl)
      ? videoLink
      : undefined;

  const subject = `${PRODUCT_NAME} — your video is ready`;
  const text = [
    `Hi${auth.session.user?.name ? ` ${auth.session.user.name}` : ""},`,
    "",
    `Your video "${title}" (${durationLabel}) is ready in ${PRODUCT_NAME}.`,
    safeVideoLink ? `Watch: ${safeVideoLink}` : `Open Studio: ${studioUrl}`,
    "",
    "Thank you for creating with RTAS.",
  ].join("\n");

  const html = `
    <p>Hi${auth.session.user?.name ? ` ${auth.session.user.name}` : ""},</p>
    <p>Your video <strong>${title}</strong> (${durationLabel}) is ready.</p>
    ${
      safeVideoLink
        ? `<p><a href="${safeVideoLink}">Watch your video</a></p>`
        : `<p><a href="${studioUrl}">Open ${PRODUCT_NAME}</a></p>`
    }
    <p>Thank you for creating with RTAS.</p>
  `;

  const result = await sendEmail({ to: email, subject, html, text });

  return NextResponse.json({
    ok: result.ok,
    provider: result.provider,
    devPreviewPath: result.devPreviewPath,
    error: result.error,
  });
}
