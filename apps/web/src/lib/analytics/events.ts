/**
 * Canonical product analytics events for RTAS Studio AI.
 * Names are stable for funnels / BI — do not invent success metrics.
 */

export const AnalyticsEvents = {
  HOMEPAGE_VIEWED: "Homepage Viewed",
  PRICING_VIEWED: "Pricing Viewed",
  SIGNUP_STARTED: "Signup Started",
  SIGNUP_COMPLETED: "Signup Completed",
  EMAIL_VERIFIED: "Email Verified",
  LOGIN_SUCCESS: "Login Success",
  LOGIN_FAILURE: "Login Failure",
  DASHBOARD_VIEWED: "Dashboard Viewed",
  PROJECT_CREATED: "Project Created",
  VIDEO_GENERATED: "Video Generated",
  VIDEO_FAILED: "Video Failed",
  CREDITS_PURCHASED: "Credits Purchased",
  SUBSCRIPTION_STARTED: "Subscription Started",
  SUBSCRIPTION_RENEWED: "Subscription Renewed",
  SUBSCRIPTION_CANCELLED: "Subscription Cancelled",
  INVOICE_CREATED: "Invoice Created",
  DOWNLOAD_STARTED: "Download Started",
  DOWNLOAD_COMPLETED: "Download Completed",
  SUPPORT_CONTACTED: "Support Contacted",
  /** Phase 13 Sprint 3 — funnel / RevOps */
  LEAD_CAPTURED: "Lead Captured",
  ENTERPRISE_LEAD_CAPTURED: "Enterprise Lead Captured",
  UPGRADE_PROMPT_SHOWN: "Upgrade Prompt Shown",
  UPGRADE_CTA_CLICKED: "Upgrade CTA Clicked",
  PLAN_COMPARE_VIEWED: "Plan Compare Viewed",
  RETENTION_CENTER_VIEWED: "Retention Center Viewed",
  LIFECYCLE_STAGE: "Lifecycle Stage",
  REFERRAL_INVITE_SHOWN: "Referral Invite Shown",
} as const;

export type AnalyticsEventName =
  (typeof AnalyticsEvents)[keyof typeof AnalyticsEvents];

/** Safe property bag — never put passwords, tokens, or full card data here. */
export type AnalyticsProps = Record<
  string,
  string | number | boolean | null | undefined
>;
