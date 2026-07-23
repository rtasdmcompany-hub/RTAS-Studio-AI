import type { PaymentWebhookEvent, UserProfile } from "@rtas/shared";
import { processPaymentEvent } from "@rtas/utils/payments";
import {
  getServerProfile,
  getServerProfileByEmail,
  saveServerProfile,
} from "@/lib/server/profile-store";
import { applyLedgerActions, recordWebhookAudit } from "./billing/ledger";
import { AnalyticsEvents, trackServerEvent } from "@/lib/analytics";
import {
  sendBillingNotificationEmail,
  sendPaymentSuccessEmail,
} from "@/lib/marketing/send-hooks";

async function resolveProfile(
  userId: string,
  email?: string
): Promise<UserProfile> {
  let profile: UserProfile | null = null;
  if (email) {
    profile = await getServerProfileByEmail(email);
  }
  if (!profile) {
    profile = await getServerProfile(userId);
  }
  if (profile.id === "local-user" && userId !== "local-user") {
    profile = { ...profile, id: userId };
  }
  if (!profile.email && email) {
    profile = { ...profile, email };
  }
  return profile;
}

function extractUserId(event: PaymentWebhookEvent): string {
  if ("payload" in event && event.payload && "userId" in event.payload) {
    return String(event.payload.userId ?? "").trim();
  }
  return "";
}

function extractEmail(event: PaymentWebhookEvent): string | undefined {
  if (
    "payload" in event &&
    event.payload &&
    "email" in event.payload &&
    typeof event.payload.email === "string"
  ) {
    return event.payload.email;
  }
  return undefined;
}

export type ProcessVerifiedWebhookResult = {
  ok: boolean;
  duplicate?: boolean;
  ignored?: boolean;
  reason?: string;
  profile?: UserProfile;
  eventType: string;
  error?: string;
};

/**
 * Process a verified + idempotency-claimed webhook event.
 * Does not verify signatures — caller must verify first.
 */
export async function processVerifiedWebhookEvent(input: {
  provider: string;
  eventId: string;
  event: PaymentWebhookEvent;
}): Promise<ProcessVerifiedWebhookResult> {
  const { provider, eventId, event } = input;
  const userId = extractUserId(event);
  const email = extractEmail(event);

  try {
    if (
      (event.type === "subscription_activated" ||
        event.type === "subscription_renewed") &&
      !userId
    ) {
      await recordWebhookAudit({
        provider,
        eventId,
        eventType: event.type,
        signatureValid: true,
        processed: false,
        error: "missing_user_id",
        payload: event,
      });
      return {
        ok: false,
        eventType: event.type,
        error: "Missing user_id in webhook custom_data",
      };
    }

    if (event.type === "ignored") {
      await recordWebhookAudit({
        provider,
        eventId,
        eventType: event.type,
        userId: userId || undefined,
        signatureValid: true,
        processed: true,
        payload: event,
      });
      return { ok: true, ignored: true, reason: event.reason, eventType: event.type };
    }

    const profile = userId
      ? await resolveProfile(userId, email)
      : await getServerProfile("local-user");

    const result = processPaymentEvent(profile, event);
    const saved = result.applied
      ? await saveServerProfile(result.profile)
      : profile;

    if (result.actions.length > 0 && saved.id) {
      await applyLedgerActions({
        userId: saved.id,
        provider: event.provider,
        event,
        actions: result.actions,
      });
    }

    await recordWebhookAudit({
      provider,
      eventId,
      eventType: event.type,
      userId: saved.id,
      signatureValid: true,
      processed: true,
      payload: event,
    });

    if (result.applied) {
      if (event.type === "subscription_activated") {
        trackServerEvent(AnalyticsEvents.SUBSCRIPTION_STARTED, {
          provider,
          userId: saved.id,
          planKey:
            "payload" in event && event.payload && "planType" in event.payload
              ? String(event.payload.planType ?? "")
              : undefined,
        });
        if (saved.email) {
          const planLabel =
            "payload" in event && event.payload && "planType" in event.payload
              ? String(event.payload.planType ?? "plan")
              : saved.tier || "plan";
          void sendPaymentSuccessEmail({
            userId: saved.id,
            email: saved.email,
            name: saved.name,
            planLabel,
            credits: saved.credits,
          }).catch(() => undefined);
        }
      } else if (event.type === "subscription_renewed") {
        trackServerEvent(AnalyticsEvents.SUBSCRIPTION_RENEWED, {
          provider,
          userId: saved.id,
        });
        if (saved.email) {
          void sendPaymentSuccessEmail({
            userId: saved.id,
            email: saved.email,
            name: saved.name,
            planLabel: saved.tier || "subscription",
            credits: saved.credits,
          }).catch(() => undefined);
        }
      } else if (event.type === "subscription_cancelled") {
        trackServerEvent(AnalyticsEvents.SUBSCRIPTION_CANCELLED, {
          provider,
          userId: saved.id,
        });
        if (saved.email) {
          void sendBillingNotificationEmail({
            userId: saved.id,
            email: saved.email,
            name: saved.name,
            headline: "Subscription cancelled",
            detail:
              "Your subscription was cancelled. Remaining credits stay available until their expiry date. You can resubscribe anytime from Pricing.",
          }).catch(() => undefined);
        }
      }
    }

    return {
      ok: true,
      profile: saved,
      eventType: event.type,
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : "webhook_process_failed";
    console.error("[process-webhook]", message);
    await recordWebhookAudit({
      provider,
      eventId,
      eventType: event.type,
      userId: userId || undefined,
      signatureValid: true,
      processed: false,
      error: message,
      payload: event,
    });
    return { ok: false, eventType: event.type, error: message };
  }
}
