import { NextResponse } from "next/server";
import {
  applyPlanFromWebhook,
  cancelPremiumFromWebhook,
  parsePaddleWebhook,
  verifyPaddleSignature,
  type PaddleWebhookBody,
} from "@/lib/payments";
import { processFalFundingAfterPayment } from "@/lib/payments/fal-funding-service";
import { claimWebhookEventId } from "@/lib/server/webhook-idempotency";

export const runtime = "nodejs";

/**
 * Paddle Billing webhook (Merchant of Record).
 * Dashboard → Developer Tools → Notifications → endpoint URL:
 * https://your-domain.com/api/webhooks/paddle
 */
export async function POST(request: Request) {
  const deferPaddle =
    process.env.RTAS_DEFER_PADDLE === "1" ||
    process.env.RTAS_DEFER_PADDLE === "true";
  const hasSecret = Boolean(process.env.PADDLE_WEBHOOK_SECRET?.trim());

  // Keep Paddle routes mounted; defer verification until production keys exist.
  // Do not accept unsigned payloads as successful payments.
  if (deferPaddle && !hasSecret) {
    return NextResponse.json(
      {
        error:
          "Paddle webhook verification deferred until production keys are configured.",
        deferred: true,
        code: "PADDLE_DEFERRED",
      },
      { status: 503 }
    );
  }

  const rawBody = await request.text();
  const signature =
    request.headers.get("paddle-signature") ??
    request.headers.get("Paddle-Signature");

  if (!verifyPaddleSignature(rawBody, signature)) {
    return NextResponse.json({ error: "Invalid signature" }, { status: 401 });
  }

  let body: PaddleWebhookBody;
  try {
    body = JSON.parse(rawBody) as PaddleWebhookBody;
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const event = parsePaddleWebhook(body);
  const payload = "payload" in event ? event.payload : undefined;
  const paymentId =
    payload && "paymentId" in payload
      ? String(payload.paymentId ?? "")
      : "";
  const userId =
    payload && "userId" in payload ? String(payload.userId ?? "") : "";
  const eventKey =
    (typeof body.data?.id === "string" && body.data.id) ||
    `${event.type}:${paymentId}:${userId}`;

  const claimed = await claimWebhookEventId(`paddle:${eventKey}`, "paddle");
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
