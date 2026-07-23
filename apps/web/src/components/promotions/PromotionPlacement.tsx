"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { UserProfile } from "@rtas/shared";
import { Button, Card } from "@rtas/ui";
import { startCheckout } from "@/lib/checkout-client";
import type { PromotionRecord, PromotionResolved } from "@/lib/promotions/types";

type PlacementPayload = {
  ok?: boolean;
  promotions?: PromotionResolved[];
  sessionId?: string;
};

type Props = {
  placement: string;
  pagePath: string;
  profile?: UserProfile | null;
  title?: string;
  emptyMinHeightClassName?: string;
};

export function PromotionPlacement({
  placement,
  pagePath,
  profile,
  title,
  emptyMinHeightClassName = "min-h-[5rem]",
}: Props) {
  const [promotions, setPromotions] = useState<PromotionResolved[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [dismissed, setDismissed] = useState<string[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(`rtas:promo:dismissed:${placement}`);
      setDismissed(raw ? (JSON.parse(raw) as string[]) : []);
    } catch {
      setDismissed([]);
    }
  }, [placement]);

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams({ placement, pagePath });
    void fetch(`/api/promotions/placements?${params.toString()}`, {
      cache: "no-store",
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((json: PlacementPayload | null) => {
        if (cancelled || !json?.ok) return;
        setPromotions(Array.isArray(json.promotions) ? json.promotions : []);
        setSessionId(json.sessionId || "");
      })
      .catch(() => {
        if (!cancelled) {
          setPromotions([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [placement, pagePath]);

  const visible = useMemo(
    () => promotions.filter((item) => !dismissed.includes(item.promotion.id)),
    [dismissed, promotions]
  );

  useEffect(() => {
    for (const item of visible) {
      const variantId = item.variant?.id || "control";
      const key = `rtas:promo:view:${item.promotion.id}:${variantId}:${placement}:${pagePath}`;
      if (sessionStorage.getItem(key)) continue;
      sessionStorage.setItem(key, "1");
      void fetch("/api/promotions/interactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          promotionId: item.promotion.id,
          variantId: item.variant?.id ?? null,
          action: "view",
          placement,
          pagePath,
          sessionId,
        }),
      }).catch(() => {
        sessionStorage.removeItem(key);
      });
    }
  }, [pagePath, placement, sessionId, visible]);

  async function handleDismiss(item: PromotionResolved) {
    const next = [...dismissed, item.promotion.id];
    setDismissed(next);
    localStorage.setItem(`rtas:promo:dismissed:${placement}`, JSON.stringify(next));
    await fetch("/api/promotions/interactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        promotionId: item.promotion.id,
        variantId: item.variant?.id ?? null,
        action: "dismiss",
        placement,
        pagePath,
        sessionId,
      }),
    }).catch(() => undefined);
  }

  async function handleCheckout(item: PromotionResolved, promotion: PromotionRecord) {
    if (!profile || !promotion.checkoutPlan) return;
    setBusyId(item.promotion.id);
    try {
      await fetch("/api/promotions/interactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          promotionId: item.promotion.id,
          variantId: item.variant?.id ?? null,
          action: "click",
          placement,
          pagePath,
          sessionId,
        }),
      });

      await startCheckout(profile, promotion.checkoutPlan, {
        promotionAttribution: {
          promotionId: promotion.id,
          variantId: item.variant?.id ?? null,
          placement,
          pagePath,
          revenueValueUsd: promotion.revenueValueCents / 100,
        },
      });
    } finally {
      setBusyId(null);
    }
  }

  async function trackClick(item: PromotionResolved) {
    await fetch("/api/promotions/interactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        promotionId: item.promotion.id,
        variantId: item.variant?.id ?? null,
        action: "click",
        placement,
        pagePath,
        sessionId,
      }),
    }).catch(() => undefined);
  }

  if (visible.length === 0) {
    return <div className={emptyMinHeightClassName} aria-hidden />;
  }

  if (placement === "homepage_announcement") {
    const item = visible[0];
    const promotion = item.promotion;
    return (
      <section
        aria-label="Announcement"
        className="mb-5 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 shadow-[0_12px_40px_rgba(0,0,0,0.18)] backdrop-blur-md"
      >
        <div className="flex flex-wrap items-center gap-3">
          <span className="rounded-full border border-white/10 bg-white/10 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-zinc-100">
            {promotion.badgeText || "Announcement"}
          </span>
          <p className="flex-1 text-sm text-zinc-100">
            <strong>{item.variant?.headline || promotion.title}</strong>{" "}
            <span className="text-ds-text-muted">
              {item.variant?.body || promotion.description}
            </span>
          </p>
          <Link
            href={promotion.ctaHref}
            className="rounded-xl border border-ds-accent-lavender/40 bg-ds-accent-lavender/10 px-3 py-2 text-sm font-medium text-zinc-100 transition hover:bg-ds-accent-lavender/20"
            onClick={() => void trackClick(item)}
          >
            {item.variant?.ctaLabel || promotion.ctaLabel}
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className={emptyMinHeightClassName} aria-label={title || "Recommended promotions"}>
      {title ? <h2 className="mb-3 text-sm uppercase tracking-wide text-ds-text-muted">{title}</h2> : null}
      <div className="grid gap-3">
        {visible.map((item) => {
          const promotion = item.promotion;
          const label =
            promotion.sponsorLabel ||
            (promotion.promotionType === "partner" ? "Sponsored Partner" : promotion.badgeText);
          return (
            <Card
              key={promotion.id}
              variant="glass"
              className="relative overflow-hidden rounded-3xl border border-white/10 p-5"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  {label ? (
                    <span className="inline-flex rounded-full border border-white/10 bg-white/10 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-zinc-100">
                      {label}
                    </span>
                  ) : null}
                  <h3 className="mt-3 text-lg font-semibold text-zinc-100">
                    {item.variant?.headline || promotion.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-ds-text-muted">
                    {item.variant?.body || promotion.description}
                  </p>
                </div>
                {promotion.dismissible ? (
                  <button
                    type="button"
                    className="rounded-full border border-white/10 px-2 py-1 text-xs text-ds-text-muted hover:text-zinc-100"
                    aria-label={`Dismiss ${promotion.title}`}
                    onClick={() => void handleDismiss(item)}
                  >
                    Dismiss
                  </button>
                ) : null}
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-3">
                {promotion.ctaKind === "checkout" && profile && promotion.checkoutPlan ? (
                  <Button
                    variant="primary"
                    loading={busyId === promotion.id}
                    loadingLabel="Opening checkout..."
                    onClick={() => void handleCheckout(item, promotion)}
                  >
                    {item.variant?.ctaLabel || promotion.ctaLabel}
                  </Button>
                ) : (
                  <Link
                    href={promotion.ctaHref}
                    className="inline-flex items-center rounded-xl border border-ds-accent-lavender/40 bg-ds-accent-lavender/10 px-4 py-2 text-sm font-medium text-zinc-100 transition hover:bg-ds-accent-lavender/20"
                    onClick={() => void trackClick(item)}
                  >
                    {item.variant?.ctaLabel || promotion.ctaLabel}
                  </Link>
                )}
                {promotion.sponsorName ? (
                  <span className="text-xs text-ds-text-muted">Source: {promotion.sponsorName}</span>
                ) : null}
              </div>
            </Card>
          );
        })}
      </div>
    </section>
  );
}
