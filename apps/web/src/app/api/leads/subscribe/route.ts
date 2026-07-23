import { createHash } from "crypto";
import { NextResponse } from "next/server";
import { PRODUCT_NAME } from "@rtas/shared";
import {
  checkRateLimitAsync,
  clientIpFromRequest,
  rateLimitResponse,
} from "@/lib/server/api-auth";
import { sendEmail } from "@/lib/server/mailer";
import { isEmailDeliveryConfigured } from "@/lib/env";
import { SITE_SUPPORT_EMAIL } from "@/lib/site-links";
import { logSystemEvent } from "@/lib/server/audit-log";
import { prisma, isPrismaConfigured } from "@/lib/prisma";
import { trackServerEvent } from "@/lib/analytics";
import { AnalyticsEvents } from "@/lib/analytics/events";

export const runtime = "nodejs";

const KINDS = [
  "newsletter",
  "early_access",
  "product_updates",
  "ai_tips",
] as const;
type SubscribeKind = (typeof KINDS)[number];

const KIND_LABEL: Record<SubscribeKind, string> = {
  newsletter: "Newsletter",
  early_access: "Early access",
  product_updates: "Product updates",
  ai_tips: "AI tips",
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function asTrimmedString(value: unknown, max = 200): string {
  if (typeof value !== "string") return "";
  return value.trim().slice(0, max);
}

function hashIp(ip: string): string {
  return createHash("sha256").update(ip).digest("hex").slice(0, 32);
}

export async function POST(request: Request) {
  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(`marketing-subscribe:${ip}`, 12, 60 * 60_000);
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  let body: Record<string, unknown> = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const kindRaw = asTrimmedString(body.kind, 40).toLowerCase();
  if (!KINDS.includes(kindRaw as SubscribeKind)) {
    return NextResponse.json(
      {
        error:
          "Invalid list. Use newsletter, early_access, product_updates, or ai_tips.",
      },
      { status: 400 }
    );
  }
  const kind = kindRaw as SubscribeKind;
  const email = asTrimmedString(body.email, 254).toLowerCase();
  const name = asTrimmedString(body.name, 120);
  const source = asTrimmedString(body.source, 80) || "web";
  const consentPrivacy = body.consentPrivacy === true;
  const ua = request.headers.get("user-agent")?.slice(0, 240) ?? undefined;

  if (!email || !EMAIL_RE.test(email)) {
    return NextResponse.json({ error: "A valid email is required." }, { status: 400 });
  }
  if (!consentPrivacy) {
    return NextResponse.json(
      {
        error:
          "Please confirm you agree to be contacted and accept the Privacy Policy.",
      },
      { status: 400 }
    );
  }

  let stored = false;
  if (isPrismaConfigured()) {
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const client = prisma as any;
      if (client.marketingLead?.upsert) {
        await client.marketingLead.upsert({
          where: { email_kind: { email, kind } },
          create: {
            email,
            name: name || null,
            kind,
            source,
            consentPrivacy: true,
            ipHash: hashIp(ip),
            userAgent: ua,
            metadataJson: { path: source },
          },
          update: {
            name: name || undefined,
            consentPrivacy: true,
            source,
            ipHash: hashIp(ip),
            userAgent: ua,
          },
        });
        stored = true;
      }
    } catch {
      /* fall through to email + system log */
    }
  }

  await logSystemEvent({
    level: "info",
    source: "marketing.lead",
    message: `${KIND_LABEL[kind]} subscribe: ${email}`,
    metadata: {
      kind,
      email,
      name: name || null,
      source,
      stored,
      consentPrivacy: true,
    },
  });

  void trackServerEvent(AnalyticsEvents.LEAD_CAPTURED, {
    kind,
    source,
    stored,
  });

  if (isEmailDeliveryConfigured()) {
    const subject = `[${PRODUCT_NAME}] ${KIND_LABEL[kind]} — ${email}`;
    const text = [
      `Kind: ${KIND_LABEL[kind]}`,
      `Email: ${email}`,
      name ? `Name: ${name}` : null,
      `Source: ${source}`,
      `Consent (privacy): yes`,
      `Stored in DB: ${stored ? "yes" : "no (email/log only)"}`,
      `Submitted: ${new Date().toISOString()}`,
      `IP hash: ${hashIp(ip)}`,
    ]
      .filter(Boolean)
      .join("\n");

    const result = await sendEmail({
      to: SITE_SUPPORT_EMAIL,
      subject,
      text,
      html: `<pre style="font-family:ui-monospace,monospace;white-space:pre-wrap;font-size:13px">${text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")}</pre>`,
    });

    if (!result.ok && !stored) {
      return NextResponse.json(
        {
          error:
            result.error ||
            `Could not save subscription. Email ${SITE_SUPPORT_EMAIL} directly.`,
          code: "EMAIL_SEND_FAILED",
        },
        { status: 502 }
      );
    }
  } else if (!stored) {
    return NextResponse.json(
      {
        error: `Subscription storage is not ready on this environment. Please email ${SITE_SUPPORT_EMAIL} or set DATABASE_URL / RESEND_API_KEY.`,
        code: "STORAGE_NOT_CONFIGURED",
      },
      { status: 503 }
    );
  }

  return NextResponse.json({
    ok: true,
    kind,
    stored,
  });
}
