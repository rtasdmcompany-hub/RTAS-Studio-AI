"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import type { PaidPlanType } from "@rtas/shared";
import { loadProfile, saveProfile } from "@/lib/store";
import { startCheckout } from "@/lib/checkout-client";
import { PRICING_TIERS, planDisplayName } from "@/lib/pricing-tiers";
import {
  PricingCheckoutModal,
  type PricingCheckoutModalState,
} from "@/components/marketing/PricingCheckoutModal";

function FeatureChecklist({
  features,
}: {
  features: (typeof PRICING_TIERS)[number]["features"];
}) {
  return (
    <dl className="rtas-pricing-tier__matrix" aria-label="Plan feature comparison">
      {features.map((row) => (
        <div
          key={row.label}
          className={`rtas-pricing-tier__matrix-row${
            row.included ? "" : " rtas-pricing-tier__matrix-row--muted"
          }`}
        >
          <dt>{row.label}</dt>
          <dd>
            <span
              className={`rtas-pricing-tier__check${
                row.included
                  ? " rtas-pricing-tier__check--yes"
                  : " rtas-pricing-tier__check--no"
              }`}
              aria-hidden
            >
              {row.included ? "✓" : "—"}
            </span>
            {row.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

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
          planLabel: planDisplayName(plan),
          message: result.message ?? `${planDisplayName(plan)} is active.`,
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
      <section id="plans" className="rtas-pricing-matrix">
        {PRICING_TIERS.map((tier) => (
          <article
            key={tier.plan}
            className={`rtas-pricing-tier${
              tier.featured ? " rtas-pricing-tier--featured" : ""
            }`}
          >
            {tier.featured ? (
              <span className="rtas-pricing-tier__badge">Most Popular</span>
            ) : null}

            <p className="rtas-pricing-tier__subtitle">{tier.subtitle}</p>
            <h2 className="rtas-pricing-tier__name">{tier.name}</h2>
            <p className="rtas-pricing-tier__price">
              ${tier.price}
              <span>{tier.priceSuffix}</span>
            </p>
            <p className="rtas-pricing-tier__credits">{tier.creditsLabel}</p>

            <ul className="rtas-pricing-tier__highlights">
              {tier.highlights.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>

            <FeatureChecklist features={tier.features} />

            <button
              type="button"
              className="rtas-btn-lavender rtas-pricing-tier__cta"
              disabled={busy !== null}
              onClick={() => void runCheckout(tier.plan)}
            >
              {busy === tier.plan ? "Starting…" : tier.ctaLabel}
            </button>
          </article>
        ))}

        <p className="rtas-pricing-matrix__note">
          After payment you&apos;ll return to Studio with credits ready.{" "}
          <Link href="/studio">Go to workspace</Link>
        </p>
      </section>

      <PricingCheckoutModal state={modal} onClose={() => setModal(null)} />
    </>
  );
}
