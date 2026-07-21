import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import {
  AiShowcaseGrid,
  AiShowcaseHero,
} from "@/components/marketing/AiShowcase";
import { TrustBadges } from "@/components/marketing/TrustBadges";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import {
  AI_SHOWCASE_HERO_EYEBROW,
  AI_SHOWCASE_HERO_HEADLINE,
  AI_SHOWCASE_HERO_SUPPORT,
  AI_SHOWCASE_ITEMS,
  AI_SHOWCASE_PROOF_POINTS,
} from "@/lib/ai-showcase";

import { buildPageMetadata } from "@/lib/site-metadata";

export const metadata: Metadata = buildPageMetadata({
  title: "AI Showcase",
  description: `Watch ${PRODUCT_NAME} category previews — rap, solo, commercial, cartoon, and faith-forward cinema with Identity Preservation output.`,
  path: "/showcase",
  openGraphTitle: `AI Showcase · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Identity Preservation AI video across music, brand, stylized, and cultural categories.",
});

export default function ShowcasePage() {
  const heroItem = AI_SHOWCASE_ITEMS[0];

  return (
    <MarketingLayout>
      <div className="rtas-ai-showcase-bleed">
        <AiShowcaseHero item={heroItem} />
        <div className="rtas-ai-showcase-bleed__content">
          <p className="rtas-eyebrow">{AI_SHOWCASE_HERO_EYEBROW}</p>
          <h1>{AI_SHOWCASE_HERO_HEADLINE}</h1>
          <p className="rtas-ai-showcase-bleed__lead">{AI_SHOWCASE_HERO_SUPPORT}</p>
          <div className="rtas-ai-showcase-bleed__actions">
            <ButtonLink href="/studio" variant="lavender">
              Create in Studio
            </ButtonLink>
            <ButtonLink href="/pricing" variant="ghost">
              View pricing
            </ButtonLink>
          </div>
        </div>
      </div>

      <InnerPageContainer>
        <InnerPageSection className="rtas-ai-showcase-trust text-center">
          <TrustBadges limit={4} compact />
        </InnerPageSection>

        <section className="rtas-ai-showcase-proof" aria-labelledby="showcase-proof-title">
          <h2 id="showcase-proof-title" className="rtas-ai-showcase-proof__title">
            What the showcase proves
          </h2>
          <div className="rtas-ai-showcase-proof__grid">
            {AI_SHOWCASE_PROOF_POINTS.map((point) => (
              <article key={point.id}>
                <h3>{point.title}</h3>
                <p>{point.body}</p>
              </article>
            ))}
          </div>
        </section>

        <InnerPageSection id="gallery" className="rtas-ai-showcase-section">
          <h2 className="text-white text-center">Category gallery</h2>
          <p className="rtas-ai-showcase-section__lead">
            Five production styles. Same studio. Mute loops for fast preview — open Studio to
            render your own masters.
          </p>
          <AiShowcaseGrid items={AI_SHOWCASE_ITEMS} />
        </InnerPageSection>

        <section className="rtas-ai-showcase-final" aria-labelledby="showcase-final-title">
          <h2 id="showcase-final-title">Your next clip can look like this.</h2>
          <p>
            Start with Creator Starter to evaluate the pipeline, or go Pro when you are ready to
            ship clean commercial masters.
          </p>
          <div className="rtas-ai-showcase-final__actions">
            <ButtonLink href="/studio" variant="lavender">
              Open Studio
            </ButtonLink>
            <ButtonLink href="/features" variant="ghost">
              Compare features
            </ButtonLink>
          </div>
        </section>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
