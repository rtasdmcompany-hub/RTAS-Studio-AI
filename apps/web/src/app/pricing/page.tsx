import type { Metadata } from "next";
import {
  PREMIUM_PRICE_USD,
  PRODUCT_NAME,
  STANDARD_PRICE_USD,
  TESTER_PRICE_USD,
} from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import { PricingPlans } from "@/components/marketing/PricingPlans";
import { TrustBadges } from "@/components/marketing/TrustBadges";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";
import {
  PRICING_AUDIENCE_GUIDE,
  PRICING_FAQ,
  PRICING_FINAL_CTA_BODY,
  PRICING_FINAL_CTA_TITLE,
  PRICING_HERO_EYEBROW,
  PRICING_HERO_HEADLINE,
  PRICING_HERO_SUPPORT,
  PRICING_VALUE_POINTS,
} from "@/lib/pricing-copy";

export const metadata: Metadata = {
  title: "Pricing",
  description: `${PRODUCT_NAME} pricing: Creator Starter $${TESTER_PRICE_USD}, Pro Studio $${STANDARD_PRICE_USD}/mo, Production Enterprise $${PREMIUM_PRICE_USD}/mo. 1 credit = 1 second. Global merchant-of-record checkout.`,
  openGraph: {
    title: `Pricing · ${PRODUCT_NAME}`,
    description: `Transparent credit pricing from $${TESTER_PRICE_USD}. Pro $${STANDARD_PRICE_USD}/mo · Enterprise $${PREMIUM_PRICE_USD}/mo.`,
  },
};

export default function PricingPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="rtas-pricing-hero rtas-pricing-hero--conversion text-center">
          <p className="rtas-eyebrow">{PRICING_HERO_EYEBROW}</p>
          <h1 className="text-white">{PRICING_HERO_HEADLINE}</h1>
          <p className="rtas-pricing-hero__lead rtas-pricing-hero__lead--conversion">
            {PRICING_HERO_SUPPORT}
          </p>
          <TrustBadges className="rtas-pricing-trust" limit={4} compact />
        </InnerPageSection>

        <section className="rtas-pricing-value" aria-label="Why these plans">
          {PRICING_VALUE_POINTS.map((point) => (
            <article key={point.id} className="rtas-pricing-value__item">
              <h3>{point.title}</h3>
              <p>{point.body}</p>
            </article>
          ))}
        </section>

        <section className="rtas-pricing-guide" aria-labelledby="pricing-guide-title">
          <h2 id="pricing-guide-title" className="rtas-pricing-guide__title">
            Which plan fits you?
          </h2>
          <div className="rtas-pricing-guide__grid">
            {PRICING_AUDIENCE_GUIDE.map((item) => (
              <article key={item.id} className="rtas-pricing-guide__card">
                <p className="rtas-pricing-guide__hint">{item.planHint}</p>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </article>
            ))}
          </div>
        </section>

        <InnerPageSection className="rtas-pricing-plans-section">
          <PricingPlans />
        </InnerPageSection>

        <InnerPageSection className="rtas-pricing-faq rtas-pricing-faq--conversion">
          <h2 className="text-white">Pricing FAQ</h2>
          <div className="rtas-pricing-faq__grid">
            {PRICING_FAQ.map((item) => (
              <article key={item.id} className="rtas-pricing-faq__item">
                <h3>{item.question}</h3>
                <p>{item.answer}</p>
              </article>
            ))}
          </div>
          <p className="rtas-pricing-legal">
            <a href="/help/billing">Billing help</a> · <a href="/terms">Terms</a> ·{" "}
            <a href="/privacy">Privacy</a> · <a href="/cookies">Cookies</a>
          </p>
        </InnerPageSection>

        <section className="rtas-pricing-final" aria-labelledby="pricing-final-title">
          <h2 id="pricing-final-title">{PRICING_FINAL_CTA_TITLE}</h2>
          <p>{PRICING_FINAL_CTA_BODY}</p>
          <div className="rtas-pricing-final__actions">
            <ButtonLink href="#plans" variant="lavender">
              Choose a plan
            </ButtonLink>
            <ButtonLink href="/studio" variant="ghost">
              Open Studio
            </ButtonLink>
          </div>
        </section>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
