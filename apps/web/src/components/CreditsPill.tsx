"use client";

import Link from "next/link";
import { useStudioProfile } from "@/context/StudioProfileContext";
import { creditsLabel } from "@/lib/monetization";
import { isPaidTier } from "@rtas/shared";

export function CreditsPill() {
  const { profile } = useStudioProfile();

  if (!profile) {
    return (
      <Link href="/pricing" className="studio-credits" aria-busy="true">
        <span className="studio-credits__icon" aria-hidden>
          ◆
        </span>
        <span className="studio-credits__body">
          <span className="studio-credits__label">Credits</span>
          <strong className="studio-credits__value">…</strong>
        </span>
      </Link>
    );
  }

  const isPaid = profile.subscriptionActive || isPaidTier(profile.tier);
  const label = creditsLabel(profile);

  return (
    <Link
      href="/pricing"
      className={`studio-credits${isPaid ? " studio-credits--paid" : ""}`}
      title={isPaid ? "Manage plan & credits" : "Upgrade for more credits"}
    >
      <span className="studio-credits__icon" aria-hidden>
        ◆
      </span>
      <span className="studio-credits__body">
        <span className="studio-credits__label">{isPaid ? "Studio credits" : "Credits"}</span>
        <strong className="studio-credits__value">{label}</strong>
      </span>
      <span className="studio-credits__cta">{isPaid ? "Manage plan" : "Upgrade Credits"}</span>
    </Link>
  );
}
