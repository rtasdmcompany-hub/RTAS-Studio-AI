# RTAS Studio AI — Pricing Optimization

**Classification:** Growth / monetization  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Sprint:** Phase 11 · Sprint 8  
**Integrity:** Separates **CURRENT LIVE** tiers from **PROPOSED** packaging language. No invented free plan.

---

## Source of truth (CURRENT LIVE)

Constants live in product shared credits; public messaging must not invent prices.

| Internal / product name | Price | Credits / access | Status |
|-------------------------|-------|------------------|--------|
| **Tester** | $5 (one-time / time-boxed) | 30 seconds · 5 days | LIVE |
| **Standard** | $89 / month | 2000 seconds | LIVE |
| **Premium 4K** | $249 / month | 2000 seconds | LIVE |
| **Free** | $0 | **0 credits** (no free generation pool) | LIVE account state — **not a plan to sell** |

**Credit model (VERIFIED):** 1 credit = 1 second.

**Checkout:** Paddle Merchant of Record — may still be pending approval (**growth blocker**).

Cross-links: [`business/README.md`](../../business/README.md) · [`docs/marketing/PRICING-STRATEGY.md`](../marketing/PRICING-STRATEGY.md) · [`business/sales/ICP.md`](../../business/sales/ICP.md)

---

## Current vs proposed — honesty table

Marketing and sales often want Starter / Pro / Agency / Enterprise language. Map carefully. **Do not claim SKUs that are not in checkout.**

| Proposed sales language | Maps to CURRENT LIVE | What is true today | What is proposed only |
|-------------------------|----------------------|--------------------|------------------------|
| **Starter** | **Tester** | $5 · 30s · 5 days · prove the pipeline | Rename/label in copy only if product UI/checkout still resolve to Tester economics |
| **Pro** | **Standard** | $89/mo · 2000s · core studio | “Most popular” positioning; optional annual later (**not live**) |
| **Agency** | **Standard × N seats** and/or **Premium** mix | Buyers purchase multiple Standard/Premium seats; no separate Agency SKU in billing | Dedicated Agency SKU, pooled credits, shared workspace, invoicing (**proposed**) |
| **Enterprise** | **Premium pilot** or multi-seat + custom terms | Premium 4K is the quality ceiling SKU; enterprise is a **developing ICP** | Custom ACV, SSO, MSA, security pack, volume seconds (**proposed**) |
| **Free** | Free account with **0 credits** | Not a monetization plan; paywall on generate | Do **not** invent a live free credit tier for growth experiments without product + finance sign-off |

Historical messaging note: [`docs/marketing/PRICING-STRATEGY.md`](../marketing/PRICING-STRATEGY.md) uses “Creator Starter / Pro Studio / Production Enterprise” as **positioning labels** for the same $5 / $89 / $249 economics. Treat those as marketing aliases for Tester / Standard / Premium—not as separate products—until billing SKUs change.

---

## List economics (VERIFIED math)

| Tier | Price | Seconds | Implied $/sec (if fully used) |
|------|------:|--------:|------------------------------:|
| Tester | $5 | 30 | ≈ $0.167 |
| Standard | $89 | 2000 | $0.0445 |
| Premium 4K | $249 | 2000 | $0.1245 |

Premium charges more for **quality / cinematic 4K positioning**, not for more seconds. That is intentional ARPU design—communicate it clearly so buyers do not expect 3× credits at $249.

---

## Optimization goals

1. Maximize **Tester → Standard** conversion inside and immediately after the 5-day window.  
2. Increase **Premium mix** among quality-sensitive agencies and brand teams.  
3. Enable **multi-seat** revenue without inventing a fake Agency plan in the UI.  
4. Prepare **Enterprise** commercial path without overselling readiness.  
5. Keep trust: no bait free credits that violate current product economics.

---

## Recommended packaging moves (PROPOSED — not live)

### Near term (copy & sales only)

| Move | Rationale | Risk if mishandled |
|------|-----------|--------------------|
| Use Starter/Pro as **aliases** for Tester/Standard in ads | Matches buyer vocabulary | Confusion if checkout still says Tester/Standard—add “also called…” once |
| Sell “Agency” as **N× Standard/Premium seats** | Honest today | Do not show Agency price on /pricing until SKU exists |
| Position Premium as **Pro + cinematic 4K** | Explains price delta | Do not imply unlimited 4K cinema for Tester |

### Medium term (requires product/billing work — out of this sprint’s code scope)

| Proposal | Description | Gate |
|----------|-------------|------|
| Annual Standard / Premium | ~2 months free equivalent or similar | Finance + Paddle price IDs |
| Agency pack | Pooled 5k–10k seconds, 3–5 seats, shared billing | Product multi-seat + MoR items |
| Enterprise custom | Volume seconds, MSA, security questionnaire pack | Diligence pack + support capacity |
| Credit top-ups | Overage seconds without full tier jump | Clear rate card; prevent bill shock |

### Explicitly rejected for now

| Idea | Why rejected |
|------|--------------|
| Public free plan with free seconds | Contradicts current product (0 credits); high abuse / COGS risk |
| Fake “unlimited” tier | Economics and AUP posture break |
| Invented discount codes as permanent pricing | Erodes trust; complicates MoR |

---

## Persona → tier guidance (CURRENT)

| Persona | First buy | Optimize toward |
|---------|-----------|-----------------|
| Creator | Tester (Starter language OK) | Standard (Pro) |
| Agency | Standard or Tester→Standard | Multi-seat + selective Premium |
| Startup | Tester → Standard | Premium for brand-sensitive launches |
| Enterprise evaluator | Premium or multi-seat | Custom commercial (**proposed**) |

---

## Experiments to run (after checkout stable)

| Experiment | Hypothesis (assumption) | Success signal |
|------------|-------------------------|----------------|
| Tester CTA prominence | Lower friction raises paid starts | Tester starts ↑ without refund ↑ |
| Premium comparison block | Clear 4K story raises upgrade rate | Standard→Premium ↑ |
| Agency “seats” calculator | Agencies buy 2+ seats | Seats per account ↑ |
| No free-credit promo | Honesty improves pay conversion | Paying / signup ↑ |

All results: record in [`GROWTH_METRICS_DASHBOARD.md`](GROWTH_METRICS_DASHBOARD.md)—leave blank until measured.

---

## Founder checklist

- [ ] Audit all public pages: no “free credits” promise  
- [ ] Align sales one-pager language with Tester/Standard/Premium truth  
- [ ] Document Paddle price IDs ↔ tiers when checkout is live  
- [ ] Do not publish Agency/Enterprise SKUs until billing supports them  

---

*Companions: [`REVENUE_STRATEGY.md`](REVENUE_STRATEGY.md) · [`ENTERPRISE_EXPANSION_PLAN.md`](ENTERPRISE_EXPANSION_PLAN.md) · [`SALES_FUNNEL_BLUEPRINT.md`](SALES_FUNNEL_BLUEPRINT.md)*
