import { NextResponse } from "next/server";
import { PRODUCT_NAME } from "@rtas/shared";
import { sendEmail } from "@/lib/server/mailer";

type Body = {
  email?: string;
  name?: string;
  title?: string;
  videoUrl?: string;
  durationSeconds?: number;
};

export async function POST(request: Request) {
  let body: Body = {};
  try {
    body = (await request.json()) as Body;
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const email = body.email?.trim();
  if (!email) {
    return NextResponse.json({ error: "email required" }, { status: 400 });
  }

  const title = body.title?.trim() || "Your video";
  const durationLabel = body.durationSeconds
    ? `${body.durationSeconds} seconds`
    : "your requested length";
  const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";
  const studioUrl = `${appUrl}/studio`;
  const videoLink = body.videoUrl?.trim();

  const subject = `${PRODUCT_NAME} — your video is ready`;
  const text = [
    `Hi${body.name ? ` ${body.name}` : ""},`,
    "",
    `Your video "${title}" (${durationLabel}) is ready in ${PRODUCT_NAME}.`,
    videoLink ? `Watch: ${videoLink}` : `Open Studio: ${studioUrl}`,
    "",
    "Thank you for creating with RTAS.",
  ].join("\n");

  const html = `
    <p>Hi${body.name ? ` ${body.name}` : ""},</p>
    <p>Your video <strong>${title}</strong> (${durationLabel}) is ready.</p>
    ${
      videoLink
        ? `<p><a href="${videoLink}">Watch your video</a></p>`
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
