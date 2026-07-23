import { NextResponse } from "next/server";
import {
  checkRateLimitAsync,
  rateLimitResponse,
  requireApiSession,
} from "@/lib/server/api-auth";
import { createSupportTicket } from "@/lib/customer-success/tickets";
import { isPrismaConfigured } from "@/lib/prisma";
import { sendEmail } from "@/lib/server/mailer";
import { isEmailDeliveryConfigured } from "@/lib/env";
import { SITE_PRIVACY_EMAIL } from "@/lib/site-links";
import { logEvent } from "@/lib/observability";
import { PRODUCT_NAME } from "@rtas/shared";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * Request account deletion (DSAR). Creates a support ticket + notifies privacy@.
 * Does not immediately wipe data — ops verifies identity and statutory holds.
 * POST /api/user/privacy/deletion-request
 */
export async function POST(request: Request) {
  const auth = await requireApiSession();
  if (!auth.ok) return auth.response;

  const limited = await checkRateLimitAsync(
    `privacy-delete:${auth.userId}`,
    3,
    60 * 60_000
  );
  if (!limited.ok) return rateLimitResponse(limited.retryAfterSec);

  let confirm = false;
  let note = "";
  try {
    const body = (await request.json()) as { confirm?: unknown; note?: unknown };
    confirm = body.confirm === true;
    note = typeof body.note === "string" ? body.note.trim().slice(0, 2000) : "";
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  if (!confirm) {
    return NextResponse.json(
      {
        error:
          "Set confirm: true to submit an account deletion request. This queues a review — it does not delete instantly.",
      },
      { status: 400 }
    );
  }

  if (!isPrismaConfigured()) {
    return NextResponse.json(
      {
        error:
          "Deletion requests require the production database. Email privacy@rtasstudio.com instead.",
      },
      { status: 503 }
    );
  }

  const email = auth.session.user.email ?? "(no email on session)";
  const description = [
    "Account deletion / erasure request submitted from Privacy settings.",
    `User ID: ${auth.userId}`,
    `Email: ${email}`,
    note ? `User note: ${note}` : "User note: (none)",
    "Process: verify identity, check billing/statutory retention, then erase or anonymize eligible personal data. Do not claim instant deletion.",
  ].join("\n");

  try {
    const ticket = await createSupportTicket({
      userId: auth.userId,
      category: "account",
      priority: "high",
      subject: "Account deletion request (privacy)",
      description,
    });

    if (isEmailDeliveryConfigured()) {
      await sendEmail({
        to: SITE_PRIVACY_EMAIL,
        subject: `[${PRODUCT_NAME}] Deletion request ${ticket.ticketNumber}`,
        text: description,
        html: `<pre style="font-family:sans-serif;white-space:pre-wrap">${description
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")}</pre>`,
      });
    }

    logEvent("info", "privacy.deletion_request", {
      userId: auth.userId,
      ticketNumber: ticket.ticketNumber,
    });

    return NextResponse.json({
      ok: true,
      ticketNumber: ticket.ticketNumber,
      message:
        "Deletion request received. We will verify identity and complete erasure subject to billing and legal retention. Typical timeline: 30–45 days.",
    });
  } catch (err) {
    logEvent("error", "privacy.deletion_request.failed", {
      userId: auth.userId,
      message: err instanceof Error ? err.message : "unknown",
    });
    return NextResponse.json(
      {
        error:
          "Could not create deletion request. Email privacy@rtasstudio.com with your account email.",
      },
      { status: 500 }
    );
  }
}
