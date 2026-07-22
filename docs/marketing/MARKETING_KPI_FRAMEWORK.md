# RTAS Studio AI — Marketing KPI Framework

**Classification:** Marketing / measurement  
**Phase:** 12 · Sprint 5  
**Rule:** **Formulas + reporting structure only.** Value columns stay blank until filled from analytics, Paddle, ESP, CRM, or Search Console. No fabricated KPIs.

Cross-links: [`../growth/GROWTH_METRICS_DASHBOARD.md`](../growth/GROWTH_METRICS_DASHBOARD.md) · [`CUSTOMER_ACQUISITION_CHANNELS.md`](CUSTOMER_ACQUISITION_CHANNELS.md)

---

## 1. Verified constants (inputs — not KPIs)

| Input | Value |
|-------|------:|
| Tester price | $5 |
| Tester seconds | 30 |
| Tester window | 5 days |
| Standard price | $89 / mo |
| Premium 4K price | $249 / mo |
| Monthly credit pool (Standard/Premium) | 2000 s |
| Credit model | 1 credit = 1 second |
| Free credits | 0 |

---

## 2. Reporting cadence

| Cadence | Focus |
|---------|--------|
| Weekly | Acquisition funnel, spend, checkout health |
| Monthly | Retention, MRR mix, channel CAC, content/SEO |
| Quarterly | Positioning, channel mix, enterprise pipeline quality |

---

## 3. Acquisition KPIs

| Metric | Formula | Value | Period |
|--------|---------|------:|--------|
| Unique visitors | Count from analytics | | |
| Signups | Count | | |
| Visit → Signup % | `signups / visitors` | | |
| Activated users | Users with ≥1 successful generation | | |
| Signup → Activated % | `activated / signups` | | |
| Tester checkouts | Successful Tester payments | | |
| Standard starts | New Standard subscriptions | | |
| Premium starts | New Premium subscriptions | | |
| Signup → Paid % | `first_paid_accounts / signups` | | |

---

## 4. Revenue & monetization KPIs

| Metric | Formula | Value | Period |
|--------|---------|------:|--------|
| Tester revenue | `tester_count × $5` | | |
| MRR | `Σ Standard + Σ Premium` (exclude one-time Tester or report separately) | | |
| ARPU (paid) | `period_revenue / paying_accounts` | | |
| ARPPU | `period_revenue / active_paid_accounts` | | |
| Tester → Standard % | `standard_from_tester / tester_cohort` | | |
| Standard → Premium % | `premium_from_standard / standard_cohort` | | |

---

## 5. Channel efficiency KPIs

| Metric | Formula | Value | Period |
|--------|---------|------:|--------|
| Blended CAC | `total_sales_marketing_spend / new_paying_accounts` | | |
| Channel CAC | `channel_spend / channel_paying_accounts` | | |
| Paid CTR | `clicks / impressions` | | |
| Landing CVR | `conversions / landing_sessions` | | |
| Refund rate | `refunds / successful_payments` | | |

---

## 6. Retention & engagement KPIs

| Metric | Formula | Value | Period |
|--------|---------|------:|--------|
| Logo churn | `churned_subs / start_of_period_subs` | | |
| Revenue churn | `lost_MRR / start_MRR` | | |
| Net revenue retention | `(start_MRR + expansion − contraction − churn) / start_MRR` | | |
| DAU/WAU/MAU | Distinct active generators | | |
| Support RTA | `% tickets responded within target` | | |

---

## 7. Content / SEO / email KPIs

| Metric | Formula | Value | Period |
|--------|---------|------:|--------|
| Organic clicks | GSC clicks | | |
| Organic CTR | `clicks / impressions` | | |
| Indexed pages | GSC coverage | | |
| Email delivery % | `delivered / sent` | | |
| Email CTR | `unique_clicks / delivered` | | |
| Unsubscribe % | `unsubs / delivered` | | |

---

## 8. Integrity KPIs (process)

| Metric | Formula | Target intent |
|--------|---------|---------------|
| Fake-proof incidents | Count of fabricated-metric violations caught | Minimize to 0 |
| Messaging defects | Pages with free-trial or plan-name contradictions | Minimize to 0 |
| Checkout failure rate | `failed_checkouts / checkout_starts` | Monitor; pause paid if spiking |

---

## 9. Dashboard ownership

| Source | Owner use |
|--------|-----------|
| Product analytics | Funnel |
| Paddle | Revenue, refunds |
| Search Console | SEO |
| ESP | Email |
| CRM | Outbound / enterprise |
| Ads managers | Paid CAC |

**Never** paste estimated numbers into investor or public materials without labeling them as estimates — prefer blanks over fiction.
