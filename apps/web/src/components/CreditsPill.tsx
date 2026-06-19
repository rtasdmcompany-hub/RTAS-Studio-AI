"use client";

import { useStudioProfile } from "@/context/StudioProfileContext";
import { creditsLabel } from "@/lib/monetization";
import { isPaidTier } from "@rtas/shared";

export function CreditsPill() {
  const { profile } = useStudioProfile();

  if (!profile) {
    return (
      <span className="credits-pill">
        Credits: <strong>…</strong>
      </span>
    );
  }

  const isPaid = profile.subscriptionActive || isPaidTier(profile.tier);

  return (
    <span
      className="credits-pill"
      title={isPaid ? "Paid plan credits" : "Subscribe for credits"}
    >
      Credits: <strong>{creditsLabel(profile)}</strong>
    </span>
  );
}
