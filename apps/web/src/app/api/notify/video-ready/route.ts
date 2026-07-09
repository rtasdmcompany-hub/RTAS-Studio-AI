import { NextResponse } from "next/server";
import { PRODUCT_NAME } from "@rtas/shared";
import { sendEmail } from "@/lib/server/mailer";
import {
  checkRateLimitAsync,
  rateLimitResponse,
  requireApiSession,
} from "@/lib/server/api-auth";
import { escapeHtml } from "@/lib/server/html-escape";

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
    (videoLink.startsWith("/") ||
      videoLink.startsWith(`${appUrl}/`) ||
      videoLink === appUrl)
      ? videoLink
      : undefined;

  const safeName = auth.session.user?.name
    ? escapeHtml(auth.session.user.name)
    : "";
  const safeTitle = escapeHtml(title);
  const safeDuration = escapeHtml(durationLabel);
  const safeHref = safeVideoLink ? escapeHtml(safeVideoLink) : "";
  const safeStudio = escapeHtml(studioUrl);
  const safeProduct = escapeHtml(PRODUCT_NAME);

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
    <p>Hi${safeName ? ` ${safeName}` : ""},</p>
    <p>Your video <strong>${safeTitle}</strong> (${safeDuration}) is ready.</p>
    ${
      safeHref
        ? `<p><a href="${safeHref}">Watch your video</a></p>`
        : `<p><a href="${safeStudio}">Open ${safeProduct}</a></p>`
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
