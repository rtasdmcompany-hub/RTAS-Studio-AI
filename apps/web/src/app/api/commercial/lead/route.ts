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
import { sendEnterpriseFollowupEmail } from "@/lib/marketing/send-hooks";
import { isPrismaConfigured, prisma } from "@/lib/prisma";
import { randomUUID } from "crypto";
import {
  createEnterpriseLead,
  isValidDemoType,
  isValidPlanInterest,
  isValidRequestType,
} from "@/lib/enterprise/crm";
import { ENTERPRISE_DEMO_TYPE_LABELS } from "@/lib/enterprise/pipeline";

export const runtime = "nodejs";

const KINDS = ["beta", "enterprise", "partners", "demo"] as const;
type LeadKind = (typeof KINDS)[number];

const KIND_LABEL: Record<LeadKind, string> = {
  beta: "Public Beta application",
  enterprise: "Enterprise sales inquiry",
  partners: "Partnership application",
  demo: "Demo / consultation booking",
};

const MAX_MESSAGE = 4000;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function asTrimmedString(value: unknown, max = 200): string {
  if (typeof value !== "string") return "";
  return value.trim().slice(0, max);
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
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
      { error: "Invalid lead kind. Use beta, enterprise, partners, or demo." },
      { status: 400 }
    );
  }
  const kind = kindRaw as LeadKind;

  const name = asTrimmedString(body.name, 120);
  const email = asTrimmedString(body.email, 254).toLowerCase();
  const company = asTrimmedString(body.company, 160);
  const role = asTrimmedString(body.role, 120);
  const website = asTrimmedString(body.website, 240);
  const phone = asTrimmedString(body.phone, 40);
  const teamSize = asTrimmedString(body.teamSize, 40);
  const industry = asTrimmedString(body.industry, 80);
  const partnerType = asTrimmedString(body.partnerType, 80);
  let requestType = asTrimmedString(body.requestType, 80);
  const demoType = asTrimmedString(body.demoType, 80);
  const planInterest = asTrimmedString(body.planInterest, 40);
  const timeline = asTrimmedString(body.timeline, 200);
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

  if (kind === "enterprise" || kind === "demo") {
    if (!company) {
      return NextResponse.json({ error: "Company name is required." }, { status: 400 });
    }
    if (!role) {
      return NextResponse.json({ error: "Role / title is required." }, { status: 400 });
    }
    if (!message || message.length < 20) {
      return NextResponse.json(
        { error: "Please include project context (at least 20 characters)." },
        { status: 400 }
      );
    }
    if (planInterest && !isValidPlanInterest(planInterest)) {
      return NextResponse.json(
        { error: "Plan interest must be tester, creator, business, or enterprise." },
        { status: 400 }
      );
    }
    if (demoType && !isValidDemoType(demoType)) {
      return NextResponse.json(
        {
          error:
            "Demo type must be book_demo, technical_consultation, or discovery_call.",
        },
        { status: 400 }
      );
    }

    if (!requestType && demoType) {
      requestType =
        demoType === "book_demo"
          ? "demo"
          : demoType === "technical_consultation"
            ? "technical_consultation"
            : "discovery_call";
    }
    if (!requestType) requestType = kind === "demo" ? "demo" : "inquiry";

    if (!isValidRequestType(requestType)) {
      return NextResponse.json(
        {
          error:
            "Request type must be demo, technical_consultation, discovery_call, proposal, meeting, quote, or inquiry.",
        },
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
      "software",
      "education",
      "enterprise",
      "affiliate", // legacy lead form value — prefer /affiliate apply
      "marketing_agencies", // alias accepted → stored as creative_agencies historically
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

  const userAgent = request.headers.get("user-agent") || undefined;
  const persist =
    kind === "enterprise" || kind === "demo" || kind === "partners" || kind === "beta"
      ? await createEnterpriseLead({
          kind,
          name,
          email,
          company: company || undefined,
          role: role || undefined,
          website: website || undefined,
          phone: phone || undefined,
          teamSize: teamSize || undefined,
          industry: industry || undefined,
          requestType: requestType || (kind === "partners" ? partnerType : undefined),
          demoType: demoType || undefined,
          message: message || useCase || undefined,
          planInterest: planInterest || undefined,
          timeline: timeline || undefined,
          requirements: message || useCase || undefined,
          source:
            kind === "demo"
              ? "demo_form"
              : kind === "enterprise"
                ? "enterprise_form"
                : kind === "partners"
                  ? "partners_form"
                  : "beta_form",
          ip,
          userAgent,
        })
      : { ok: false, skipped: true as const };

  const emailConfigured = isEmailDeliveryConfigured();
  if (!persist.ok && persist.skipped && !emailConfigured) {
    return NextResponse.json(
      {
        error:
          "Lead storage and email delivery are not configured. Please email contact@rtasstudio.com directly.",
        code: "LEAD_CHANNEL_UNAVAILABLE",
      },
      { status: 503 }
    );
  }

  const subject = `[${PRODUCT_NAME}] ${KIND_LABEL[kind]} — ${name}`;
  const demoLabel =
    demoType && isValidDemoType(demoType)
      ? ENTERPRISE_DEMO_TYPE_LABELS[demoType]
      : null;
  const lines = [
    `Kind: ${KIND_LABEL[kind]}`,
    persist.ok && persist.id ? `CRM lead id: ${persist.id}` : null,
    `Name: ${name}`,
    `Email: ${email}`,
    company ? `Company / org: ${company}` : null,
    role ? `Role: ${role}` : null,
    website ? `Website: ${website}` : null,
    phone ? `Phone: ${phone}` : null,
    teamSize ? `Team size: ${teamSize}` : null,
    industry ? `Industry: ${industry}` : null,
    partnerType ? `Partner type: ${partnerType}` : null,
    requestType ? `Request type: ${requestType}` : null,
    demoLabel ? `Demo type: ${demoLabel}` : null,
    planInterest ? `Plan interest: ${planInterest}` : null,
    timeline ? `Timeline: ${timeline}` : null,
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
  const html = `<pre style="font-family:ui-monospace,monospace;white-space:pre-wrap;font-size:13px">${escapeHtml(text)}</pre>`;

  let adminEmailOk = false;
  let confirmEmailOk = false;
  let emailProvider: string | undefined;
  let emailError: string | undefined;

  if (emailConfigured) {
    const adminResult = await sendEmail({
      to: SITE_SUPPORT_EMAIL,
      subject,
      text,
      html,
    });
    adminEmailOk = adminResult.ok;
    emailProvider = adminResult.provider;
    if (!adminResult.ok) emailError = adminResult.error;

    const followup = await sendEnterpriseFollowupEmail({
      email,
      name,
      kindLabel: KIND_LABEL[kind],
    });
    confirmEmailOk = followup.ok;
  }

  if (isPrismaConfigured()) {
    try {
      await prisma.commercialLead.create({
        data: {
          id: randomUUID(),
          kind,
          name,
          email,
          company: company || "",
          role: role || "",
          website: website || "",
          partnerType: partnerType || "",
          requestType: requestType || "",
          useCase: useCase || "",
          message: message || "",
          status: "new",
          ip,
        },
      });
    } catch {
      /* CommercialLeads table may not be migrated yet — CRM path still primary */
    }
  }

  if (!persist.ok && !adminEmailOk) {
    return NextResponse.json(
      {
        error:
          emailError ||
          "Failed to store or notify. Please email contact@rtasstudio.com directly.",
        code: persist.skipped ? "EMAIL_SEND_FAILED" : "LEAD_PERSIST_FAILED",
      },
      { status: persist.skipped ? 502 : 500 }
    );
  }

  const { logSystemEvent } = await import("@/lib/server/audit-log");
  await logSystemEvent({
    level: "info",
    source: "commercial.lead",
    message: `${KIND_LABEL[kind]} — ${name}`,
    metadata: {
      kind,
      email,
      company: company || null,
      requestType: requestType || null,
      partnerType: partnerType || null,
      leadId: persist.ok ? persist.id : null,
    },
  });

  return NextResponse.json({
    ok: true,
    kind,
    leadId: persist.ok ? persist.id : undefined,
    persisted: Boolean(persist.ok),
    adminNotified: adminEmailOk,
    confirmationSent: confirmEmailOk,
    provider: emailProvider,
    warning:
      !emailConfigured && persist.ok
        ? "Lead saved to CRM; email delivery is not configured on this environment."
        : undefined,
  });
}
