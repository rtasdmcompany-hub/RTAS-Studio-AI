import { NextResponse } from "next/server";
import {
  applyPlanFromWebhook,
  parseLemonSqueezyWebhook,
  verifyLemonSqueezySignature,
  type LemonSqueezyWebhookBody,
} from "@/lib/payments";

export const runtime = "nodejs";

/** Omni Reach — $5 Tester publishing plan webhooks only */
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
      if (event.payload.planType !== "tester") {
        return NextResponse.json({
          ok: true,
          ignored: "Non-tester plans are handled by RTAS Studio AI",
        });
      }
      const profile = await applyPlanFromWebhook(event.payload);
      return NextResponse.json({
        ok: true,
        event: event.type,
        userId: profile.id,
        tier: profile.tier,
      });
    }
    case "ignored":
      return NextResponse.json({ ok: true, ignored: event.reason });
    case "subscription_cancelled":
      return NextResponse.json({ ok: true, ignored: "Subscription cancelled" });
    default:
      return NextResponse.json({ ok: true });
  }
}
