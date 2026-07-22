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

export const runtime = "nodejs";

const KINDS = ["beta", "enterprise", "partners"] as const;
type LeadKind = (typeof KINDS)[number];

const KIND_LABEL: Record<LeadKind, string> = {
  beta: "Public Beta application",
  enterprise: "Enterprise sales inquiry",
  partners: "Partnership application",
};

const MAX_MESSAGE = 4000;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function asTrimmedString(value: unknown, max = 200): string {
  if (typeof value !== "string") return "";
  return value.trim().slice(0, max);
}

export async function POST(request: Request) {
  const ip = clientIpFromRequest(request) || "unknown";
  const limited = await checkRateLimitAsync(`commercial-lead:${ip}`, 8, 60 * 60_000);
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  let body: Record<string, unknown> = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const kindRaw = asTrimmedString(body.kind, 32).toLowerCase();
  if (!KINDS.includes(kindRaw as LeadKind)) {
    return NextResponse.json(
      { error: "Invalid lead kind. Use beta, enterprise, or partners." },
      { status: 400 }
    );
  }
  const kind = kindRaw as LeadKind;

  const name = asTrimmedString(body.name, 120);
  const email = asTrimmedString(body.email, 254).toLowerCase();
  const company = asTrimmedString(body.company, 160);
  const role = asTrimmedString(body.role, 120);
  const website = asTrimmedString(body.website, 240);
  const partnerType = asTrimmedString(body.partnerType, 80);
  const requestType = asTrimmedString(body.requestType, 80);
  const useCase = asTrimmedString(body.useCase, 500);
  const message = asTrimmedString(body.message, MAX_MESSAGE);
  const acceptTerms = body.acceptTerms === true;
  const acceptPrivacy = body.acceptPrivacy === true;

  if (!name || name.length < 2) {
    return NextResponse.json({ error: "Name is required (min 2 characters)." }, { status: 400 });
  }
  if (!email || !EMAIL_RE.test(email)) {
    return NextResponse.json({ error: "A valid email address is required." }, { status: 400 });
  }

  if (kind === "beta") {
    if (!useCase || useCase.length < 10) {
      return NextResponse.json(
        { error: "Please describe your use case (at least 10 characters)." },
        { status: 400 }
      );
    }
    if (!acceptTerms || !acceptPrivacy) {
      return NextResponse.json(
        { error: "You must accept the Terms of Service and Privacy Policy to apply." },
        { status: 400 }
      );
    }
  }

  if (kind === "enterprise") {
    if (!company) {
      return NextResponse.json({ error: "Company name is required." }, { status: 400 });
    }
    if (!["demo", "proposal", "meeting", "quote"].includes(requestType)) {
      return NextResponse.json(
        { error: "Request type must be demo, proposal, meeting, or quote." },
        { status: 400 }
      );
    }
  }

  if (kind === "partners") {
    if (!company) {
      return NextResponse.json({ error: "Organization name is required." }, { status: 400 });
    }
    const allowed = [
      "technology",
      "creative_agencies",
      "enterprise",
      "affiliate",
      "education",
    ];
    if (!allowed.includes(partnerType)) {
      return NextResponse.json({ error: "Select a valid partnership type." }, { status: 400 });
    }
    if (!message || message.length < 20) {
      return NextResponse.json(
        { error: "Please describe the partnership opportunity (at least 20 characters)." },
        { status: 400 }
      );
    }
  }

  if (!isEmailDeliveryConfigured()) {
    return NextResponse.json(
      {
        error:
          "Lead email delivery is not configured on this environment. Please email contact@rtasstudio.com directly, or set RESEND_API_KEY / SMTP_* and retry.",
        code: "EMAIL_NOT_CONFIGURED",
      },
      { status: 503 }
    );
  }

  const subject = `[${PRODUCT_NAME}] ${KIND_LABEL[kind]} — ${name}`;
  const lines = [
    `Kind: ${KIND_LABEL[kind]}`,
    `Name: ${name}`,
    `Email: ${email}`,
    company ? `Company / org: ${company}` : null,
    role ? `Role: ${role}` : null,
    website ? `Website: ${website}` : null,
    partnerType ? `Partner type: ${partnerType}` : null,
    requestType ? `Request type: ${requestType}` : null,
    useCase ? `Use case: ${useCase}` : null,
    kind === "beta"
      ? `Terms accepted: ${acceptTerms ? "yes" : "no"} · Privacy accepted: ${acceptPrivacy ? "yes" : "no"}`
      : null,
    message ? `Message:\n${message}` : null,
    "",
    `IP: ${ip}`,
    `Submitted: ${new Date().toISOString()}`,
    `Source: /api/commercial/lead`,
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

  if (!result.ok) {
    return NextResponse.json(
      {
        error:
          result.error ||
          "Failed to send notification email. Please email contact@rtasstudio.com directly.",
        code: "EMAIL_SEND_FAILED",
      },
      { status: 502 }
    );
  }

  return NextResponse.json({
    ok: true,
    kind,
    provider: result.provider,
  });
}
