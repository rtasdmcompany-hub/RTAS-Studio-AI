# Pricing strategy (Phase 2)

Commercial source of truth for public pricing messaging. Plan economics live in `@rtas/shared` (`credits.ts`) — do not invent prices here.

## Sync sources

- `apps/web/src/lib/pricing-copy.ts` — hero, value points, audience guide, FAQ
- `apps/web/src/lib/pricing-tiers.ts` — tier cards + feature matrix
- `apps/web/src/app/pricing/page.tsx` — page composition + SEO metadata
- `packages/shared/src/credits.ts` — prices and credit pools

## Current public matrix

| Plan | Price | Credits | Resolution | Commercial |
|------|------:|--------:|------------|------------|
| Creator Starter | $5 one-time | 30s · 5-day | 720p eval | Preview only |
| Pro Studio | $89/mo | 2000s (~33 min) | 1080p | Yes |
| Production Enterprise | $249/mo | 2000s (~33 min) | 4K | Yes |

## Positioning

1. **Starter** — remove risk; prove the pipeline before subscription.
2. **Pro** — default revenue plan; most popular; weekly shipping.
3. **Enterprise** — quality upgrade (4K + priority+), same credit pool.

## Conversion path

1. Hero (outcome + credit clarity)
2. Trust badges
3. Value strip (credits / MoR / commercial)
4. Audience guide → scroll to plans
5. Tier cards + checkout CTAs
6. Objection FAQ
7. Final CTA → plans / Studio

## Rules

- Never invent fake discounts, annual plans, or customer counts.
- Keep 1 credit = 1 second as the primary economic message.
- Link billing detail to `/help/billing`.
