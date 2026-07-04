import {
  PREMIUM_PRICE_USD,
  PRODUCT_NAME,
  STANDARD_PRICE_USD,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
} from "@rtas/shared";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import { PricingPlans } from "@/components/marketing/PricingPlans";
import {
  InnerPageContainer,
  InnerPageSection,
} from "@/components/marketing/InnerPageLayout";

export default function PricingPage() {
  return (
    <MarketingLayout>
      <InnerPageContainer>
        <InnerPageSection className="rtas-pricing-hero text-center">
          <p className="rtas-eyebrow">Global SaaS pricing</p>
          <h1 className="text-zinc-100">Studio conversion matrix</h1>
          <p className="rtas-pricing-hero__lead">
            {PRODUCT_NAME} uses transparent credit economics —{" "}
            <strong className="text-zinc-100">1 credit = 1 second</strong> of rendered
            video. Start with Creator Starter (${TESTER_PRICE_USD} pay-as-you-go), scale
            with Pro Studio Tier (${STANDARD_PRICE_USD}/mo), or deploy Production Enterprise
            (${PREMIUM_PRICE_USD}/mo) for 4K cinematic output.
          </p>
        </InnerPageSection>

        <InnerPageSection className="rtas-pricing-page">
          <PricingPlans />
        </InnerPageSection>

        <InnerPageSection className="rtas-pricing-faq">
          <h2 className="text-zinc-100">Which tier fits your workflow?</h2>
          <div className="rtas-faq-grid">
            <div>
              <h3>Creator Starter — ${TESTER_PRICE_USD}</h3>
              <p>
                Pay-as-you-go evaluation pass — ship one real clip end-to-end and validate
                the full pipeline before committing to a monthly tier ({TESTER_DURATION_DAYS}-day
                access window).
              </p>
            </div>
            <div>
              <h3>Pro Studio Tier — ${STANDARD_PRICE_USD}/mo</h3>
              <p>
                Monthly 1080p HD credits with clean exports, priority identity-lock queuing,
                and licensed commercial downloads — the global standard for active creators.
              </p>
            </div>
            <div>
              <h3>Production Enterprise — ${PREMIUM_PRICE_USD}/mo</h3>
              <p>
                Same monthly render capacity at cinematic 4K resolution, enterprise-grade
                identity continuity, and priority+ queuing for music videos, ads, and brand
                films.
              </p>
            </div>
          </div>
          <p className="rtas-pricing-legal">
            <a href="/terms">Terms of Service</a> · <a href="/privacy">Privacy Policy</a> ·{" "}
            <a href="/cookies">Cookies</a>
          </p>
        </InnerPageSection>
      </InnerPageContainer>
    </MarketingLayout>
  );
}
