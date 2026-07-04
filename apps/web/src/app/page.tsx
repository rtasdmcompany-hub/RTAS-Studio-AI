import Link from "next/link";
import {
  PREMIUM_PRICE_USD,
  PRODUCT_NAME,
  STANDARD_PRICE_USD,
  TESTER_PRICE_USD,
} from "@rtas/shared";
import { MarketingLayout } from "@/components/marketing/MarketingLayout";
import { LandingCategoryShowcase } from "@/components/marketing/LandingCategoryShowcase";
import { ShowcaseVideos } from "@/components/marketing/ShowcaseVideos";
import {
  SHOWCASE_HERO_HEADLINE,
  SHOWCASE_HERO_TAGLINE,
} from "@/lib/preview-showcase";

const TRUST_LABELS = [
  "Creators",
  "Musicians",
  "Brands",
  "Agencies",
  "Filmmakers",
  "Marketers",
] as const;

const WORKFLOW_STEPS = [
  {
    id: "compose",
    step: "01",
    title: "Compose",
    body: "Pick category, drop lyrics, audio, and face lock — one guided wizard, zero clutter.",
  },
  {
    id: "render",
    step: "02",
    title: "Render",
    body: "Cinematic AI pipeline with identity-locked faces, clear credit cost, and live progress.",
  },
  {
    id: "publish",
    step: "03",
    title: "Publish",
    body: "Preview full-screen, download your master, and revisit every render in your library.",
  },
] as const;

const VALUE_GRID = [
  {
    title: "Every style. One studio.",
    body: "Song videos, religious and faith-based content, business ads, cartoons, and stories — pick a category and only the inputs you need appear.",
  },
  {
    title: "Music-first pipeline.",
    body: "Upload audio, sync lyrics, and direct emotional cinematic motion — built for musicians and storytellers.",
  },
  {
    title: "100% face lock.",
    body: "Real-face mode with identity shield keeps your likeness consistent shot after shot — a core RTAS advantage.",
  },
  {
    title: "Credits you can trust.",
    body: "1 credit = 1 second. Transparent pricing with secure Paddle / Lemon Squeezy checkout worldwide.",
  },
] as const;

export default function HomePage() {
  return (
    <MarketingLayout>
      {/* Landing-only cinematic backdrop — deferred, code-split, never blocks first paint */}
      <ShowcaseVideos />
      {/* Hero — 5 category videos (100% visible) + headline overlay */}
      <section id="categories" className="rtas-hero-showcase">
        <div className="rtas-hero-showcase__videos">
          <LandingCategoryShowcase variant="hero" />
        </div>
        <div className="rtas-hero-showcase__content video-text-highlight">
          <div className="rtas-hero-showcase__headline">
            <h1>{SHOWCASE_HERO_HEADLINE}</h1>
          </div>
          <p className="rtas-hero-showcase__tagline">
            <strong>{PRODUCT_NAME}</strong> — {SHOWCASE_HERO_TAGLINE}
          </p>
          <Link href="/studio" className="rtas-btn-lavender rtas-btn-lavender--lg">
            Start creating <span aria-hidden>→</span>
          </Link>
        </div>
      </section>

      <section className="rtas-trusted video-content-panel">
        <p>Trusted by creative teams at</p>
        <ul>
          {TRUST_LABELS.map((label) => (
            <li key={label}>{label}</li>
          ))}
        </ul>
      </section>

      <section id="workflow" className="rtas-workflow video-content-panel">
        <h2>One studio. Three beats.</h2>
        <p className="rtas-workflow__lead">
          From first lyric to final export — {PRODUCT_NAME} keeps compose, render,
          and publish in a single cinematic workspace built for global creators.
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
        <Link href="/studio" className="rtas-btn-lavender rtas-workflow__cta">
          Open Studio <span aria-hidden>→</span>
        </Link>
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
      </section>

      <section className="rtas-final-cta video-content-panel">
        <h2>Make videos worth watching.</h2>
        <p>Compose · Render · Publish — built for international music-video standards.</p>
        <div className="rtas-final-cta__row">
          <Link href="/studio" className="rtas-btn-lavender">
            Get started
          </Link>
          <Link href="/pricing" className="rtas-btn-ghost">
            View pricing
          </Link>
        </div>
        <p className="rtas-final-cta__note">
          Tester ${TESTER_PRICE_USD} · Standard ${STANDARD_PRICE_USD}/mo · Premium ${PREMIUM_PRICE_USD}/mo
        </p>
      </section>
    </MarketingLayout>
  );
}
