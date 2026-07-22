# RTAS Studio AI — Retention Strategy

**Classification:** Growth / lifecycle  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Sprint:** Phase 11 · Sprint 8  
**Integrity:** Strategies and formulas only. Retention rates blank until real cohorts exist.

---

## Retention thesis

Retention is won when customers **consume seconds productively** and believe the next month’s $89 or $249 will produce more commercial video than alternatives (freelancers, other AI tools, stock). Churn risk is highest when: checkout friction scars trust, Tester expires unused, Standard sits idle, or quality expectations were set like Hollywood VFX.

Cross-links: [`CUSTOMER_SUCCESS_FRAMEWORK.md`](CUSTOMER_SUCCESS_FRAMEWORK.md) · [`REVENUE_STRATEGY.md`](REVENUE_STRATEGY.md) · [`business/marketing/USP.md`](../../business/marketing/USP.md) · [`business/roadmap/BUSINESS_ROADMAP.md`](../../business/roadmap/BUSINESS_ROADMAP.md)

---

## Retention by tier

| Tier | Retention job | Primary risk |
|------|---------------|--------------|
| **Tester** | Convert to Standard/Premium before/at day 5 | Unused 30 seconds; confusion about “free” |
| **Standard** | Monthly renewal; habit of weekly generation | Idle subscription; credit intimidation |
| **Premium** | Justify quality premium each cycle | “Same seconds as Standard” misunderstanding |
| **Multi-seat** | Keep team workspace valuable | One champion leaves; seats unused |

---

## North-star retention metrics (formulas; values blank)

| Metric | Formula | Cadence |
|--------|---------|---------|
| Tester conversion | `subscriptions_from_testers / tester_starts` | Weekly |
| Logo churn (paid) | `cancelled_paid / paid_start_of_period` | Monthly |
| Gross revenue retention | `MRR_end_from_start_cohort / MRR_start_cohort` (excl. new) | Monthly |
| Net revenue retention | `(MRR_end_incl_expansion − churn − contraction) / MRR_start` | Monthly |
| Idle paid rate | `paid_accounts_with_0_gens_in_14d / paid_accounts` | Weekly |
| Credit utilization | `seconds_used / seconds_granted` | Monthly |

Dashboard: [`GROWTH_METRICS_DASHBOARD.md`](GROWTH_METRICS_DASHBOARD.md).

---

## Drivers of retention (levers)

### 1. Time-to-first-success

If a paid user does not complete a successful generation quickly, retention collapses. CS Playbook B applies.

### 2. Expectation alignment

- Tester is evaluation, not a studio retainer.  
- Standard is volume/predictability at 1080p-class studio use.  
- Premium is quality/4K—not 3× credits.  
- No free plan—do not train users to wait for free credits.

### 3. Habit loops

Encourage recurring use cases from ICP: ad variants, social cuts, music video concepts, animation tests—**weekly**, not one-off novelty.

### 4. Trust continuity

Stable billing via Paddle, clear refund policy, consistent AUP. Payment failures and surprise declines are involuntary churn—monitor MoR health.

### 5. Product reliability

Generation success rate and queue transparency matter more than vanity feature launches for early retention.

---

## Lifecycle interventions

| Trigger | Intervention |
|---------|--------------|
| Paid + no generation in 48h | How-to nudge + support offer |
| Tester day 3 | Conversion education (2000s at $89) |
| Tester day 5 | Expiry + upgrade CTA |
| Utilization >80% mid-cycle | Expansion conversation (seat / future top-up) |
| Utilization <10% at day 20 | Save outreach: blocker diagnosis |
| Cancel request | Exit interview tags; right-size tier if applicable |
| Refund spike | Ops review: checkout, quality, messaging honesty |

---

## Win-back (proposed process)

1. Tag cancel reason.  
2. If checkout/product bug: fix + invite return with honesty (no fake coupons required).  
3. If price: acknowledge; Tester re-entry only if economically sane.  
4. If quality: Premium trial narrative only when appropriate—do not gift unlimited Premium.  
5. Do not harass; one thoughtful follow-up max unless they re-engage.

---

## Community & content retention (light)

| Asset | Use |
|-------|-----|
| Help Center / troubleshooting | Reduce silent frustration |
| Changelog | Show progress without fake roadmaps |
| Showcase videos (owned assets) | Remind of quality bar |
| Branding guidelines | Keep creative consistent ([`business/branding/README.md`](../../business/branding/README.md)) |

Avoid building a “community” vanity metric before paid cohort exists.

---

## Anti-patterns

- Buying retention with undeclared free credits that contradict product policy.  
- Fake case studies to “inspire” renewals.  
- Promising enterprise SLAs to Standard buyers.  
- Ignoring Paddle dunning / failed payment as “marketing churn.”

---

## 90-day retention program (founder-owned)

| Window | Focus |
|--------|-------|
| Days 1–30 | Instrument idle-paid and Tester conversion; manual outreach to every paid idle account |
| Days 31–60 | Written cancel taxonomy; weekly retention review |
| Days 61–90 | First real cohort chart (even if n is small); decide one product or messaging fix from churn themes |

---

*Companions: [`CUSTOMER_SUCCESS_FRAMEWORK.md`](CUSTOMER_SUCCESS_FRAMEWORK.md) · [`SALES_FUNNEL_BLUEPRINT.md`](SALES_FUNNEL_BLUEPRINT.md) · [`PRICING_OPTIMIZATION.md`](PRICING_OPTIMIZATION.md)*
