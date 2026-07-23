/**
 * Analytics / third-party ID detection.
 * Scripts are NOT injected here — only detect whether ENV is present.
 */

function readPublic(key: string): string {
  const raw = process.env[key];
  return raw?.trim() ?? "";
}

export type AnalyticsVendorStatus = {
  ga4: boolean;
  gtm: boolean;
  posthog: boolean;
  genericAnalyticsId: boolean;
  metaPixel: boolean;
  linkedInInsight: boolean;
  clarity: boolean;
  sentry: boolean;
  /** True when any product-analytics sink ID is configured. */
  anyProductAnalytics: boolean;
};

export function getAnalyticsVendorStatus(): AnalyticsVendorStatus {
  const ga4 = Boolean(readPublic("NEXT_PUBLIC_GA_MEASUREMENT_ID"));
  const gtm = Boolean(readPublic("NEXT_PUBLIC_GTM_ID"));
  const posthog = Boolean(readPublic("NEXT_PUBLIC_POSTHOG_KEY"));
  const genericAnalyticsId = Boolean(readPublic("NEXT_PUBLIC_ANALYTICS_ID"));
  const metaPixel = Boolean(readPublic("NEXT_PUBLIC_META_PIXEL_ID"));
  const linkedInInsight = Boolean(readPublic("NEXT_PUBLIC_LINKEDIN_PARTNER_ID"));
  const clarity = Boolean(readPublic("NEXT_PUBLIC_CLARITY_ID"));
  const sentry = Boolean(
    readPublic("NEXT_PUBLIC_SENTRY_DSN") || readPublic("SENTRY_DSN")
  );

  return {
    ga4,
    gtm,
    posthog,
    genericAnalyticsId,
    metaPixel,
    linkedInInsight,
    clarity,
    sentry,
    anyProductAnalytics: ga4 || gtm || posthog || genericAnalyticsId,
  };
}

export function isProductAnalyticsConfigured(): boolean {
  return getAnalyticsVendorStatus().anyProductAnalytics;
}
