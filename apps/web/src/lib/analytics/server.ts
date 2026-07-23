import { logEvent } from "@/lib/observability";
import { isProductAnalyticsConfigured } from "./config";
import type { AnalyticsEventName, AnalyticsProps } from "./events";
import { sanitizeAnalyticsProps } from "./sanitize";

/**
 * Server-side analytics. Safe without consent cookies (server has no browser consent).
 * Does not invent vendor payloads — structured log sink until GA4/PostHog server SDK is wired.
 * Never include secrets, passwords, or payment credentials in properties.
 */
export function trackServerEvent(
  event: AnalyticsEventName | string,
  properties?: AnalyticsProps
): void {
  const safe = sanitizeAnalyticsProps(properties);
  const configured = isProductAnalyticsConfigured();

  if (!configured) {
    if (process.env.NODE_ENV !== "production") {
      logEvent("debug", `analytics.server:${event}`, safe);
    }
    return;
  }

  logEvent("info", `analytics.server:${event}`, {
    ...safe,
    analyticsConfigured: true,
    sink: "structured_log",
  });
}
