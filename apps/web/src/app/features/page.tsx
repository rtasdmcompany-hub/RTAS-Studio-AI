import type { Metadata } from "next";
import { PRODUCT_NAME } from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import { FeatureComparisonTable } from "@/components/marketing/FeatureComparisonTable";
import { TrustBadges } from "@/components/marketing/TrustBadges";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import { StructuredData } from "@/components/seo/StructuredData";
import {
  FEATURE_CAPABILITIES,
  FEATURES_HERO_EYEBROW,
  FEATURES_HERO_HEADLINE,
  FEATURES_HERO_SUPPORT,
  WORKFLOW_COMPARISON,
} from "@/lib/feature-comparison";
import { buildPageMetadata } from "@/lib/site-metadata";
import { breadcrumbSchema } from "@/lib/structured-data";

export const metadata: Metadata = buildPageMetadata({
  title: "Features",
  description: `Compare ${PRODUCT_NAME} capabilities across Tester, Standard, and Premium 4K — text-to-video, commercials, Identity Preservation, credits, and commercial downloads.`,
  path: "/features",
  openGraphTitle: `Features · ${PRODUCT_NAME}`,
  openGraphDescription:
    "Side-by-side plan comparison for compose, Identity Preservation, render, and publish.",
});

export default function FeaturesPage() {
  return (
    <MarketingLayout>
      <StructuredData
        data={breadcrumbSchema([
          { name: "Home", path: "/" },
          { name: "Features", path: "/features" },
        ])}
      />
      <InnerPageContainer>
        <InnerPageSection className="rtas-features-hero text-center">
          <p className="rtas-eyebrow">{FEATURES_HERO_EYEBROW}</p>
          <h1 className="text-white">{FEATURES_HERO_HEADLINE}</h1>
          <p className="rtas-features-hero__lead">{FEATURES_HERO_SUPPORT}</p>
          <TrustBadges className="rtas-pricing-trust" limit={4} compact />
          <div className="rtas-features-hero__actions">
            <ButtonLink href="/pricing#plans" variant="lavender">
              View pricing
            </ButtonLink>
            <ButtonLink href="/studio" variant="ghost">
              Open Studio
            </ButtonLink>
          </div>
        </InnerPageSection>

        <section className="rtas-features-caps" aria-labelledby="features-caps-title">
          <h2 id="features-caps-title" className="rtas-features-caps__title">
            Core capabilities
          </h2>
          <div className="rtas-features-caps__grid">
            {FEATURE_CAPABILITIES.map((cap) => (
              <article key={cap.id} className="rtas-features-caps__item">
                <h3>{cap.title}</h3>
                <p>{cap.body}</p>
              </article>
            ))}
          </div>
        </section>

        <InnerPageSection className="rtas-features-matrix-section" id="compare">
          <h2 className="text-white text-center">Plan comparison</h2>
          <p className="rtas-features-matrix-lead">
            Same studio for every plan. Resolution, watermark, queue priority, and commercial
            rights scale with your tier.
          </p>
          <FeatureComparisonTable />
        </InnerPageSection>

        <section className="rtas-features-workflow" aria-labelledby="features-workflow-title">
          <h2 id="features-workflow-title" className="rtas-features-workflow__title">
            One studio vs a fragmented stack
          </h2>
          <div className="rtas-features-workflow__grid">
            {WORKFLOW_COMPARISON.map((col) => (
              <article
                key={col.id}
                className={`rtas-features-workflow__col${
                  col.id === "rtas" ? " rtas-features-workflow__col--rtas" : ""
                }`}
              >
                <h3>{col.title}</h3>
                <ul>
                  {col.points.map((point) => (
                    <li key={point}>{point}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>

        <section className="rtas-features-final" aria-labelledby="features-final-title">
          <h2 id="features-final-title">Choose the tier that matches your output.</h2>
          <p>Standard is the default for weekly shipping. Premium 4K unlocks cinematic output.</p>
          <div className="rtas-features-final__actions">
            <ButtonLink href="/pricing#plans" variant="lavender">
              Compare pricing
            </ButtonLink>
            <ButtonLink href="/how-to-use" variant="ghost">
              60-second guide
            </ButtonLink>
          </div>
        </section>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
