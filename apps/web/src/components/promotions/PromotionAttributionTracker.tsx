"use client";

import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";

export function PromotionAttributionTracker() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    const promo = searchParams.get("promo");
    const placement = searchParams.get("promoPlacement");
    const pagePath = searchParams.get("promoPage") || pathname || "/";
    const payment = searchParams.get("payment");
    const variantId = searchParams.get("promoVariant");
    const revenueUsd = Number(searchParams.get("promoRevenueUsd") || "0");

    if (!promo || !placement || payment !== "success") return;

    const dedupeKey = `rtas:promo:conversion:${promo}:${variantId || "control"}:${placement}:${pagePath}`;
    if (sessionStorage.getItem(dedupeKey)) return;
    sessionStorage.setItem(dedupeKey, "1");

    void fetch("/api/promotions/interactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        promotionId: promo,
        variantId,
        action: "conversion",
        placement,
        pagePath,
        revenueAmountUsd: Number.isFinite(revenueUsd) ? revenueUsd : 0,
      }),
    }).catch(() => {
      sessionStorage.removeItem(dedupeKey);
    });
  }, [pathname, searchParams]);

  return null;
}
