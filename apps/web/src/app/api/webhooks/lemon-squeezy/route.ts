import { NextResponse } from "next/server";
import {
  applyPlanFromWebhook,
  cancelPremiumFromWebhook,
  parseLemonSqueezyWebhook,
  verifyLemonSqueezySignature,
  type LemonSqueezyWebhookBody,
} from "@/lib/payments";
import { processFalFundingAfterPayment } from "@/lib/payments/fal-funding-service";

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

  switch (event.type) {
    case "subscription_activated":
    case "subscription_renewed": {
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
      return NextResponse.json({ ok: true, ignored: event.reason });
  }
}
