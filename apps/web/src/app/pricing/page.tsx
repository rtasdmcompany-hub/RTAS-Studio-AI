import {
  PRODUCT_NAME,
  TESTER_DURATION_DAYS,
  TESTER_PRICE_USD,
} from "@rtas/shared";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import { PricingPlans } from "@/components/marketing/PricingPlans";

export default function PricingPage() {
  return (
    <MarketingLayout>
      <div className="rtas-pricing-page">
        <section className="rtas-pricing-hero video-content-panel">
          <p className="rtas-eyebrow">Transparent credits</p>
          <h1>Recharge &amp; plans</h1>
          <p className="rtas-pricing-hero__lead">
            {PRODUCT_NAME} uses simple video length — <strong>1 credit = 1 second</strong>.
            Pick Tester (${TESTER_PRICE_USD} / {TESTER_DURATION_DAYS} days) to try the full
            studio, Standard ($89/mo) for regular HD content, or Premium 4K ($249/mo) for
            cinema-grade output.
          </p>
        </section>

        <PricingPlans />

        <section className="rtas-pricing-faq video-content-panel">
          <h2>What&apos;s the difference?</h2>
          <div className="rtas-faq-grid">
            <div>
              <h3>Tester ($5 / 5 days)</h3>
              <p>
                A short trial pass — enough to build one real clip end-to-end and see the
                workflow before you subscribe.
              </p>
            </div>
            <div>
              <h3>Standard ($89 / month)</h3>
              <p>
                Monthly HD credits for social, ads and brand videos — commercial rights included.
                The sweet spot for active creators.
              </p>
            </div>
            <div>
              <h3>Premium 4K ($249 / month)</h3>
              <p>
                Same monthly time as Standard, but with cinematic 4K quality, stronger
                identity-lock, and the richest scenes for music videos and films.
              </p>
            </div>
          </div>
          <p className="rtas-pricing-legal">
            <a href="/terms">Terms of Service</a> · <a href="/privacy">Privacy Policy</a> ·{" "}
            <a href="/cookies">Cookies</a>
          </p>
        </section>
      </div>
    </MarketingLayout>
  );
}
