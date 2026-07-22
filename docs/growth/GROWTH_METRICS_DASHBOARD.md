# RTAS Studio AI — Growth Metrics Dashboard

**Classification:** Growth / measurement  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Sprint:** Phase 11 · Sprint 8  
**Rule:** Formulas and definitions only. **All measured values blank until real data exists.** No invented KPIs.

---

## How to use this document

1. Instrument events to match definitions.  
2. Fill the **Value** column from analytics, Paddle, and CRM—never from guesses.  
3. Label estimates explicitly if used for planning outside this sheet.  
4. Recalculate weekly (acquisition) and monthly (retention/revenue).

Cross-links: [`REVENUE_STRATEGY.md`](REVENUE_STRATEGY.md) · [`SALES_FUNNEL_BLUEPRINT.md`](SALES_FUNNEL_BLUEPRINT.md) · [`RETENTION_STRATEGY.md`](RETENTION_STRATEGY.md) · [`business/roadmap/BUSINESS_ROADMAP.md`](../../business/roadmap/BUSINESS_ROADMAP.md) · [`business/investors/README.md`](../../business/investors/README.md)

---

## Verified pricing inputs (constants)

| Input | Value | Status |
|-------|------:|--------|
| Tester price | $5 | VERIFIED |
| Tester seconds | 30 | VERIFIED |
| Tester window | 5 days | VERIFIED |
| Standard price | $89 / mo | VERIFIED |
| Standard seconds | 2000 | VERIFIED |
| Premium price | $249 / mo | VERIFIED |
| Premium seconds | 2000 | VERIFIED |
| Credit model | 1 credit = 1 second | VERIFIED |
| Free credits | 0 | VERIFIED |

---

## A. Acquisition funnel

| Metric | Formula | Value | Period |
|--------|---------|------:|--------|
| Unique visitors | Count | | |
| Signups | Count | | |
| Visit→Signup % | `signups / visitors` | | |
| Activated users | Users with first Studio success action | | |
| Signup→Activated % | `activated / signups` | | |
| Tester starts | Successful Tester checkouts | | |
| Standard starts | New Standard subscriptions | | |
| Premium starts | New Premium subscriptions | | |
| First-paid accounts | Distinct accounts with any paid event | | |
| Signup→Paid % | `first_paid / signups` | | |

---

## B. Monetization & mix

| Metric | Formula | Value | Period |
|--------|---------|------:|--------|
| MRR | `Σ Standard_MRR + Σ Premium_MRR` (exclude one-time Tester or amortize separately) | | |
| Tester revenue | `tester_count × $5` (period) | | |
| ARPU (paid) | `period_revenue / paying_accounts` | | |
| Standard share of MRR | `standard_MRR / MRR` | | |
| Premium share of MRR | `premium_MRR / MRR` | | |
| Tester→Standard % | `standard_from_tester / tester_starts` (e.g. 14-day) | | |
| Standard→Premium % | `premium_upgrades / standard_accounts` (e.g. 60-day) | | |
| Seats per account | `active_seats / paying_accounts` | | |

---

## C. Retention & expansion

| Metric | Formula | Value | Period |
|--------|---------|------:|--------|
| Logo churn % | `cancelled_paid / paid_BoP` | | |
| Revenue churn % | `lost_MRR / MRR_BoP` | | |
| Gross revenue retention | `MRR_from_BoP_cohort_EoP / MRR_BoP` | | |
| Net revenue retention | `(MRR_BoP − churn − contraction + expansion) / MRR_BoP` | | |
| Idle paid % | `paid_with_0_gens_14d / paid` | | |
| Credit utilization % | `seconds_used / seconds_granted` | | |
| Tester expiry w/o upgrade % | `testers_expired_unconverted / tester_starts` | | |

---

## D. Unit economics (fill when CAC/COGS known)

| Metric | Formula | Value | Period |
|--------|---------|------:|--------|
| CAC (blended) | `sales_and_marketing_spend / new_paying_accounts` | | |
| CAC by channel | `channel_spend / channel_new_paying` | | |
| Contribution per account | `revenue − generation_COGS − payment_fees − support_alloc` | | |
| Payback months | `CAC / monthly_contribution` | | |
| LTV (simple) | `ARPU × gross_margin × lifetime_months` | | |
| LTV:CAC | `LTV / CAC` | | |

**Do not publish LTV:CAC externally until inputs are measured.**

---

## E. Checkout / MoR health (leading indicator)

| Metric | Formula | Value | Period |
|--------|---------|------:|--------|
| Checkout attempt→success % | `successful_checkouts / checkout_attempts` | | |
| Payment failure % | `failed_payments / payment_attempts` | | |
| Refund rate % | `refunds / successful_payments` | | |
| MoR blocker status | Qualitative: open / mitigating / clear | | |

If checkout success is near zero, treat acquisition spend as blocked.

---

## F. Assisted sales pipeline

| Metric | Formula | Value | Period |
|--------|---------|------:|--------|
| Outbound accounts touched | Count | | |
| Replies | Count | | |
| Qualified opportunities | Count | | |
| Closed-won (paid) | Count | | |
| Closed-won MRR | Sum | | |
| Win rate | `won / qualified` | | |

No vanity opportunities.

---

## G. Affiliate (only if program launches)

| Metric | Formula | Value | Period |
|--------|---------|------:|--------|
| Affiliate-sourced paid | Count | | |
| Commission expense | Sum | | |
| Affiliate fraud / refund % | As defined in affiliate strategy | | |

Program is **proposed, not live** — leave blank.

---

## Suggested weekly scorecard (founder)

1. MoR/checkout health  
2. New first-paid  
3. Tester→Standard conversions  
4. Idle paid count + outreach done  
5. One qualitative churn theme  

---

## Data sources (wire when ready)

| Source | Feeds |
|--------|-------|
| Web analytics | Visitors, funnel pages |
| App database / admin | Signups, tiers, credits, generations |
| Paddle | Checkouts, MRR, refunds, failed payments |
| Email / CRM | Assisted pipeline |
| Support inbox | Qualitative tags |

---

## Blank attestation

As of Sprint 8 documentation date, **no production KPI values are asserted in this file**. Filling numbers without instrumentation is a policy violation for investor and public materials.

---

*Companions: all docs in `docs/growth/` · Sprint report [`docs/business/PHASE11-SPRINT8-REPORT.md`](../business/PHASE11-SPRINT8-REPORT.md)*
