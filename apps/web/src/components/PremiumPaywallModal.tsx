"use client";

import { useEffect } from "react";
import Link from "next/link";
import {
  PREMIUM_CREDITS,
  PREMIUM_PRICE_USD,
  STANDARD_CREDITS,
  STANDARD_PRICE_USD,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
} from "@rtas/shared";
import { Button, Dialog } from "@rtas/ui";
import { trackClientEvent } from "@/lib/analytics";
import { AnalyticsEvents } from "@/lib/analytics/events";

type Props = {
  open: boolean;
  message?: string;
  /** Current account tier for context-aware compare (no misleading urgency). */
  currentTier?: string;
  creditsRequired?: number;
  creditsAvailable?: number;
  onSubscribeTester: () => void;
  onSubscribeStandard: () => void;
  onSubscribePremium: () => void;
  onClose: () => void;
};

function planHint(currentTier: string | undefined, plan: string): string | null {
  if (!currentTier || currentTier === "free") return null;
  if (currentTier === plan) return "Your current plan";
  if (currentTier === "premium" && plan !== "premium") return "Lower tier";
  if (currentTier === "standard" && plan === "tester") return "Evaluation pass";
  if (currentTier === "tester" && (plan === "standard" || plan === "premium")) {
    return "Upgrade path";
  }
  return null;
}

export function PremiumPaywallModal({
  open,
  message,
  currentTier,
  creditsRequired,
  creditsAvailable,
  onSubscribeTester,
  onSubscribeStandard,
  onSubscribePremium,
  onClose,
}: Props) {
  useEffect(() => {
    if (!open) return;
    trackClientEvent(AnalyticsEvents.UPGRADE_PROMPT_SHOWN, {
      tier: currentTier ?? "unknown",
      creditsRequired: creditsRequired ?? null,
      creditsAvailable: creditsAvailable ?? null,
    });
  }, [open, currentTier, creditsRequired, creditsAvailable]);

  const contextLine =
    typeof creditsRequired === "number" && typeof creditsAvailable === "number"
      ? `This render needs ${creditsRequired}s · you have ${creditsAvailable}s.`
      : null;

  return (
    <Dialog
      open={open}
      variant="paywall"
      titleId="paywall-title"
      contentClassName="paywall-modal paywall-modal--wide"
      onClose={onClose}
      closeOnEscape
    >
      <h2 id="paywall-title" className="paywall-title">
        {creditsAvailable === 0 ? "You have no credits" : "Need more credits"}
      </h2>
      <p className="paywall-desc">
        {message ??
          `Add credits to generate. Tester starts at $${TESTER_PRICE_USD} — new accounts begin at 0 credits (not a free credit plan).`}
      </p>
      {contextLine ? <p className="paywall-desc paywall-desc--context">{contextLine}</p> : null}
      <p className="paywall-desc paywall-desc--context">
        Compare calmly — no countdown timers. 1 credit = 1 second of finished video.
      </p>

      <div className="paywall-compare" role="list" aria-label="Plan compare">
        <div className="paywall-compare__row" role="listitem">
          <div>
            <strong>Tester</strong>
            <span>
              ${TESTER_PRICE_USD} · {TESTER_CREDITS}s · {TESTER_DURATION_DAYS} days
            </span>
            {planHint(currentTier, "tester") ? (
              <em>{planHint(currentTier, "tester")}</em>
            ) : null}
          </div>
          <Button
            variant="paywall-tester"
            onClick={() => {
              trackClientEvent(AnalyticsEvents.UPGRADE_CTA_CLICKED, { plan: "tester" });
              onSubscribeTester();
            }}
          >
            Get Tester
          </Button>
        </div>
        <div className="paywall-compare__row" role="listitem">
          <div>
            <strong>Standard</strong>
            <span>
              ${STANDARD_PRICE_USD}/mo · {STANDARD_CREDITS}s · HD commercial
            </span>
            {planHint(currentTier, "standard") ? (
              <em>{planHint(currentTier, "standard")}</em>
            ) : null}
          </div>
          <Button
            variant="paywall-standard"
            onClick={() => {
              trackClientEvent(AnalyticsEvents.UPGRADE_CTA_CLICKED, { plan: "standard" });
              onSubscribeStandard();
            }}
          >
            Go Standard
          </Button>
        </div>
        <div className="paywall-compare__row" role="listitem">
          <div>
            <strong>Premium 4K</strong>
            <span>
              ${PREMIUM_PRICE_USD}/mo · {PREMIUM_CREDITS}s · cinematic 4K
            </span>
            {planHint(currentTier, "premium") ? (
              <em>{planHint(currentTier, "premium")}</em>
            ) : null}
          </div>
          <Button
            variant="paywall"
            onClick={() => {
              trackClientEvent(AnalyticsEvents.UPGRADE_CTA_CLICKED, { plan: "premium" });
              onSubscribePremium();
            }}
          >
            Go Premium 4K
          </Button>
        </div>
      </div>

      <Link
        href="/pricing#plans"
        className="paywall-recharge-link"
        onClick={() =>
          trackClientEvent(AnalyticsEvents.PLAN_COMPARE_VIEWED, { from: "paywall" })
        }
      >
        Full plan comparison →
      </Link>

      <button type="button" className="paywall-skip-link rtas-ui-focus-ring" onClick={onClose}>
        Maybe later
      </button>
    </Dialog>
  );
}
