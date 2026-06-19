"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import {
  PREMIUM_CREDITS,
  PREMIUM_PRICE_USD,
  STANDARD_CREDITS,
  STANDARD_PRICE_USD,
  TESTER_CREDITS,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
  type PaidPlanType,
} from "@rtas/shared";
import { loadProfile, saveProfile } from "@/lib/store";
import { startCheckout } from "@/lib/checkout-client";
import {
  planLabelFor,
  PricingCheckoutModal,
  type PricingCheckoutModalState,
} from "@/components/marketing/PricingCheckoutModal";

export function PricingPlans() {
  const router = useRouter();
  const { data: session, status: authStatus } = useSession();
  const [busy, setBusy] = useState<PaidPlanType | null>(null);
  const [modal, setModal] = useState<PricingCheckoutModalState | null>(null);

  useEffect(() => {
    if (!modal) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setModal(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [modal]);

  const runCheckout = async (plan: PaidPlanType) => {
    if (busy) return;

    if (authStatus !== "loading" && !session?.user) {
      setModal({
        kind: "info",
        title: "Sign in required",
        message: "Please sign in first — then choose your plan again.",
      });
      router.push(`/auth/login?callbackUrl=${encodeURIComponent("/pricing#plans")}`);
      return;
    }

    setBusy(plan);
    setModal(null);

    try {
      const profile = loadProfile();
      if (session?.user?.id) {
        profile.id = session.user.id;
        profile.email = session.user.email ?? profile.email;
        profile.name = session.user.name ?? profile.name;
      }

      const result = await startCheckout(profile, plan);

      if (result.profile) {
        saveProfile(result.profile);
      }

      if (result.activated) {
        setModal({
          kind: "success",
          planLabel: planLabelFor(plan),
          message: result.message ?? `${planLabelFor(plan)} plan is active.`,
          demo: Boolean(result.demo),
        });
        return;
      }

      if (result.openedUrl && result.paymentPending) {
        setModal({
          kind: "info",
          title: "Complete payment",
          message:
            result.message ??
            "Secure checkout opened in a new tab. Complete payment there — credits unlock automatically when finished.",
        });
        return;
      }

      if (result.message) {
        setModal({
          kind: "info",
          title: "Checkout",
          message: result.message,
        });
      }
    } catch {
      setModal({
        kind: "info",
        title: "Something went wrong",
        message: "Please try again or email support@rtasdigital.com.",
      });
    } finally {
      setBusy(null);
    }
  };

  return (
    <>
      <section id="plans" className="rtas-pricing-grid">
        <article className="rtas-price-card">
          <h2>Tester</h2>
          <p className="rtas-price-card__price">
            ${TESTER_PRICE_USD} <span>one-time</span>
          </p>
          <ul>
            <li>
              <strong>{TESTER_CREDITS} seconds</strong> of video ({TESTER_DURATION_DAYS}-day access)
            </li>
            <li>Full studio workflow — lyrics, identity &amp; scenes</li>
            <li>Quick quality — perfect for your first test clip</li>
            <li>See how RTAS works before committing monthly</li>
          </ul>
          <button
            type="button"
            className="rtas-btn-lavender rtas-price-card__cta"
            disabled={busy !== null}
            onClick={() => void runCheckout("tester")}
          >
            {busy === "tester" ? "Starting…" : `Get Tester — $${TESTER_PRICE_USD}`}
          </button>
        </article>

        <article className="rtas-price-card rtas-price-card--featured">
          <span className="rtas-price-card__badge">Most popular</span>
          <h2>Standard</h2>
          <p className="rtas-price-card__price">
            ${STANDARD_PRICE_USD}
            <span>/month</span>
          </p>
          <ul>
            <li>
              <strong>{STANDARD_CREDITS} seconds</strong> every month (≈33 minutes)
            </li>
            <li>HD output for social posts, ads &amp; brand content</li>
            <li>Commercial rights on all paid exports</li>
            <li>Face-lock &amp; multi-scene music videos</li>
            <li>Best for creators publishing every week</li>
          </ul>
          <button
            type="button"
            className="rtas-btn-lavender rtas-price-card__cta"
            disabled={busy !== null}
            onClick={() => void runCheckout("standard")}
          >
            {busy === "standard" ? "Starting…" : `Get Standard — $${STANDARD_PRICE_USD}/mo`}
          </button>
        </article>

        <article className="rtas-price-card">
          <h2>Premium 4K</h2>
          <p className="rtas-price-card__price">
            ${PREMIUM_PRICE_USD}
            <span>/month</span>
          </p>
          <ul>
            <li>
              <strong>{PREMIUM_CREDITS} seconds</strong> every month (≈33 minutes)
            </li>
            <li>Cinematic <strong>4K</strong> — film-grade colour &amp; detail</li>
            <li>Advanced identity-lock for consistent faces across scenes</li>
            <li>Longest scenes &amp; richest visual quality</li>
            <li>Built for music videos, ads &amp; premium brand films</li>
          </ul>
          <button
            type="button"
            className="rtas-btn-lavender rtas-price-card__cta"
            disabled={busy !== null}
            onClick={() => void runCheckout("premium")}
          >
            {busy === "premium" ? "Starting…" : `Get Premium — $${PREMIUM_PRICE_USD}/mo`}
          </button>
        </article>

        <p className="rtas-pricing-note">
          After payment you&apos;ll return to Studio with credits ready.{" "}
          <Link href="/studio">Go to workspace</Link>
        </p>
      </section>

      <PricingCheckoutModal state={modal} onClose={() => setModal(null)} />
    </>
  );
}
