import { createHash } from "crypto";
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
import { isPrismaConfigured, prisma } from "@/lib/prisma";

export const runtime = "nodejs";

const KINDS = ["bug", "feature", "general", "suggestion", "feedback", "other"] as const;
type FeedbackKind = (typeof KINDS)[number];

const KIND_LABEL: Record<FeedbackKind, string> = {
  bug: "Bug report",
  feature: "Feature request",
  general: "General feedback",
  suggestion: "Suggestion",
  feedback: "General feedback",
  other: "Other",
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
  const limited = await checkRateLimitAsync(`product-feedback:${ip}`, 10, 60 * 60_000);
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  let body: Record<string, unknown> = {};
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const kindRaw = asTrimmedString(body.kind, 32).toLowerCase();
  const kindNormalized =
    kindRaw === "feedback" ? "general" : kindRaw === "suggestion" ? "suggestion" : kindRaw;
  if (!KINDS.includes(kindRaw as FeedbackKind) && !KINDS.includes(kindNormalized as FeedbackKind)) {
    return NextResponse.json(
      {
        error:
          "Invalid feedback type. Use bug, feature, general, suggestion, feedback, or other.",
      },
      { status: 400 }
    );
  }
  const kind = (KINDS.includes(kindRaw as FeedbackKind)
    ? kindRaw
    : kindNormalized) as FeedbackKind;
  const storeKind =
    kind === "feedback" ? "general" : kind === "feature" ? "feature" : kind;

  const email = asTrimmedString(body.email, 254).toLowerCase();
  const message = asTrimmedString(body.message, 4000);

  const csatRaw = body.csatScore ?? body.rating;
  const csatScore =
    typeof csatRaw === "number"
      ? csatRaw
      : typeof csatRaw === "string"
        ? Number.parseInt(csatRaw, 10)
        : NaN;

  const npsRaw = body.npsScore;
  const npsScore =
    typeof npsRaw === "number"
      ? npsRaw
      : typeof npsRaw === "string"
        ? Number.parseInt(npsRaw, 10)
        : NaN;

  if (!message || message.length < 10) {
    return NextResponse.json(
      { error: "Please include a message of at least 10 characters." },
      { status: 400 }
    );
  }
  if (email && !EMAIL_RE.test(email)) {
    return NextResponse.json({ error: "Reply email looks invalid." }, { status: 400 });
  }
  if (Number.isFinite(csatScore) && (csatScore < 1 || csatScore > 5)) {
    return NextResponse.json(
      { error: "CSAT rating must be from 1 to 5 when provided." },
      { status: 400 }
    );
  }
  if (Number.isFinite(npsScore) && (npsScore < 0 || npsScore > 10)) {
    return NextResponse.json(
      { error: "NPS score must be from 0 to 10 when provided." },
      { status: 400 }
    );
  }

  const session = await getServerSession(authOptions);
  const userId = session?.user?.id ?? null;
  const hasCsat = Number.isFinite(csatScore);
  const hasNps = Number.isFinite(npsScore);

  let storedFeedbackId: string | null = null;
  let storedSurveyIds: string[] = [];

  if (isPrismaConfigured()) {
    try {
      const feedback = await prisma.customerFeedback.create({
        data: {
          userId,
          email: email || session?.user?.email || null,
          kind: storeKind,
          message,
          csatScore: hasCsat ? csatScore : null,
          ipHash: hashIp(ip),
          source: asTrimmedString(body.source, 80) || "/feedback",
        },
      });
      storedFeedbackId = feedback.id;

      if (hasCsat) {
        const csat = await prisma.customerSurveyResponse.create({
          data: {
            userId,
            email: email || session?.user?.email || null,
            surveyType: "csat",
            score: csatScore,
            comment: message.slice(0, 1000),
            source: "/feedback",
          },
        });
        storedSurveyIds.push(csat.id);
      }
      if (hasNps) {
        const nps = await prisma.customerSurveyResponse.create({
          data: {
            userId,
            email: email || session?.user?.email || null,
            surveyType: "nps",
            score: npsScore,
            comment: asTrimmedString(body.npsComment, 1000) || null,
            source: "/feedback",
          },
        });
        storedSurveyIds.push(nps.id);
      }
    } catch {
      /* fall through to email — storage failure should not block mailto path entirely */
    }
  }

  const emailConfigured = isEmailDeliveryConfigured();
  let emailSent = false;
  let emailError: string | null = null;

  if (emailConfigured) {
    const subject = `[${PRODUCT_NAME}] ${KIND_LABEL[kind]}${
      hasCsat ? ` (CSAT ${csatScore}/5)` : ""
    }${hasNps ? ` (NPS ${npsScore}/10)` : ""}`;
    const lines = [
      `Type: ${KIND_LABEL[kind]}`,
      hasCsat ? `CSAT: ${csatScore}/5` : "CSAT: (not provided)",
      hasNps ? `NPS: ${npsScore}/10` : "NPS: (not provided)",
      email ? `Reply-to: ${email}` : "Reply-to: (not provided)",
      userId ? `User ID: ${userId}` : "User ID: (anonymous)",
      storedFeedbackId ? `Feedback ID: ${storedFeedbackId}` : null,
      "",
      message,
      "",
      `IP hash: ${hashIp(ip)}`,
      `Submitted: ${new Date().toISOString()}`,
      `Source: /api/feedback`,
    ].filter(Boolean) as string[];
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
    if (!result.ok) emailError = result.error || "EMAIL_SEND_FAILED";
  }

  if (storedFeedbackId) {
    return NextResponse.json({
      ok: true,
      stored: true,
      feedbackId: storedFeedbackId,
      surveyIds: storedSurveyIds,
      emailSent,
      ...(emailError ? { emailWarning: emailError } : {}),
    });
  }

  if (emailSent) {
    return NextResponse.json({ ok: true, stored: false, emailSent: true });
  }

  return NextResponse.json(
    {
      error: emailConfigured
        ? emailError ||
          `Failed to store or send feedback. Please email ${SITE_SUPPORT_EMAIL} directly.`
        : `Feedback could not be stored (database unavailable) and email delivery is not configured. Please email ${SITE_SUPPORT_EMAIL} directly.`,
      code: emailConfigured ? "FEEDBACK_FAILED" : "EMAIL_NOT_CONFIGURED",
    },
    { status: 503 }
  );
}
