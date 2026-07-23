/**
 * Customer lifecycle stages for RTAS Studio AI RevOps.
 * Stages are derived from real account + usage signals — never invented %.
 */

export const LIFECYCLE_STAGES = [
  "visitor",
  "signup",
  "verified",
  "activated",
  "first_video",
  "paid",
  "retained",
  "expanded",
  "churn_risk",
  "churned",
  "customer_success",
] as const;

export type LifecycleStage = (typeof LIFECYCLE_STAGES)[number];

export const LIFECYCLE_STAGE_LABEL: Record<LifecycleStage, string> = {
  visitor: "Visitor",
  signup: "Signup",
  verified: "Verified",
  activated: "Activated (first project)",
  first_video: "First video",
  paid: "Paid customer",
  retained: "Retained",
  expanded: "Expanded (upgrade)",
  churn_risk: "Churn risk",
  churned: "Churned",
  customer_success: "Customer success",
};

export type LifecycleSignals = {
  hasAccount: boolean;
  emailVerified: boolean;
  hasProjectOrJob: boolean;
  hasCompletedVideo: boolean;
  hasPaidPlan: boolean;
  subscriptionActive: boolean;
  credits: number;
  /** True when previously paid but subscription inactive and credits depleted. */
  looksChurned?: boolean;
  /** True when paid with low credits and no recent activity signal. */
  churnRisk?: boolean;
  /** Premium or upgraded from tester/standard. */
  expanded?: boolean;
};

/**
 * Derive the furthest applicable lifecycle stage from real signals.
 * Prefer concrete facts over speculation.
 */
export function deriveLifecycleStage(signals: LifecycleSignals): LifecycleStage {
  if (!signals.hasAccount) return "visitor";

  if (signals.looksChurned) return "churned";
  if (signals.churnRisk && signals.hasPaidPlan) return "churn_risk";

  if (signals.expanded && signals.subscriptionActive) return "expanded";
  if (signals.subscriptionActive && signals.hasCompletedVideo) return "retained";
  if (signals.hasPaidPlan || signals.subscriptionActive) return "paid";
  if (signals.hasCompletedVideo) return "first_video";
  if (signals.hasProjectOrJob) return "activated";
  if (signals.emailVerified) return "verified";
  return "signup";
}

/** Human-readable next action for retention / CS surfaces. */
export function lifecycleNextAction(stage: LifecycleStage): {
  label: string;
  href: string;
} {
  switch (stage) {
    case "visitor":
      return { label: "Start creating", href: "/studio" };
    case "signup":
      return { label: "Verify email", href: "/auth/check-email" };
    case "verified":
      return { label: "Open Studio", href: "/studio" };
    case "activated":
      return { label: "Generate first video", href: "/studio" };
    case "first_video":
      return { label: "Get Tester or subscribe", href: "/pricing#plans" };
    case "paid":
      return { label: "Keep creating", href: "/studio" };
    case "retained":
      return { label: "Explore Premium 4K", href: "/pricing#plans" };
    case "expanded":
      return { label: "Customer Success", href: "/help" };
    case "churn_risk":
      return { label: "Recharge credits", href: "/pricing#plans" };
    case "churned":
      return { label: "Reactivate plan", href: "/pricing#plans" };
    case "customer_success":
      return { label: "Help Center", href: "/help" };
    default:
      return { label: "Open Studio", href: "/studio" };
  }
}
