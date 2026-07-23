/**
 * Rule-based churn prevention — no fake AI predictions.
 * Signals are derived from observable account facts only.
 */

export type RiskLevel = "healthy" | "watch" | "at_risk" | "critical";

export type ChurnSignal = {
  id: string;
  severity: "info" | "warn" | "critical";
  label: string;
  detail: string;
};

export type ChurnInput = {
  now: Date;
  createdAt: Date;
  lastLoginAt: Date | null;
  lastGenerationAt: Date | null;
  lastActivityAt: Date | null;
  credits: number;
  tier: string;
  subscriptionActive: boolean;
  creditsExpireAt: Date | null;
  emailVerified: boolean;
  projectCount: number;
  completedVideoCount: number;
  openTicketCount: number;
  failedPaymentCount: number;
  recentGenerationCount: number;
};

export type ChurnResult = {
  riskLevel: RiskLevel;
  riskScore: number;
  signals: ChurnSignal[];
  recommendations: string[];
};

function daysSince(from: Date | null, now: Date): number | null {
  if (!from) return null;
  return Math.floor((now.getTime() - from.getTime()) / 86_400_000);
}

export function buildChurnSignals(input: ChurnInput): ChurnResult {
  const signals: ChurnSignal[] = [];
  const recommendations: string[] = [];
  let score = 0;

  const inactiveDays = daysSince(input.lastActivityAt, input.now);
  const loginGap = daysSince(input.lastLoginAt, input.now);
  const genGap = daysSince(input.lastGenerationAt, input.now);

  if (!input.emailVerified) {
    score += 25;
    signals.push({
      id: "email_unverified",
      severity: "warn",
      label: "Email not verified",
      detail: "Studio access requires a verified email.",
    });
    recommendations.push("Verify your email to unlock Studio and Dashboard.");
  }

  if (inactiveDays !== null && inactiveDays >= 21) {
    score += 35;
    signals.push({
      id: "inactive_21d",
      severity: "critical",
      label: "Inactive 21+ days",
      detail: `No login or generation activity for ${inactiveDays} days.`,
    });
    recommendations.push(
      "Open Studio and complete a short render to re-activate your workflow."
    );
  } else if (inactiveDays !== null && inactiveDays >= 10) {
    score += 20;
    signals.push({
      id: "inactive_10d",
      severity: "warn",
      label: "Low recent engagement",
      detail: `Last activity was ${inactiveDays} days ago.`,
    });
    recommendations.push("Visit Retention Center for tips and feature discovery.");
  } else if (inactiveDays === null && daysSince(input.createdAt, input.now)! >= 3) {
    score += 15;
    signals.push({
      id: "never_active",
      severity: "warn",
      label: "No recorded activity yet",
      detail: "No last login or generation timestamp on this account.",
    });
    recommendations.push("Sign in and create your first Studio project.");
  }

  if (input.subscriptionActive && input.credits <= 10) {
    score += 25;
    signals.push({
      id: "low_credits",
      severity: "warn",
      label: "Low credit balance",
      detail: `Only ${input.credits} seconds remaining on an active plan.`,
    });
    recommendations.push(
      "Upgrade plan or wait for renewal — generation stops when credits hit zero."
    );
  } else if (!input.subscriptionActive && input.credits <= 0 && input.tier !== "free") {
    score += 30;
    signals.push({
      id: "expired_pool",
      severity: "critical",
      label: "Credits exhausted / plan inactive",
      detail: "Subscription inactive and credit balance is zero.",
    });
    recommendations.push("Renew or choose Tester / Standard / Premium on Pricing.");
  }

  if (
    input.creditsExpireAt &&
    input.creditsExpireAt.getTime() < input.now.getTime() &&
    input.credits > 0
  ) {
    score += 20;
    signals.push({
      id: "credits_expired",
      severity: "warn",
      label: "Credit pool past expiry date",
      detail: `creditsExpireAt is ${input.creditsExpireAt.toISOString()}.`,
    });
    recommendations.push("Check Billing — expired pools may no longer be usable.");
  }

  if (input.tier === "tester" && input.creditsExpireAt) {
    const daysLeft = Math.ceil(
      (input.creditsExpireAt.getTime() - input.now.getTime()) / 86_400_000
    );
    if (daysLeft <= 2 && daysLeft >= 0) {
      score += 15;
      signals.push({
        id: "tester_expiring",
        severity: "warn",
        label: "Tester window ending soon",
        detail: `About ${daysLeft} day(s) left on the 5-day Tester pool.`,
      });
      recommendations.push(
        "Upgrade to Standard ($89) or Premium ($249) before Tester credits expire."
      );
    }
  }

  if (input.failedPaymentCount > 0) {
    score += 40;
    signals.push({
      id: "failed_payments",
      severity: "critical",
      label: "Failed or canceled payment events",
      detail: `${input.failedPaymentCount} billing transaction(s) matched failure/cancel rules.`,
    });
    recommendations.push(
      "Review Billing history and update payment method via your Paddle customer portal."
    );
  }

  if (input.openTicketCount >= 2) {
    score += 10;
    signals.push({
      id: "open_tickets",
      severity: "info",
      label: "Multiple open support tickets",
      detail: `${input.openTicketCount} tickets still open or waiting.`,
    });
    recommendations.push("Reply on open tickets so support can close blockers.");
  }

  if (input.projectCount === 0 || input.completedVideoCount === 0) {
    score += 15;
    signals.push({
      id: "no_first_value",
      severity: "warn",
      label: "First value not reached",
      detail:
        input.completedVideoCount === 0
          ? "No completed generation jobs yet."
          : "No projects saved yet.",
    });
    recommendations.push("Follow Getting Started on /success and complete one render.");
  }

  if (input.recentGenerationCount === 0 && (genGap ?? 99) >= 7 && input.subscriptionActive) {
    score += 10;
    signals.push({
      id: "paid_idle",
      severity: "warn",
      label: "Paid plan with no recent generations",
      detail: "Active subscription but zero generations in the last 14 days.",
    });
    recommendations.push(
      "Use Retention Center tutorials and feature tips to put credits to work."
    );
  }

  if (loginGap !== null && loginGap >= 14 && input.subscriptionActive) {
    score += 10;
    signals.push({
      id: "login_gap",
      severity: "warn",
      label: "Long gap since last login",
      detail: `Last login ${loginGap} days ago.`,
    });
  }

  if (signals.length === 0) {
    signals.push({
      id: "healthy",
      severity: "info",
      label: "No churn risk signals",
      detail: "Account activity and billing signals look stable from available data.",
    });
    recommendations.push("Explore Premium 4K or invite a teammate via referral when ready.");
  }

  score = Math.min(100, score);
  let riskLevel: RiskLevel = "healthy";
  if (score >= 70) riskLevel = "critical";
  else if (score >= 45) riskLevel = "at_risk";
  else if (score >= 20) riskLevel = "watch";

  // Dedupe recommendations while preserving order
  const seen = new Set<string>();
  const uniqueRecs = recommendations.filter((r) => {
    if (seen.has(r)) return false;
    seen.add(r);
    return true;
  });

  return {
    riskLevel,
    riskScore: score,
    signals,
    recommendations: uniqueRecs.slice(0, 6),
  };
}
