import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { buildPageMetadata } from "@/lib/site-metadata";
import { CAMPAIGN_CHANNEL_LABEL, CAMPAIGN_PLANS } from "@/lib/launch/campaigns";

export const metadata: Metadata = buildPageMetadata({
  title: "Marketing Campaign Center",
  description: `Campaign plan structures for ${PRODUCT_NAME} across YouTube, LinkedIn, X, Meta, TikTok, Reddit, Product Hunt, and paid search — no fabricated metrics.`,
  path: "/launch/campaigns",
  openGraphTitle: `Campaign Center · ${PRODUCT_NAME}`,
});

const STATUS_LABEL: Record<string, string> = {
  done: "Done",
  in_progress: "In progress",
  planned: "Planned",
  blocked: "Blocked",
  not_started: "Not started",
};

export default function CampaignCenterPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Marketing</p>
          <h1 className="text-zinc-100">Campaign Center</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Channel plans for organic and paid acquisition. Metrics fields are structures only —
            live numbers stay zero / Ready for Integration until real analytics are connected.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/launch" variant="ghost">
              Launch Center
            </ButtonLink>
            <ButtonLink href="/launch/assets" variant="ghost">
              Assets
            </ButtonLink>
          </div>
        </InnerPageSection>

        <div className="grid gap-4 lg:grid-cols-2">
          {CAMPAIGN_PLANS.map((plan) => (
            <InnerPageSection key={plan.id} className="inner-page-section--panel text-left">
              <p className="text-xs uppercase tracking-wide text-ds-text-muted">
                {CAMPAIGN_CHANNEL_LABEL[plan.channel]} · {STATUS_LABEL[plan.status]}
              </p>
              <h2 className="mt-2 text-lg text-zinc-100">{plan.name}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{plan.objective}</p>
              <p className="mt-3 text-sm text-zinc-300">
                <span className="text-ds-text-muted">Audience:</span> {plan.audience}
              </p>
              <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-ds-text-muted">
                {plan.contentPillars.map((p) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-ds-text-muted">{plan.metricsNote}</p>
              <p className="mt-2 text-xs text-ds-text-muted">
                Owner: {plan.owner} · CTA: {plan.cta}
              </p>
              <p className="mt-2 text-xs text-ds-text-muted">
                Assets needed: {plan.assetsNeeded.join(" · ")}
              </p>
            </InnerPageSection>
          ))}
        </div>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
