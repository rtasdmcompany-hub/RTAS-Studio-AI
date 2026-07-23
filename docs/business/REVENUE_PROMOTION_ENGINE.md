# Revenue Promotion Engine

## Purpose
RTAS Studio AI Phase 13 Business Enhancement introduces a centralized Revenue Promotion Engine (RPE) for premium internal promotions, approved partner-ready placements, and educational recommendations.

The engine is intentionally not ad-tech:
- No Google AdSense
- No banner-ad clutter
- No popups
- No autoplay or intrusive media
- No third-party tracking scripts
- No low-quality or off-brand promotions

## Core Architecture
- Storage: Prisma-backed `RevenuePromotion` and `RevenuePromotionInteraction`
- Matching: server-side targeting by page, placement, audience, plan, credits, country, language, and recent activity
- Rendering: premium card/announcement placement component
- Admin: `/admin/promotions`
- Analytics: views, clicks, CTR, dismiss rate, conversions, revenue generated
- Experimentation: JSON-backed A/B variants per promotion

## Promotion Types
- Internal: plan upgrades, credits, enterprise, white label, new features
- Partner: approved partner-ready placements labeled with sponsor context
- Educational: docs, tutorials, learning center, updates

## Implemented Placements
- Homepage: `homepage_announcement`
- Dashboard: `dashboard_sidebar`
- Studio: `studio_recommendations`
- Billing/Credits help: `billing_upgrade`
- Enterprise: `enterprise_cta`
- Documentation: `docs_partner_recommendations`
- Success / learning center: `learning_center`
- Blog: `blog_affiliate_recommendations`

## Data Model
- `RevenuePromotion`
  - scheduling
  - priority
  - target page
  - placements
  - audience rules
  - CTA mode and optional checkout plan
  - A/B variants JSON
- `RevenuePromotionInteraction`
  - action
  - placement
  - page path
  - user/session context
  - revenue generated

## Conversion Attribution
- Promo-linked checkouts append promotion metadata to the provider success URL
- A global attribution tracker records conversion events when payment success returns with promotion context
- View/click/dismiss events are written directly by the promotion placement component

## UX Guardrails
- Promotions are excluded from checkout, auth flows, password reset, error pages, and render/progress UI
- Premium visual language only: rounded cards, soft borders, glass treatment, low-noise CTAs
- Empty states remain real; metrics start at zero until interaction data exists
