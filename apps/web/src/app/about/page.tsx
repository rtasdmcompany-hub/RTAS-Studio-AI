import type { Metadata } from "next";
import { COMPANY_NAME, GROUP_NAME, PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "About",
  description: `About ${PRODUCT_NAME} — mission, vision, and the team behind the international AI video studio built by ${COMPANY_NAME}.`,
  path: "/about",
  openGraphTitle: `About · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Mission, vision, company story, and values for creators who need cinematic AI video with clear credits and commercial licensing.",
});

const TRUST = [
  {
    title: "Merchant of Record billing",
    body: "International checkout via Paddle (Merchant of Record) — tax, invoices, and compliance handled by Paddle so you can focus on shipping work.",
  },
  {
    title: "Identity-aware generation",
    body: "Real-face, avatar, and stylized modes with server-side credit guards so billing cannot be bypassed and likeness workflows stay intentional.",
  },
  {
    title: "Enterprise-ready operations",
    body: "Health and readiness probes, fail-closed webhooks, and documented deployment practices for teams launching globally.",
  },
] as const;

const VALUES = [
  {
    title: "Craft over hype",
    body: "We ship guided workflows, clear credit costs, and licensed masters — not vague “unlimited AI” promises.",
  },
  {
    title: "Honesty in billing",
    body: "Credits map to output seconds. Plans unlock resolution, queue priority, and commercial rights without hidden traps.",
  },
  {
    title: "Creator continuity",
    body: "Identity lock, style previews, and a library archive help artists and brands stay consistent across every render.",
  },
  {
    title: "International by default",
    body: `Built under ${GROUP_NAME} for creators and teams shipping music videos, ads, and stories across markets.`,
  },
] as const;

export default function AboutPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="rtas-about-page text-center">
          <p className="rtas-eyebrow">About</p>
          <h1 className="text-zinc-100">{PRODUCT_NAME}</h1>
          <p className="rtas-about-page__lead mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Built by {COMPANY_NAME} under {GROUP_NAME} — an international AI video
            studio for creators and teams who need cinematic output with clear credits,
            commercial licensing, and a premium product experience.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/studio" variant="lavender">
              Open Studio
            </ButtonLink>
            <ButtonLink href="/careers" variant="ghost">
              Careers
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section
          className="grid gap-4 md:grid-cols-2"
          aria-labelledby="about-mission-vision"
        >
          <h2 id="about-mission-vision" className="sr-only">
            Mission and vision
          </h2>
          <InnerPageSection>
            <p className="rtas-eyebrow">Mission</p>
            <h3 className="text-lg text-zinc-100">
              Make professional AI video production clear and shippable
            </h3>
            <p className="mt-2 text-sm text-ds-text-muted">
              We help creators and teams go from brief to publishable master in one
              workspace — with identity control, transparent credits, and commercial
              rights that match real production needs.
            </p>
          </InnerPageSection>
          <InnerPageSection>
            <p className="rtas-eyebrow">Vision</p>
            <h3 className="text-lg text-zinc-100">
              The default studio for international creative output
            </h3>
            <p className="mt-2 text-sm text-ds-text-muted">
              A single product surface where music videos, ads, and stories are composed,
              rendered, previewed, and archived — reliable enough for agencies, clear enough
              for independents.
            </p>
          </InnerPageSection>
        </section>

        <InnerPageSection>
          <p className="rtas-eyebrow">Company story</p>
          <h2 className="text-xl text-zinc-100">From marketing craft to AI studio</h2>
          <p className="mt-3 max-w-3xl text-sm text-ds-text-muted">
            {COMPANY_NAME} built {PRODUCT_NAME} as a proprietary software division under{" "}
            {GROUP_NAME}. The product grew from a practical need: creative teams were
            stitching together prompts, editors, and billing tools that did not speak to
            each other. We designed a guided studio — mode, category, style, face lock when
            required, credit cost before generate — then a cloud render pipeline and library
            so every master stays findable.
          </p>
          <p className="mt-3 max-w-3xl text-sm text-ds-text-muted">
            Today the platform serves international creators and production teams who want
            cinematic AI video without sacrificing licensing clarity or operational trust.
          </p>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-3" aria-label="Trust foundations">
          {TRUST.map((item) => (
            <InnerPageSection key={item.title}>
              <h2 className="text-lg text-zinc-100">{item.title}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
            </InnerPageSection>
          ))}
        </section>

        <section aria-labelledby="about-values">
          <InnerPageSection className="text-center pb-2">
            <h2 id="about-values" className="text-xl text-zinc-100">
              How we work
            </h2>
            <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
              Team values that show up in product decisions, support, and hiring.
            </p>
          </InnerPageSection>
          <div className="grid gap-4 md:grid-cols-2">
            {VALUES.map((item) => (
              <InnerPageSection key={item.title}>
                <h3 className="text-lg text-zinc-100">{item.title}</h3>
                <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              </InnerPageSection>
            ))}
          </div>
        </section>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-zinc-100">From first prompt to publish</h2>
          <p className="mx-auto mt-3 max-w-xl text-sm text-ds-text-muted">
            Compose in a guided wizard, render through a credit-guarded AI pipeline, then
            preview and archive every master in your library — one workspace, global ready.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/how-to-use" variant="primary">
              Product guide
            </ButtonLink>
            <ButtonLink href="/pricing" variant="ghost">
              View pricing
            </ButtonLink>
            <ButtonLink href="/help/contact" variant="ghost">
              Contact us
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
