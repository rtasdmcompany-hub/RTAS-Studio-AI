# Promotion Analytics

## Metrics
The Revenue Promotion Engine tracks first-party promotion outcomes:
- Views
- Clicks
- CTR
- Dismisses
- Dismiss Rate
- Conversions
- Revenue Generated

## Event Model
Events are stored in `RevenuePromotionInteraction` with:
- `promotionId`
- `variantId`
- `action`
- `placement`
- `pagePath`
- `userId` or `sessionId`
- `country`
- `language`
- `revenueAmountCents`

## A/B Testing
Variants are stored as JSON per promotion. Current structure supports testing:
- Headline
- Body copy
- CTA label
- Placement override
- Audience override
- Image URL

Variant selection is deterministic by promotion + user/session + placement so a viewer sees stable messaging within a session.

## Attribution
- Clicks are recorded on CTA interaction
- Dismisses are recorded when the user hides a placement
- Conversions are recorded when provider success returns with promotion metadata
- Revenue generated is recorded from conversion payloads

## Reporting Surface
`/admin/promotions` shows:
- aggregate summary
- per-promotion CTR
- dismiss rate
- revenue generated

## Known Limits
- Revenue attribution currently depends on promotion-aware checkout flows
- Non-checkout business outcomes such as enterprise form submission can be added as future conversion sources
