"use client";

import Link from "next/link";
import type { PaidPlanType } from "@rtas/shared";

export type PricingCheckoutModalState =
  | {
      kind: "success";
      planLabel: string;
      message: string;
      demo: boolean;
    }
  | {
      kind: "info";
      title: string;
      message: string;
    };

type Props = {
  state: PricingCheckoutModalState | null;
  onClose: () => void;
};

export function PricingCheckoutModal({ state, onClose }: Props) {
  if (!state) return null;

  return (
    <div
      className="rtas-checkout-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pricing-checkout-title"
      onClick={onClose}
    >
      <div
        className="rtas-checkout-modal"
        onClick={(e) => e.stopPropagation()}
      >
        {state.kind === "success" ? (
          <>
            {state.demo ? (
              <span className="rtas-checkout-modal__tag">Development mode — no real payment</span>
            ) : null}
            <h2 id="pricing-checkout-title" className="rtas-checkout-modal__title">
              {state.planLabel} activated
            </h2>
            <p className="rtas-checkout-modal__message">{state.message}</p>
            <Link href="/studio" className="rtas-btn-lavender rtas-checkout-modal__primary">
              Open Studio →
            </Link>
            <button type="button" className="rtas-checkout-modal__close" onClick={onClose}>
              Stay on pricing
            </button>
          </>
        ) : (
          <>
            <h2 id="pricing-checkout-title" className="rtas-checkout-modal__title">
              {state.title}
            </h2>
            <p className="rtas-checkout-modal__message">{state.message}</p>
            <button
              type="button"
              className="rtas-btn-lavender rtas-checkout-modal__primary"
              onClick={onClose}
            >
              OK
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export function planLabelFor(plan: PaidPlanType): string {
  if (plan === "tester") return "Tester";
  if (plan === "premium") return "Premium 4K";
  return "Standard";
}
