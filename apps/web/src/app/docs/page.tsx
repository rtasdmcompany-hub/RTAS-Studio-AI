import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

export const metadata: Metadata = {
  title: "Documentation",
  description: `Official product documentation for ${PRODUCT_NAME} — studio workflow, identity lock, credits, and publishing.`,
};

const SECTIONS = [
  {
    title: "Studio workflow",
    body: "Choose mode, category, and visual style, then complete the guided wizard. Prompt or image input, face lock when required, and clear credit cost before you generate.",
    href: "/how-to-use",
    cta: "Open How to use",
  },
  {
    title: "Identity lock",
    body: "Real face mode needs a clear reference photo and consent. Avatar and Cartoon keep continuity without a live likeness lock. Use Style step previews to pick the right look.",
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

export default function DocsPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="text-center">
          <p className="rtas-eyebrow">Documentation</p>
          <h1 className="text-white">Product documentation</h1>
          <p className="mx-auto mt-3 max-w-2xl text-ds-text-muted">
            Everything you need to compose, render, and publish with {PRODUCT_NAME} — written for
            creators and teams shipping internationally.
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

        <InnerPageSection className="text-center">
          <h2 className="text-xl text-white">Need a quick answer?</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-ds-text-muted">
            FAQ, troubleshooting, and contact live in Help Center. Status and API notes are under
            Developers.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/help/faq" variant="lavender">
              FAQ
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
