import { COMPANY_NAME, GROUP_NAME, PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

const TRUST = [
  {
    title: "Merchant of Record billing",
    body: "International checkout via Paddle or Lemon Squeezy — tax, invoices, and compliance handled by the MoR.",
  },
  {
    title: "Identity-aware generation",
    body: "Real-face, avatar, and stylized modes with server-side credit guards so billing cannot be bypassed.",
  },
  {
    title: "Enterprise-ready ops",
    body: "Health and readiness probes, fail-closed webhooks, and documented deployment runbooks for global launch.",
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
            <ButtonLink href="/help" variant="ghost">
              Help Center
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section className="grid gap-4 md:grid-cols-3" aria-label="Why RTAS">
          {TRUST.map((item) => (
            <InnerPageSection key={item.title}>
              <h2 className="text-lg text-zinc-100">{item.title}</h2>
              <p className="mt-2 text-sm text-ds-text-muted">{item.body}</p>
            </InnerPageSection>
          ))}
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
          </div>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
