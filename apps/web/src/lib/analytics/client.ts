"use client";

import { logEvent } from "@/lib/observability";
import { hasAnalyticsConsent } from "./consent";
import { isProductAnalyticsConfigured } from "./config";
import type { AnalyticsEventName, AnalyticsProps } from "./events";
import { sanitizeAnalyticsProps } from "./sanitize";

/**
 * Client-side analytics.
 * - Respects cookie consent (Analytics category required for optional product analytics).
 * - No-ops (aside from dev debug logs) when vendor IDs are missing — does NOT inject pixels.
 */
export function trackClientEvent(
  event: AnalyticsEventName | string,
  properties?: AnalyticsProps
): void {
  if (typeof window === "undefined") return;

  const safe = sanitizeAnalyticsProps(properties);
  const consented = hasAnalyticsConsent();
  const configured = isProductAnalyticsConfigured();

  if (!consented) {
    if (process.env.NODE_ENV !== "production") {
      logEvent("debug", `analytics.client.blocked_consent:${event}`, safe);
    }
    return;
  }

  if (!configured) {
    if (process.env.NODE_ENV !== "production") {
      logEvent("debug", `analytics.client:${event}`, safe);
    }
    return;
  }

  // Structured log only — third-party scripts intentionally not auto-enabled.
  // When GA4/GTM/PostHog IDs exist, ops can add Script tags + forward here.
  logEvent("info", `analytics.client:${event}`, {
    ...safe,
    analyticsConfigured: true,
    sink: "structured_log",
  });

  // Optional dataLayer push if GTM was added manually elsewhere.
  try {
    const w = window as Window & { dataLayer?: unknown[] };
    if (Array.isArray(w.dataLayer)) {
      w.dataLayer.push({
        event: String(event).replace(/\s+/g, "_").toLowerCase(),
        ...safe,
      });
    }
  } catch {
    /* ignore */
  }
}
