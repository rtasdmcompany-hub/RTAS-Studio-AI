"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Card } from "@rtas/ui";
import { AdminMetricCard, AdminPageShell, formatUsd, useAdminSecret } from "@/components/admin/AdminShell";
import type { PromotionAdminRow } from "@/lib/promotions/types";

type Payload = {
  ok?: boolean;
  error?: string;
  promotions?: PromotionAdminRow[];
  summary?: {
    active: number;
    views: number;
    clicks: number;
    conversions: number;
    revenueGeneratedUsd: number;
  };
};

const EMPTY_FORM = {
  id: "",
  slug: "",
  title: "",
  description: "",
  promotionType: "internal",
  sponsorName: "",
  sponsorLabel: "",
  status: "draft",
  targetPage: "*",
  placements:
    "dashboard_sidebar, studio_recommendations, billing_upgrade, credits_upgrade",
  audienceRules:
    '{\n  "audiences": ["free_user"],\n  "plans": ["free"]\n}',
  variants:
    '[\n  {\n    "id": "control",\n    "headline": "Primary headline",\n    "body": "Variant copy for A/B testing.",\n    "ctaLabel": "Learn more"\n  }\n]',
  ctaLabel: "Learn more",
  ctaHref: "/pricing",
  ctaKind: "link",
  checkoutPlan: "",
  imageUrl: "",
  badgeText: "",
  priority: "100",
  dismissible: "true",
  revenueValueUsd: "0",
  startAt: "",
  endAt: "",
  metadataJson: '{\n  "theme": "glass"\n}',
};

export function PromotionsAdminClient() {
  const { secret, setSecret, stored, unlock, lock } = useAdminSecret();
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [data, setData] = useState<Payload | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  const load = useCallback(async (adminSecret: string) => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/promotions", {
        headers: { "x-rtas-admin-secret": adminSecret },
      });
      const json = (await res.json()) as Payload;
      if (!res.ok || !json.ok) {
        throw new Error(json.error ?? "Could not load promotions.");
      }
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load promotions.");
      setData(null);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (stored) void load(stored);
  }, [stored, load]);

  const summary = data?.summary;
  const promotions = data?.promotions ?? [];

  const selectedPreview = useMemo(() => {
    return {
      promotion: {
        id: form.id || "preview",
        slug: form.slug || "preview",
        title: form.title || "Promotion preview",
        description: form.description || "Preview your premium placement here.",
        promotionType: (form.promotionType as PromotionAdminRow["promotionType"]) || "internal",
        sponsorName: form.sponsorName || null,
        sponsorLabel: form.sponsorLabel || null,
        status: (form.status as PromotionAdminRow["status"]) || "draft",
        targetPage: form.targetPage || "*",
        placements: form.placements.split(",").map((v) => v.trim()).filter(Boolean),
        audienceRules: null,
        variants: [],
        ctaLabel: form.ctaLabel || "Learn more",
        ctaHref: form.ctaHref || "/pricing",
        ctaKind: (form.ctaKind === "checkout" ? "checkout" : "link") as
          | "link"
          | "checkout",
        checkoutPlan:
          form.checkoutPlan === "tester" ||
          form.checkoutPlan === "standard" ||
          form.checkoutPlan === "premium"
            ? form.checkoutPlan
            : null,
        imageUrl: form.imageUrl || null,
        badgeText: form.badgeText || null,
        priority: Number(form.priority || "100"),
        dismissible: form.dismissible !== "false",
        revenueValueCents: Math.round((Number(form.revenueValueUsd || "0") || 0) * 100),
        startAt: form.startAt || null,
        endAt: form.endAt || null,
        metadataJson: null,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      variant: null,
      placement: "dashboard_sidebar",
      pagePath: "/profile",
    };
  }, [form]);

  async function savePromotion() {
    if (!stored) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const body = new URLSearchParams(form);
      const res = await fetch("/api/admin/promotions", {
        method: "POST",
        headers: {
          "x-rtas-admin-secret": stored,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: body.toString(),
      });
      const json = (await res.json()) as Payload;
      if (!res.ok || !json.ok) {
        throw new Error(json.error ?? "Save failed.");
      }
      setData(json);
      setSuccess("Promotion saved.");
      setForm(EMPTY_FORM);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  function editPromotion(row: PromotionAdminRow) {
    setForm({
      id: row.id,
      slug: row.slug,
      title: row.title,
      description: row.description,
      promotionType: row.promotionType,
      sponsorName: row.sponsorName || "",
      sponsorLabel: row.sponsorLabel || "",
      status: row.status,
      targetPage: row.targetPage,
      placements: row.placements.join(", "),
      audienceRules: JSON.stringify(row.audienceRules ?? {}, null, 2),
      variants: JSON.stringify(row.variants ?? [], null, 2),
      ctaLabel: row.ctaLabel,
      ctaHref: row.ctaHref,
      ctaKind: row.ctaKind,
      checkoutPlan: row.checkoutPlan || "",
      imageUrl: row.imageUrl || "",
      badgeText: row.badgeText || "",
      priority: String(row.priority),
      dismissible: row.dismissible ? "true" : "false",
      revenueValueUsd: String(row.revenueValueCents / 100),
      startAt: row.startAt ? row.startAt.slice(0, 16) : "",
      endAt: row.endAt ? row.endAt.slice(0, 16) : "",
      metadataJson: JSON.stringify(row.metadataJson ?? {}, null, 2),
    });
  }

  return (
    <AdminPageShell
      title="Revenue Promotion Engine"
      subtitle="Premium internal, partner, and educational promotion management."
      stored={stored}
      secret={secret}
      setSecret={setSecret}
      unlock={unlock}
      lock={lock}
      busy={busy}
      error={error}
      onRefresh={() => void load(stored)}
    >
      {success ? <Alert variant="success" message={success} /> : null}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <AdminMetricCard label="Active promotions" value={summary?.active ?? 0} />
        <AdminMetricCard label="Views" value={summary?.views ?? 0} />
        <AdminMetricCard label="Clicks" value={summary?.clicks ?? 0} />
        <AdminMetricCard label="Conversions" value={summary?.conversions ?? 0} />
        <AdminMetricCard
          label="Revenue generated"
          value={formatUsd(summary?.revenueGeneratedUsd ?? 0)}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="space-y-4 p-5">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg text-zinc-100">
              {form.id ? "Edit promotion" : "Create promotion"}
            </h2>
            {form.id ? (
              <Button variant="ghost" onClick={() => setForm(EMPTY_FORM)}>
                New draft
              </Button>
            ) : null}
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <Field label="Promotion title" value={form.title} onChange={(value) => setForm((prev) => ({ ...prev, title: value }))} />
            <Field label="Slug" value={form.slug} onChange={(value) => setForm((prev) => ({ ...prev, slug: value }))} />
            <Field label="Promotion type" value={form.promotionType} onChange={(value) => setForm((prev) => ({ ...prev, promotionType: value }))} />
            <Field label="Status" value={form.status} onChange={(value) => setForm((prev) => ({ ...prev, status: value }))} />
            <Field label="Target page" value={form.targetPage} onChange={(value) => setForm((prev) => ({ ...prev, targetPage: value }))} />
            <Field label="Placements (CSV)" value={form.placements} onChange={(value) => setForm((prev) => ({ ...prev, placements: value }))} />
            <Field label="CTA label" value={form.ctaLabel} onChange={(value) => setForm((prev) => ({ ...prev, ctaLabel: value }))} />
            <Field label="CTA href" value={form.ctaHref} onChange={(value) => setForm((prev) => ({ ...prev, ctaHref: value }))} />
            <Field label="CTA kind" value={form.ctaKind} onChange={(value) => setForm((prev) => ({ ...prev, ctaKind: value }))} />
            <Field label="Checkout plan" value={form.checkoutPlan} onChange={(value) => setForm((prev) => ({ ...prev, checkoutPlan: value }))} />
            <Field label="Sponsor name" value={form.sponsorName} onChange={(value) => setForm((prev) => ({ ...prev, sponsorName: value }))} />
            <Field label="Sponsor label" value={form.sponsorLabel} onChange={(value) => setForm((prev) => ({ ...prev, sponsorLabel: value }))} />
            <Field label="Badge text" value={form.badgeText} onChange={(value) => setForm((prev) => ({ ...prev, badgeText: value }))} />
            <Field label="Priority" value={form.priority} onChange={(value) => setForm((prev) => ({ ...prev, priority: value }))} />
            <Field label="Revenue value USD" value={form.revenueValueUsd} onChange={(value) => setForm((prev) => ({ ...prev, revenueValueUsd: value }))} />
            <Field label="Dismissible" value={form.dismissible} onChange={(value) => setForm((prev) => ({ ...prev, dismissible: value }))} />
            <Field label="Start date" type="datetime-local" value={form.startAt} onChange={(value) => setForm((prev) => ({ ...prev, startAt: value }))} />
            <Field label="End date" type="datetime-local" value={form.endAt} onChange={(value) => setForm((prev) => ({ ...prev, endAt: value }))} />
            <Field label="Image URL" value={form.imageUrl} onChange={(value) => setForm((prev) => ({ ...prev, imageUrl: value }))} />
          </div>
          <Area label="Description" value={form.description} onChange={(value) => setForm((prev) => ({ ...prev, description: value }))} />
          <Area label="Audience rules JSON" value={form.audienceRules} onChange={(value) => setForm((prev) => ({ ...prev, audienceRules: value }))} />
          <Area label="Variants JSON" value={form.variants} onChange={(value) => setForm((prev) => ({ ...prev, variants: value }))} />
          <Area label="Metadata JSON" value={form.metadataJson} onChange={(value) => setForm((prev) => ({ ...prev, metadataJson: value }))} />
          <div className="flex flex-wrap gap-3">
            <Button variant="primary" loading={saving} loadingLabel="Saving..." onClick={() => void savePromotion()}>
              {form.id ? "Update promotion" : "Create promotion"}
            </Button>
            <Button variant="ghost" onClick={() => setForm(EMPTY_FORM)}>
              Reset
            </Button>
          </div>
        </Card>

        <div className="space-y-4">
          <Card className="p-5">
            <h2 className="mb-3 text-lg text-zinc-100">Preview</h2>
            <div className="grid gap-3">
              <PromotionCardPreview item={selectedPreview} />
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="mb-3 text-lg text-zinc-100">Targeting notes</h2>
            <ul className="space-y-2 text-sm text-ds-text-muted">
              <li>Audiences: `free_user`, `paid_user`, `enterprise_lead`</li>
              <li>Recent activity: `active_last_7d`, `inactive_14d`, `generated_last_30d`, `no_generation_30d`</li>
              <li>A/B variants support headline, body, CTA label, placement, and audience overrides.</li>
            </ul>
          </Card>
        </div>
      </section>

      <Card className="overflow-hidden p-0">
        <div className="border-b border-white/10 px-5 py-4">
          <h2 className="text-lg text-zinc-100">Promotion registry</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-white/5 text-ds-text-muted">
              <tr>
                <th className="px-4 py-3 font-medium">Promotion</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Placement</th>
                <th className="px-4 py-3 font-medium">CTR</th>
                <th className="px-4 py-3 font-medium">Dismiss</th>
                <th className="px-4 py-3 font-medium">Revenue</th>
                <th className="px-4 py-3 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {promotions.map((row) => (
                <tr key={row.id} className="border-t border-white/5 text-zinc-200">
                  <td className="px-4 py-3">
                    <div className="font-medium">{row.title}</div>
                    <div className="text-xs text-ds-text-muted">{row.slug}</div>
                  </td>
                  <td className="px-4 py-3">{row.promotionType}</td>
                  <td className="px-4 py-3">{row.status}</td>
                  <td className="px-4 py-3">{row.placements.join(", ")}</td>
                  <td className="px-4 py-3">{row.metrics.ctr}%</td>
                  <td className="px-4 py-3">{row.metrics.dismissRate}%</td>
                  <td className="px-4 py-3">{formatUsd(row.metrics.revenueGeneratedUsd)}</td>
                  <td className="px-4 py-3">
                    <Button variant="ghost" onClick={() => editPromotion(row)}>
                      Edit
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </AdminPageShell>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <label className="space-y-1 text-sm">
      <span className="text-ds-text-muted">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-zinc-100"
      />
    </label>
  );
}

function Area({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="space-y-1 text-sm">
      <span className="text-ds-text-muted">{label}</span>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={6}
        className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-2 font-mono text-sm text-zinc-100"
      />
    </label>
  );
}

function PromotionCardPreview({
  item,
}: {
  item: {
    promotion: Pick<
      PromotionAdminRow,
      "title" | "description" | "ctaLabel" | "sponsorLabel" | "badgeText"
    >;
    variant: null;
    placement: string;
    pagePath: string;
  };
}) {
  return (
    <Card variant="glass" className="rounded-3xl border border-white/10 p-5">
      <span className="inline-flex rounded-full border border-white/10 bg-white/10 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-zinc-100">
        {item.promotion.sponsorLabel || item.promotion.badgeText || "Preview"}
      </span>
      <h3 className="mt-3 text-lg font-semibold text-zinc-100">{item.promotion.title}</h3>
      <p className="mt-2 text-sm text-ds-text-muted">{item.promotion.description}</p>
      <div className="mt-4">
        <span className="inline-flex items-center rounded-xl border border-ds-accent-lavender/40 bg-ds-accent-lavender/10 px-4 py-2 text-sm font-medium text-zinc-100">
          {item.promotion.ctaLabel}
        </span>
      </div>
    </Card>
  );
}
