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
import {
  AFFILIATE_PAYOUTS_LIVE,
  generateReferralCode,
} from "@/lib/affiliate/config";

export const runtime = "nodejs";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const AUDIENCE_SIZES = ["under_1k", "1k_10k", "10k_50k", "50k_250k", "250k_plus"] as const;
const PAYOUT_PREFS = ["paypal", "wise", "bank", "undecided"] as const;

function asTrimmedString(value: unknown, max = 200): string {
  if (typeof value !== "string") return "";
  return value.trim().slice(0, max);
}

export async function POST(request: Request) {
  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(`affiliate-apply:${ip}`, 6, 60 * 60_000);
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  let body: Record<string, unknown> = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const name = asTrimmedString(body.name, 120);
  const email = asTrimmedString(body.email, 254).toLowerCase();
  const company = asTrimmedString(body.company, 160);
  const website = asTrimmedString(body.website, 240);
  const audienceSize = asTrimmedString(body.audienceSize, 40);
  const channels = asTrimmedString(body.channels, 240);
  const audienceDescription = asTrimmedString(body.audienceDescription, 1000);
  const promotionPlan = asTrimmedString(body.promotionPlan, 4000);
  const payoutPreference = asTrimmedString(body.payoutPreference, 40);
  const taxCountry = asTrimmedString(body.taxCountry, 80);
  const acceptTerms = body.acceptTerms === true;
  const acceptProgramRules = body.acceptProgramRules === true;

  if (!name || name.length < 2) {
    return NextResponse.json({ error: "Name is required (min 2 characters)." }, { status: 400 });
  }
  if (!email || !EMAIL_RE.test(email)) {
    return NextResponse.json({ error: "A valid email address is required." }, { status: 400 });
  }
  if (!(AUDIENCE_SIZES as readonly string[]).includes(audienceSize)) {
    return NextResponse.json({ error: "Select a valid audience size band." }, { status: 400 });
  }
  if (!channels || channels.length < 3) {
    return NextResponse.json(
      { error: "List the channels you use (YouTube, newsletter, etc.)." },
      { status: 400 }
    );
  }
  if (!promotionPlan || promotionPlan.length < 40) {
    return NextResponse.json(
      { error: "Describe your promotion plan (at least 40 characters)." },
      { status: 400 }
    );
  }
  if (!(PAYOUT_PREFS as readonly string[]).includes(payoutPreference)) {
    return NextResponse.json({ error: "Select a payout preference." }, { status: 400 });
  }
  if (!taxCountry || taxCountry.length < 2) {
    return NextResponse.json({ error: "Tax / residence country is required." }, { status: 400 });
  }
  if (!acceptTerms || !acceptProgramRules) {
    return NextResponse.json(
      {
        error:
          "You must accept the Terms of Service, Privacy Policy, and affiliate program rules.",
      },
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

  const application = await prisma.affiliateApplication.create({
    data: {
      userId: userId || undefined,
      name,
      email,
      company,
      website,
      audienceSize,
      channels,
      audienceDescription,
      promotionPlan,
      payoutPreference,
      taxCountry,
      acceptTerms,
      acceptProgramRules,
      status: "pending",
      ip,
    },
  });

  if (userId) {
    const existing = await prisma.affiliateAccount.findUnique({ where: { userId } });
    if (!existing) {
      let code = generateReferralCode(userId);
      const clash = await prisma.affiliateAccount.findUnique({
        where: { referralCode: code },
      });
      if (clash) code = generateReferralCode(`${userId}-${Date.now()}`);
      await prisma.affiliateAccount.create({
        data: {
          userId,
          referralCode: code,
          status: "pending",
          applicationId: application.id,
          paymentStatus: "not_connected",
        },
      });
    }
  }

  let emailSent = false;
  if (isEmailDeliveryConfigured()) {
    const subject = `[${PRODUCT_NAME}] Affiliate application — ${name}`;
    const lines = [
      "Kind: Affiliate program application",
      `Application ID: ${application.id}`,
      `Name: ${name}`,
      `Email: ${email}`,
      company ? `Company: ${company}` : null,
      website ? `Website: ${website}` : null,
      `Audience size: ${audienceSize}`,
      `Channels: ${channels}`,
      audienceDescription ? `Audience: ${audienceDescription}` : null,
      `Promotion plan:\n${promotionPlan}`,
      `Payout preference: ${payoutPreference}`,
      `Tax country: ${taxCountry}`,
      `Payouts live (system flag): ${AFFILIATE_PAYOUTS_LIVE ? "yes" : "NO — applications only"}`,
      `Linked user: ${userId || "(anonymous / not signed in)"}`,
      "",
      `IP: ${ip}`,
      `Submitted: ${new Date().toISOString()}`,
      `Source: /api/affiliate/apply`,
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
    payoutsLive: AFFILIATE_PAYOUTS_LIVE,
    message: emailSent
      ? "Application stored and notification emailed to the RTAS team."
      : "Application stored. Notification email was skipped or not configured — the team can still review the database record.",
  });
}
