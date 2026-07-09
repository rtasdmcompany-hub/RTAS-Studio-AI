import {
  creditsForPaidPlan,
  TESTER_DURATION_DAYS,
  type UserProfile,
  type PaidPlanType,
} from "@rtas/shared";
import { activatePlan } from "@/lib/store";

export type CheckoutPlan = PaidPlanType;

export type CheckoutResult = {
  openedUrl?: string;
  activated?: boolean;
  profile?: UserProfile;
  message?: string;
  paymentPending?: boolean;
  demo?: boolean;
};

export type CheckoutOptions = {
  /** Only when user confirms early resubscribe rollover */
  rolloverRemaining?: boolean;
};

/** Shared Paddle / Lemon Squeezy / local demo checkout for Studio + Profile. */
export async function startCheckout(
  profile: UserProfile,
  plan: CheckoutPlan = "standard",
  options?: CheckoutOptions
): Promise<CheckoutResult> {
  const res = await fetch("/api/checkout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: profile.email,
      plan,
    }),
  });

  const data = (await res.json().catch(() => ({}))) as {
    url?: string;
    localActivateUrl?: string;
    message?: string;
    error?: string;
    demo?: boolean;
  };

  if (!res.ok) {
    return {
      message:
        data.error ?? data.message ?? "Checkout could not start. Please try again.",
    };
  }

  if (data.url) {
    const popup = window.open(data.url, "_blank", "noopener,noreferrer");
    if (!popup) {
      window.location.href = data.url;
    }
    return {
      openedUrl: data.url,
      paymentPending: true,
      message:
        "Secure checkout opened — complete payment in the new tab. Credits unlock automatically when finished.",
    };
  }

  if (data.demo) {
    const nextProfile = activatePlan(profile, plan, options);
    void fetch("/api/admin/fal-funding/refresh", { method: "POST" }).catch(() => {});

    const grant = creditsForPaidPlan(plan);
    const labels: Record<CheckoutPlan, string> = {
      tester: `${grant} seconds added — valid for ${TESTER_DURATION_DAYS} days. You're ready to create.`,
      standard: `${grant} seconds added for 1 month. HD studio unlocked.`,
      premium: `${grant} seconds added for 1 month. Premium 4K studio unlocked.`,
    };

    return {
      activated: true,
      profile: nextProfile,
      demo: true,
      message: labels[plan],
    };
  }

  if (data.localActivateUrl) {
    window.location.href = data.localActivateUrl;
    return { openedUrl: data.localActivateUrl };
  }

  const nextProfile = activatePlan(profile, plan, options);
  void fetch("/api/admin/fal-funding/refresh", { method: "POST" }).catch(() => {});

  const grant = creditsForPaidPlan(plan);
  const labels: Record<CheckoutPlan, string> = {
    tester: `Tester active — ${grant} credits for 5 days.`,
    standard: `Standard active — ${grant} credits added (1 month).`,
    premium: `Premium 4K active — ${grant} credits added (1 month).`,
  };

  return {
    activated: true,
    profile: nextProfile,
    message: labels[plan],
  };
}
