"use client";

import type { PaidPlanType } from "@rtas/shared";
import { Button, ButtonLink, Dialog } from "@rtas/ui";
import { planDisplayName } from "@/lib/pricing-tiers";

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
  return (
    <Dialog
      open={Boolean(state)}
      onClose={onClose}
      variant="checkout"
      titleId="pricing-checkout-title"
      closeOnEscape
      closeOnOverlayClick
      showGlow={false}
    >
      {state?.kind === "success" ? (
        <>
          {state.demo ? (
            <span className="rtas-checkout-modal__tag">Development mode — no real payment</span>
          ) : null}
          <h2 id="pricing-checkout-title" className="rtas-checkout-modal__title">
            {state.planLabel} activated
          </h2>
          <p className="rtas-checkout-modal__message">{state.message}</p>
          <ButtonLink href="/studio" variant="lavender" className="rtas-checkout-modal__primary">
            Open Studio →
          </ButtonLink>
          <button type="button" className="rtas-checkout-modal__close rtas-ui-focus-ring" onClick={onClose}>
            Stay on pricing
          </button>
        </>
      ) : state?.kind === "info" ? (
        <>
          <h2 id="pricing-checkout-title" className="rtas-checkout-modal__title">
            {state.title}
          </h2>
          <p className="rtas-checkout-modal__message">{state.message}</p>
          <Button
            type="button"
            variant="lavender"
            className="rtas-checkout-modal__primary"
            onClick={onClose}
          >
            OK
          </Button>
        </>
      ) : null}
    </Dialog>
  );
}

export function planLabelFor(plan: PaidPlanType): string {
  return planDisplayName(plan);
}
