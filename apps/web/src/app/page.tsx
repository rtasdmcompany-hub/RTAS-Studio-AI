import {
  PREMIUM_PRICE_USD,
  PRODUCT_NAME,
  STANDARD_PRICE_USD,
  TESTER_PRICE_USD,
} from "@rtas/shared";
import { ButtonLink } from "@rtas/ui";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import { LandingCategoryShowcase } from "@/components/marketing/LandingCategoryShowcase";
import { ShowcaseVideos } from "@/components/marketing/ShowcaseVideos";
import { TrustBadges } from "@/components/marketing/TrustBadges";
import {
  LANDING_AUDIENCES,
  LANDING_BRAND,
  LANDING_HERO_HEADLINE,
  LANDING_HERO_SUPPORT,
  LANDING_OUTCOMES,
} from "@/lib/landing-copy";

const WORKFLOW_STEPS = [
  {
    id: "compose",
    step: "01",
    title: "Compose",
    body: "Choose mode and category, add lyrics, audio, and Identity Preservation — only the fields you need.",
  },
  {
    id: "render",
    step: "02",
    title: "Render",
    body: "Cloud GPU pipeline with live progress, clear credit cost, and identity continuity.",
  },
  {
    id: "publish",
    step: "03",
    title: "Publish",
    body: "Preview full-screen, download your master, share publicly, and keep every render in your library.",
  },
] as const;

const VALUE_GRID = [
  {
    title: "Every style. One studio.",
    body: "Song videos, faith content, business ads, cartoons, and stories — pick a category and the wizard adapts.",
  },
  {
    title: "Music-first pipeline.",
    body: "Upload audio, sync lyrics, and direct cinematic motion built for musicians and storytellers.",
  },
  {
    title: "Identity Preservation.",
    body: "Authorized Identity Consistency keeps likeness consistent across shots — a core RTAS advantage.",
  },
  {
    title: "Credits you can explain.",
    body: "1 credit = 1 second. Transparent pricing with merchant-of-record checkout worldwide.",
  },
] as const;

export default function HomePage() {
  return (
    <MarketingLayout>
      <ShowcaseVideos />

      <section id="categories" className="rtas-hero-showcase" aria-label="Hero">
        <div className="rtas-hero-showcase__videos">
          <LandingCategoryShowcase variant="hero" />
        </div>
        <div className="rtas-hero-showcase__content video-text-highlight">
          <p className="rtas-hero-showcase__brand">{LANDING_BRAND}</p>
          <div className="rtas-hero-showcase__headline">
            <h1>{LANDING_HERO_HEADLINE}</h1>
          </div>
          <p className="rtas-hero-showcase__tagline">{LANDING_HERO_SUPPORT}</p>
          <div className="rtas-hero-showcase__cta-group">
            <ButtonLink href="/studio" variant="lavender-lg">
              Start creating <span aria-hidden>→</span>
            </ButtonLink>
            <ButtonLink href="/pricing" variant="ghost">
              View pricing
            </ButtonLink>
          </div>
        </div>
      </section>

      <section className="rtas-trusted video-content-panel" aria-label="Trust">
        <p className="rtas-trusted__eyebrow">Built for international creators</p>
        <TrustBadges limit={5} />
      </section>

      <section
        id="outcomes"
        className="rtas-landing-outcomes video-content-panel"
        aria-label="Product outcomes"
      >
        <h2 className="rtas-landing-outcomes__title">Why teams choose {PRODUCT_NAME}</h2>
        <ul className="rtas-landing-outcomes__grid">
          {LANDING_OUTCOMES.map((item) => (
            <li key={item.id} className="rtas-landing-outcome">
              <p className="rtas-landing-outcome__label">{item.label}</p>
              <p className="rtas-landing-outcome__detail">{item.detail}</p>
            </li>
          ))}
        </ul>
      </section>

      <section
        id="audience"
        className="rtas-landing-audience video-content-panel"
        aria-label="Who it is for"
      >
        <h2>Built for people who ship video</h2>
        <p className="rtas-landing-audience__lead">
          One product surface for artists, brands, and studios — not a pile of disconnected AI tools.
        </p>
        <div className="rtas-landing-audience__grid">
          {LANDING_AUDIENCES.map((audience) => (
            <article key={audience.id} className="rtas-landing-audience__card">
              <h3>{audience.title}</h3>
              <p>{audience.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="workflow" className="rtas-workflow video-content-panel">
        <h2>One studio. Three beats.</h2>
        <p className="rtas-workflow__lead">
          From first lyric to final export — compose, render, and publish stay in a single
          cinematic workspace.
        </p>
        <div className="rtas-workflow__pipeline">
          {WORKFLOW_STEPS.map((step) => (
            <article key={step.id} className="rtas-pipeline-step">
              <span className="rtas-pipeline-step__num">{step.step}</span>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
            </article>
          ))}
        </div>
        <ButtonLink href="/studio" variant="lavender" className="rtas-workflow__cta">
          Open Studio <span aria-hidden>→</span>
        </ButtonLink>
      </section>

      <section id="features" className="rtas-value video-content-panel">
        <h2>No handoffs. No exports. No starting over.</h2>
        <div className="rtas-value__grid">
          {VALUE_GRID.map((card) => (
            <article key={card.title} className="rtas-value__card">
              <h3>{card.title}</h3>
              <p>{card.body}</p>
            </article>
          ))}
        </div>
        <div className="rtas-value__cta-row">
          <ButtonLink href="/features" variant="ghost">
            Full feature comparison <span aria-hidden>→</span>
          </ButtonLink>
        </div>
      </section>

      <section
        id="pricing-teaser"
        className="rtas-landing-pricing video-content-panel"
        aria-label="Pricing overview"
      >
        <h2>Simple plans. Global checkout.</h2>
        <p className="rtas-landing-pricing__lead">
          Start with Tester, then scale to Standard or Premium 4K.
          Credits stay transparent: <strong>1 credit = 1 second</strong>.
        </p>
        <div className="rtas-landing-pricing__tiers">
          <article className="rtas-landing-pricing__tier">
            <h3>Tester</h3>
            <p className="rtas-landing-pricing__price">${TESTER_PRICE_USD}</p>
            <p>One-time evaluation · also called Creator Starter</p>
          </article>
          <article className="rtas-landing-pricing__tier rtas-landing-pricing__tier--featured">
            <p className="rtas-landing-pricing__badge">Most popular</p>
            <h3>Standard</h3>
            <p className="rtas-landing-pricing__price">${STANDARD_PRICE_USD}/mo</p>
            <p>Monthly HD credits + commercial downloads · also called Pro Studio</p>
          </article>
          <article className="rtas-landing-pricing__tier">
            <h3>Premium 4K</h3>
            <p className="rtas-landing-pricing__price">${PREMIUM_PRICE_USD}/mo</p>
            <p>Cinematic 4K for brand and music work · also called Production Enterprise</p>
          </article>
        </div>
        <ButtonLink href="/pricing" variant="lavender" className="rtas-landing-pricing__cta">
          Compare plans <span aria-hidden>→</span>
        </ButtonLink>
      </section>

      <section className="rtas-final-cta video-content-panel">
        <h2>Ship your next video today.</h2>
        <p>
          {PRODUCT_NAME} — compose, render, and publish at international music-video standards.
        </p>
        <div className="rtas-final-cta__row">
          <ButtonLink href="/studio" variant="lavender">
            Start creating
          </ButtonLink>
          <ButtonLink href="/enterprise" variant="ghost">
            Enterprise
          </ButtonLink>
          <ButtonLink href="/showcase" variant="ghost">
            Watch showcase
          </ButtonLink>
        </div>
        <p className="rtas-final-cta__note">
          From ${TESTER_PRICE_USD} Tester · ${STANDARD_PRICE_USD}/mo Standard · ${PREMIUM_PRICE_USD}/mo
          Premium 4K
        </p>
      </section>
    </MarketingLayout>
  );
}
