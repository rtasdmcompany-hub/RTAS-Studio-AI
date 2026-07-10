# Landing messaging guide

Keep the first viewport brand-first: product name, one headline, one supporting line, one CTA group, one dominant visual — no clutter.

## Sync sources

- `apps/web/src/lib/landing-copy.ts` — hero + audience + outcomes
- `apps/web/src/app/page.tsx` — landing composition
- `apps/web/src/components/marketing/PricingPlans.tsx` — plan names
- `docs/marketing/PRICING-STRATEGY.md` — Phase 2 pricing voice
- `@rtas/shared` — prices and credits constants

## Voice

- Premium, calm, international
- No hype spam or emoji clusters
- Prefer concrete outcomes (“credits”, “library”, “publish”)
- Never invent fake logos or fake customer counts

## Conversion path (Phase 1)

1. Hero → Start creating / View pricing
2. Trust badges
3. Outcomes (credits, identity lock, pipeline)
4. Audience fit
5. Workflow
6. Features
7. Pricing teaser → Compare plans
8. Final CTA → Studio / How-to-use

## Pre-launch copy checklist

- [x] Home hero matches current product name
- [x] Pricing matches shared constants
- [x] How-to-use steps match Studio wizard
- [x] Footer support links: Help, Feedback, email
- [x] Legal pages current
