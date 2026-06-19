"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FREE_TRIAL_DURATION_SECONDS,
  PREMIUM_CREDITS,
  PREMIUM_PRICE_USD,
  STANDARD_CREDITS,
  STANDARD_PRICE_USD,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
  type PaidPlanType,
} from "@rtas/shared";
import {
  applyCreditExpiry,
  loadProfile,
  mergeServerProfile,
  saveProfile,
} from "@/lib/store";
import { shouldConfirmEarlyResubscribe } from "@/lib/monetization";
import { startCheckout } from "@/lib/checkout-client";
import { EarlyResubscribeModal } from "@/components/EarlyResubscribeModal";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";

export default function ProfilePage() {
  const [profile, setProfile] = useState<Awaited<ReturnType<typeof loadProfile>> | null>(null);
  const [showEarlyResubscribe, setShowEarlyResubscribe] = useState(false);
  const [pendingPlan, setPendingPlan] = useState<PaidPlanType>("standard");
  const [checkoutBusy, setCheckoutBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    let p = applyCreditExpiry(loadProfile());
    saveProfile(p);
    void fetch(`/api/user/subscription?userId=${encodeURIComponent(p.id)}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((server) => {
        if (server) {
          p = mergeServerProfile(p, {
            ...p,
            tier: server.tier ?? p.tier,
            subscriptionActive: server.subscriptionActive ?? p.subscriptionActive,
            credits: server.credits ?? p.credits,
            creditsExpireAt: server.creditsExpireAt ?? p.creditsExpireAt,
            subscriptionRenewsAt:
              server.subscriptionRenewsAt ?? p.subscriptionRenewsAt,
            paymentProvider: server.paymentProvider ?? p.paymentProvider,
            freeTrialUsed: server.freeTrialUsed ?? p.freeTrialUsed,
            hasUsedFreeTrial:
              server.hasUsedFreeTrial ?? server.freeTrialUsed ?? p.hasUsedFreeTrial,
          });
          saveProfile(p);
        }
        setProfile(p);
      })
      .catch(() => setProfile(p));
  }, []);

  const runCheckout = async (
    plan: PaidPlanType,
    options?: { rolloverRemaining?: boolean }
  ) => {
    if (!profile || checkoutBusy) return;
    setCheckoutBusy(true);
    setStatus(null);
    try {
      const result = await startCheckout(profile, plan, options);
      if (result.profile) {
        saveProfile(result.profile);
        setProfile(result.profile);
      }
      if (result.message) setStatus(result.message);
      else if (result.openedUrl) setStatus("Checkout opened in a new tab.");
    } finally {
      setCheckoutBusy(false);
    }
  };

  const onMonthlyClick = (plan: "standard" | "premium") => {
    if (!profile) return;
    if (shouldConfirmEarlyResubscribe(profile) && profile.tier === plan) {
      setPendingPlan(plan);
      setShowEarlyResubscribe(true);
      return;
    }
    void runCheckout(plan);
  };

  if (!profile) return <p style={{ padding: "2rem" }}>Loading…</p>;

  const tierLabel =
    profile.tier === "premium"
      ? "Premium 4K"
      : profile.tier === "standard"
        ? "Standard"
        : profile.tier === "tester"
          ? "Tester"
          : "Free";

  return (
    <MarketingLayout>
      <div className="rtas-profile-wrap profile-page video-content-panel">
        <EarlyResubscribeModal
          open={showEarlyResubscribe}
          remainingCredits={profile.credits}
          creditsExpireAt={profile.creditsExpireAt}
          onConfirm={() => void runCheckout(pendingPlan, { rolloverRemaining: true })}
          onCancel={() => setShowEarlyResubscribe(false)}
        />

        <Link href="/studio">← Back to Studio</Link>
        <h1>Your profile</h1>
        <p className="profile-tier">
          Plan: <strong>{tierLabel}</strong>
        </p>

        <div className="profile-grid">
          <div className="profile-card">
            <p>
              <strong>Name:</strong> {profile.name}
            </p>
            <p>
              <strong>Email:</strong> {profile.email}
            </p>
            {profile.paymentProvider && (
              <p>
                <strong>Billing:</strong> {profile.paymentProvider}
              </p>
            )}
          </div>
          <div className="profile-card">
            <p>
              <strong>{FREE_TRIAL_DURATION_SECONDS}s preview:</strong>{" "}
              {profile.freeTrialUsed || profile.hasUsedFreeTrial ? "Used" : "Available once"}
            </p>
            <p>
              <strong>Subscription:</strong>{" "}
              {profile.subscriptionActive ? "Active" : "None"}
            </p>
            <p>
              <strong>Credits:</strong> {profile.credits}{" "}
              <span className="profile-note">(1 credit = 1 second of video)</span>
            </p>
            {profile.creditsExpireAt && (
              <p>
                <strong>Credits expire:</strong>{" "}
                {new Date(profile.creditsExpireAt).toLocaleDateString()}
              </p>
            )}
          </div>
        </div>

        {status ? (
          <p className="profile-status" role="status">
            {status}
          </p>
        ) : null}

        <div className="profile-checkout-row">
          <button
            type="button"
            className="btn-secondary profile-sub-btn"
            disabled={checkoutBusy}
            onClick={() => void runCheckout("tester")}
          >
            Tester — ${TESTER_PRICE_USD} · {TESTER_CREDITS}s · {TESTER_DURATION_DAYS} days
          </button>
          <button
            type="button"
            className="btn-primary profile-sub-btn"
            disabled={checkoutBusy}
            onClick={() => onMonthlyClick("standard")}
          >
            Standard — ${STANDARD_PRICE_USD}/mo · {STANDARD_CREDITS}s
          </button>
          <button
            type="button"
            className="btn-primary profile-sub-btn"
            disabled={checkoutBusy}
            onClick={() => onMonthlyClick("premium")}
          >
            Premium 4K — ${PREMIUM_PRICE_USD}/mo · {PREMIUM_CREDITS}s
          </button>
        </div>

        <footer className="profile-legal">
          <Link href="/terms">Terms</Link>
          <Link href="/privacy">Privacy</Link>
          <Link href="/cookies">Cookies</Link>
          <Link href="/pricing#plans">Pricing</Link>
        </footer>
      </div>
    </MarketingLayout>
  );
}
