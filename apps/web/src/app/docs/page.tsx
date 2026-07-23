import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { PromotionPlacement } from "@/components/promotions/PromotionPlacement";

import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "Documentation",
  description: `Official product documentation for ${PRODUCT_NAME} — getting started, studio workflow, credits, API overview, and glossary.`,
  path: "/docs",
  openGraphTitle: `Documentation · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Compose, render, and publish with clear credits — plus an overview of public health and share APIs.",
});

const GETTING_STARTED = [
  {
    step: "1",
    title: "Create an account",
    body: "Sign up with email or Google OAuth, verify your address when prompted, then open your Dashboard to see credits and library status.",
  },
  {
    step: "2",
    title: "Open Studio",
    body: "Choose mode, category, and visual style. Complete the guided wizard — prompt or image input, Identity Preservation when required, and a clear credit cost before you generate.",
  },
  {
    step: "3",
    title: "Render and preview",
    body: "Jobs run through a credit-guarded cloud pipeline. Track progress, then preview full-screen. New accounts start at 0 credits — Tester or a subscription unlocks generation.",
  },
  {
    step: "4",
    title: "Download or share",
    body: "Paid plans unlock licensed masters. Publish public share links for client review, and keep every job archived in your library.",
  },
] as const;

const SECTIONS = [
  {
    title: "Studio workflow",
    body: "Choose mode, category, and visual style, then complete the guided wizard. Prompt or image input, Identity Preservation when required, and clear credit cost before you generate.",
    href: "/how-to-use",
    cta: "Open How to use",
  },
  {
    title: "Identity Preservation",
    body: "Identity Preservation needs a clear identity reference photo and Identity consent. Avatar and Cartoon keep continuity without a live likeness lock. Use Style step previews to pick the right look.",
    href: "/studio",
    cta: "Open Studio",
  },
  {
    title: "Credits & billing",
    body: "1 credit ≈ 1 second of output. Plans unlock higher resolution, queue priority, and commercial downloads. Watermarked previews stay available for evaluation.",
    href: "/help/billing",
    cta: "Billing guide",
  },
  {
    title: "Preview & publish",
    body: "After render, preview full-screen, download licensed masters on paid tiers, share publicly, and keep every job in your library dashboard.",
    href: "/profile",
    cta: "Open dashboard",
  },
] as const;

const API_OVERVIEW = [
  {
    method: "GET",
    path: "/api/health",
    body: "Liveness probe — confirms the web process is up. Suitable for uptime monitors and load balancers. No dependency checks.",
  },
  {
    method: "GET",
    path: "/api/ready",
    body: "Readiness probe — reports whether required production dependencies are configured. Public response is minimal; use for deploy gates.",
  },
  {
    method: "GET",
    path: "/api/share/[videoId]",
    body: "Public read of a published share payload. No session required. Returns 404 when the video is not publicly shared.",
  },
  {
    method: "POST",
    path: "/api/share/[videoId]",
    body: "Authenticated publish — marks a generation job public for social and client review. Session required; rate limited per user and IP.",
  },
] as const;

const GLOSSARY = [
  {
    term: "Credit",
    definition:
      "Billing unit for generation. Approximately one credit equals one second of finished video output.",
  },
  {
    term: "Identity Preservation",
    definition:
      "Authorized Identity Consistency workflow that preserves a likeness or character continuity (avatar/cartoon) across a render.",
  },
  {
    term: "Master",
    definition:
      "Downloadable, licensed output on paid tiers — distinct from watermarked evaluation previews.",
  },
  {
    term: "Merchant of Record (MoR)",
    definition:
      "Checkout partner (Paddle or Lemon Squeezy) that handles tax, invoices, and payment compliance.",
  },
  {
    term: "BFF",
    definition:
      "Backend-for-frontend API routes under /api/* that the web app uses for auth, generation, billing, and share.",
  },
  {
    term: "Share link",
    definition:
      "Public page and API surface for a published video, used for social posts and client review.",
  },
] as const;

export default function DocsPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Documentation</p>
          <h1 className="text-white">Product documentation</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Everything you need to compose, render, and publish with {PRODUCT_NAME} —
            written for creators and teams shipping internationally.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/how-to-use" variant="lavender">
              Studio guide
            </ButtonLink>
            <ButtonLink href="/developers" variant="ghost">
              Developer docs
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section aria-labelledby="docs-getting-started">
          <InnerPageSection className="text-center pb-2">
            <h2 id="docs-getting-started" className="text-xl text-white">
              Getting started
            </h2>
            <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
              Four steps from account to a shareable or downloadable master.
            </p>
          </InnerPageSection>
          <div className="grid gap-4 md:grid-cols-2">
            {GETTING_STARTED.map((item) => (
              <InnerPageSection key={item.step}>
                <p className="rtas-eyebrow">Step {item.step}</p>
                <h3 className="text-lg text-white">{item.title}</h3>
                <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              </InnerPageSection>
            ))}
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-2" aria-label="Documentation topics">
          {SECTIONS.map((item) => (
            <InnerPageSection key={item.title}>
              <h2 className="text-lg text-white">{item.title}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              <div className="mt-4">
                <ButtonLink href={item.href} variant="ghost">
                  {item.cta} →
                </ButtonLink>
              </div>
            </InnerPageSection>
          ))}
        </section>

        <PromotionPlacement
          placement="docs_partner_recommendations"
          pagePath="/docs"
          title="Recommended resources"
          emptyMinHeightClassName="min-h-[14rem]"
        />

        <section aria-labelledby="docs-api-overview">
          <InnerPageSection className="pb-2">
            <h2 id="docs-api-overview" className="text-xl text-white">
              API overview
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-ds-text-muted">
              Public and share-oriented routes exposed by the web BFF. Generation,
              checkout, and account APIs require an authenticated session and are not
              published as a general third-party SDK. See Developers for auth and rate-limit
              notes.
            </p>
          </InnerPageSection>
          <div className="grid gap-4">
            {API_OVERVIEW.map((item) => (
              <InnerPageSection key={`${item.method}-${item.path}`}>
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <code className="text-xs font-semibold text-ds-accent-lavender">
                    {item.method}
                  </code>
                  <code className="text-sm text-zinc-100">{item.path}</code>
                </div>
                <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
              </InnerPageSection>
            ))}
          </div>
          <div className="mt-4 flex flex-wrap gap-3 px-4 md:px-6">
            <ButtonLink href="/developers" variant="ghost">
              Full developer notes →
            </ButtonLink>
            <ButtonLink href="/status" variant="ghost">
              System status →
            </ButtonLink>
          </div>
        </section>

        <section aria-labelledby="docs-glossary">
          <InnerPageSection className="text-center pb-2">
            <h2 id="docs-glossary" className="text-xl text-white">
              Glossary
            </h2>
          </InnerPageSection>
          <div className="grid gap-4 md:grid-cols-2">
            {GLOSSARY.map((item) => (
              <InnerPageSection key={item.term}>
                <h3 className="text-lg text-white">{item.term}</h3>
                <p className="mt-2 text-sm text-ds-text-muted">{item.definition}</p>
              </InnerPageSection>
            ))}
          </div>
        </section>

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-white">Need a quick answer?</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
            Open Studio when you are ready to create, or use How to use for a guided walkthrough.
            FAQ and contact live in Help Center.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/studio" variant="lavender">
              Open Studio
            </ButtonLink>
            <ButtonLink href="/how-to-use" variant="ghost">
              How to use
            </ButtonLink>
            <ButtonLink href="/help" variant="ghost">
              Help Center
            </ButtonLink>
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
