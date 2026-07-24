import { NextResponse } from "next/server";
import {
  applyPlanFromWebhook,
  cancelPremiumFromWebhook,
  parseLemonSqueezyWebhook,
  verifyLemonSqueezySignature,
  type LemonSqueezyWebhookBody,
} from "@/lib/payments";
import { processFalFundingAfterPayment } from "@/lib/payments/fal-funding-service";
import { claimWebhookEventId } from "@/lib/server/webhook-idempotency";

export const runtime = "nodejs";

/**
 * Lemon Squeezy webhook (Merchant of Record).
 * Store → Settings → Webhooks → URL:
 * https://your-domain.com/api/webhooks/lemon-squeezy
 */
export async function POST(request: Request) {
  const rawBody = await request.text();
  const signature = request.headers.get("x-signature");

  if (!verifyLemonSqueezySignature(rawBody, signature)) {
    return NextResponse.json({ error: "Invalid signature" }, { status: 401 });
  }

  let body: LemonSqueezyWebhookBody;
  try {
    body = JSON.parse(rawBody) as LemonSqueezyWebhookBody;
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const event = parseLemonSqueezyWebhook(body);
  const payload = "payload" in event ? event.payload : undefined;
  const paymentId =
    payload && "paymentId" in payload
      ? String(payload.paymentId ?? "")
      : "";
  const eventKey =
    (typeof body.data?.id === "string" && body.data.id) ||
    `${event.type}:${paymentId}`;

  const claimed = await claimWebhookEventId(
    `lemon:${eventKey}`,
    "lemon-squeezy"
  );
  if (!claimed) {
    return NextResponse.json({
      ok: true,
      duplicate: true,
      event: event.type,
    });
  }

  switch (event.type) {
    case "subscription_activated":
    case "subscription_renewed": {
      if (!event.payload.userId?.trim()) {
        return NextResponse.json(
          { error: "Missing user_id in webhook custom_data" },
          { status: 400 }
        );
      }
      const profile = await applyPlanFromWebhook(event.payload);
      const fal = await processFalFundingAfterPayment(event.payload);
      return NextResponse.json({
        ok: true,
        event: event.type,
        userId: profile.id,
        tier: profile.tier,
        credits: profile.credits,
        falFunding: {
          ledgerRecorded: fal.ledgerRecorded,
          shortfallUsd: fal.snapshot.shortfallUsd,
          alert: fal.snapshot.alertMessage ?? null,
        },
      });
    }
    case "subscription_cancelled": {
      const profile = await cancelPremiumFromWebhook(event.payload);
      return NextResponse.json({
        ok: true,
        event: event.type,
        userId: profile.id,
        tier: profile.tier,
      });
    }
    default:
      return NextResponse.json({
        ok: true,
        ignored: event.type === "ignored" ? event.reason : event.type,
      });
  }
}
