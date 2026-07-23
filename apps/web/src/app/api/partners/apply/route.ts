import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { PRODUCT_NAME } from "@rtas/shared";
import { authOptions } from "@/lib/auth/auth-options";
import {
  checkRateLimitAsync,
  clientIpFromRequest,
  rateLimitResponse,
} from "@/lib/server/api-auth";
import { sendEmail } from "@/lib/server/mailer";
import { isEmailDeliveryConfigured } from "@/lib/env";
import { SITE_SUPPORT_EMAIL } from "@/lib/site-links";
import { prisma, isPrismaConfigured } from "@/lib/prisma";
import { isPartnerTypeId } from "@/lib/affiliate/config";

export const runtime = "nodejs";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function asTrimmedString(value: unknown, max = 200): string {
  if (typeof value !== "string") return "";
  return value.trim().slice(0, max);
}

export async function POST(request: Request) {
  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(`partner-apply:${ip}`, 6, 60 * 60_000);
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  let body: Record<string, unknown> = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const name = asTrimmedString(body.name, 120);
  const email = asTrimmedString(body.email, 254).toLowerCase();
  const organization = asTrimmedString(body.organization, 160);
  const role = asTrimmedString(body.role, 120);
  const website = asTrimmedString(body.website, 240);
  const partnerType = asTrimmedString(body.partnerType, 80);
  const message = asTrimmedString(body.message, 4000);
  const acceptTerms = body.acceptTerms === true;

  if (!name || name.length < 2) {
    return NextResponse.json({ error: "Name is required (min 2 characters)." }, { status: 400 });
  }
  if (!email || !EMAIL_RE.test(email)) {
    return NextResponse.json({ error: "A valid email address is required." }, { status: 400 });
  }
  if (!organization || organization.length < 2) {
    return NextResponse.json({ error: "Organization name is required." }, { status: 400 });
  }
  if (!isPartnerTypeId(partnerType)) {
    return NextResponse.json({ error: "Select a valid partnership type." }, { status: 400 });
  }
  if (!message || message.length < 20) {
    return NextResponse.json(
      { error: "Please describe the partnership opportunity (at least 20 characters)." },
      { status: 400 }
    );
  }
  if (!acceptTerms) {
    return NextResponse.json(
      { error: "You must accept the Terms of Service and Privacy Policy." },
      { status: 400 }
    );
  }

  if (!isPrismaConfigured()) {
    return NextResponse.json(
      {
        error:
          "Application storage is not configured (DATABASE_URL). Please email contact@rtasstudio.com.",
        code: "DB_NOT_CONFIGURED",
      },
      { status: 503 }
    );
  }

  const session = await getServerSession(authOptions);
  const userId = session?.user?.id || null;

  const application = await prisma.partnerApplication.create({
    data: {
      userId: userId || undefined,
      name,
      email,
      organization,
      role,
      website,
      partnerType,
      message,
      acceptTerms,
      status: "pending",
      ip,
    },
  });

  if (userId) {
    const existing = await prisma.partnerAccount.findUnique({ where: { userId } });
    if (!existing) {
      await prisma.partnerAccount.create({
        data: {
          userId,
          organization,
          partnerType,
          status: "pending",
          applicationId: application.id,
        },
      });
    }
  }

  let emailSent = false;
  if (isEmailDeliveryConfigured()) {
    const subject = `[${PRODUCT_NAME}] Partnership application — ${organization}`;
    const lines = [
      "Kind: Partnership application",
      `Application ID: ${application.id}`,
      `Name: ${name}`,
      `Email: ${email}`,
      `Organization: ${organization}`,
      role ? `Role: ${role}` : null,
      website ? `Website: ${website}` : null,
      `Partner type: ${partnerType}`,
      `Message:\n${message}`,
      `Linked user: ${userId || "(anonymous / not signed in)"}`,
      "",
      `IP: ${ip}`,
      `Submitted: ${new Date().toISOString()}`,
      `Source: /api/partners/apply`,
    ].filter((line): line is string => line !== null);
    const text = lines.join("\n");
    const html = `<pre style="font-family:ui-monospace,monospace;white-space:pre-wrap;font-size:13px">${text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")}</pre>`;
    const result = await sendEmail({
      to: SITE_SUPPORT_EMAIL,
      subject,
      text,
      html,
    });
    emailSent = result.ok;
  }

  return NextResponse.json({
    ok: true,
    applicationId: application.id,
    emailSent,
    message: emailSent
      ? "Application stored and notification emailed to the RTAS team."
      : "Application stored. Notification email was skipped or not configured — the team can still review the database record.",
  });
}
