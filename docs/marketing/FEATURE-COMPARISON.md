# Feature comparison (Phase 3)

Public capability matrix for buyers evaluating RTAS Studio AI plans.

## Sync sources

- `apps/web/src/lib/feature-comparison.ts` — capabilities, matrix rows, workflow contrast
- `apps/web/src/components/marketing/FeatureComparisonTable.tsx` — table UI
- `apps/web/src/app/features/page.tsx` — page + SEO
- `apps/web/src/lib/pricing-tiers.ts` — must stay consistent with matrix claims

## Rules

- Do not invent competitor brand names or fake benchmark scores.
- Contrast against a generic “multi-tool stack,” not named rivals.
- Resolution / watermark / commercial claims must match pricing tiers and help/billing.
- Nav “Features” points to `/features` (not only `/#features`).

## Conversion path

1. Hero → Pricing / Studio
2. Core capabilities
3. Plan comparison table (`#compare`)
4. One studio vs fragmented stack
5. Final CTA → pricing / how-to-use
