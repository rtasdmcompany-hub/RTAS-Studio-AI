# Founder Guide — RTAS Studio AI

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (Pakistan) · RTAS brand ecosystem  
**Phase:** 13 · Sprint 10 — Final Founder Handover  
**As-of:** 23 July 2026  
**Companion pack:** [`EXECUTIVE_DASHBOARD.md`](./EXECUTIVE_DASHBOARD.md) · [`FOUNDER_CHECKLIST.md`](./FOUNDER_CHECKLIST.md) · [`OPERATIONS_RUNBOOK.md`](./OPERATIONS_RUNBOOK.md) · [`BUSINESS_CONTINUITY_PLAN.md`](./BUSINESS_CONTINUITY_PLAN.md) · [`VERSION_ROADMAP.md`](./VERSION_ROADMAP.md) · [`BUSINESS_OPERATIONS.md`](./BUSINESS_OPERATIONS.md)

**Prior depth (do not discard):** [`../business/FOUNDER_MASTER_PLAYBOOK.md`](../business/FOUNDER_MASTER_PLAYBOOK.md) · [`../investors/FOUNDER_PLAYBOOK.md`](../investors/FOUNDER_PLAYBOOK.md) · [`../operations/OPERATIONS_MANUAL.md`](../operations/OPERATIONS_MANUAL.md)

---

## 1. What you own

You are founder-operating as CEO / CTO / COO / CRO / CPO / CISO / CFO until roles are hired. The product is a **live marketing + auth shell** with a **commercial value path that is not yet E2E-proven** (payment → credits → live generation). Phase 13 Sprint 10 decision: **GLOBAL LAUNCH NOT APPROVED** until Critical gates clear — see [`../business/GLOBAL_LAUNCH_APPROVAL.md`](../business/GLOBAL_LAUNCH_APPROVAL.md).

| Domain | Your daily job |
|--------|----------------|
| Product truth | Keep Verified pricing & Identity Preservation rules in every surface |
| Commerce | Prove MoR checkout → webhook → credits before ads spend |
| Generation | Keep Fal (and fallbacks) funded; one smoke render after every major change |
| Trust | No fake customers, MRR, partners, reviews, certifications, or awards |
| Ops | Health/ready, inbox, deploy hygiene, incident honesty |

---

## 2. Verified product truth (non-negotiable)

| Fact | Value |
|------|-------|
| Apex | https://rtasstudio.com |
| Operator | RTAS Digital Marketing Company |
| Tester | **$5** · **30 seconds** · **5 days** |
| Standard | **$89/mo** · **2000 seconds** |
| Premium 4K | **$249/mo** · **2000 seconds** |
| Credits | **1 credit = 1 second** |
| Identity | **Authorized Identity Preservation only** — not deepfake / face-swap |

Source constants: `packages/shared/src/credits.ts`, `payments.ts`, legal pages `/terms` `/refund`.

---

## 3. Where to look (operating map)

| Need | Primary path |
|------|----------------|
| Launch decision | [`../business/GLOBAL_LAUNCH_APPROVAL.md`](../business/GLOBAL_LAUNCH_APPROVAL.md) |
| Phase 13 closure | [`../business/PHASE13_FINAL_REPORT.md`](../business/PHASE13_FINAL_REPORT.md) |
| Executive metrics (blank actuals) | [`EXECUTIVE_DASHBOARD.md`](./EXECUTIVE_DASHBOARD.md) · live admin [`/admin`](https://rtasstudio.com/admin) · revenue [`/admin/revenue`](https://rtasstudio.com/admin/revenue) |
| Daily/weekly ritual | [`FOUNDER_CHECKLIST.md`](./FOUNDER_CHECKLIST.md) |
| Incidents / DR | [`BUSINESS_CONTINUITY_PLAN.md`](./BUSINESS_CONTINUITY_PLAN.md) · [`OPERATIONS_RUNBOOK.md`](./OPERATIONS_RUNBOOK.md) |
| What ships next | [`VERSION_ROADMAP.md`](./VERSION_ROADMAP.md) |
| Payments architecture | [`../payments/README.md`](../payments/README.md) |
| Commercial blockers | [`../commercial/LAUNCH_BLOCKERS.md`](../commercial/LAUNCH_BLOCKERS.md) |
| Brand / ICP | [`../../marketing/brand-positioning.md`](../../marketing/brand-positioning.md) |

---

## 4. Soft vs paid launch (how to speak externally)

| Mode | Allowed today? | Condition |
|------|----------------|-----------|
| Browse marketing / legal / help | **Yes** | Honest copy; no invented traction |
| Invite-only demos | **Conditional** | Disclose generation/payment may need ops confirmation |
| Public paid ads / broad paid signup push | **No** | Until Paddle purchase → credits **and** live render proven |
| Claim “global commercial launch” / V1 GO | **No** | See GLOBAL_LAUNCH_APPROVAL |

---

## 5. Critical reopen sequence (ordered)

1. Confirm Fal wallet / generation path → one successful Studio render.  
2. Live **Tester** checkout on production → Paddle receipt → credit balance screenshot.  
3. Confirm webhook secret + price IDs / checkout URLs; ledger row present.  
4. Deploy outstanding aliases (`/contact`, GTM pages) or remove from outreach.  
5. Fix or redeploy `sitemap.xml` (prod **500** observed 23 Jul 2026).  
6. Enable observability (Sentry and/or consented analytics) or document deliberate deferral.  
7. Re-run Phase 13 Sprint 10-lite audit → update GLOBAL_LAUNCH_APPROVAL.

---

## 6. Integrity rules (never bend)

1. Never invent customers, revenue, investors, partnerships, press, reviews, certifications, or awards.  
2. Every PASS needs evidence (URL, HTTP status, screenshot, commit).  
3. Every FAIL needs a corrective action owner.  
4. Prefer “not verified” over a guessed green score.  
5. Status page and trust badges must not overclaim SLAs you have not contracted.

---

## 7. First 14 days after Critical clearance

| Day | Focus |
|-----|-------|
| 1–2 | Tester + Standard smoke; support inbox templates |
| 3–5 | Soft invite cohort (tracked sheet — real emails only) |
| 6–9 | Fix High items (naming map, free-trial copy, `/contact`) |
| 10–14 | Decide paid acquisition budget only if conversion measurable |

Detail: [`BUSINESS_OPERATIONS.md`](./BUSINESS_OPERATIONS.md) · prior [`../business/90_DAY_EXECUTION_PLAN.md`](../business/90_DAY_EXECUTION_PLAN.md).

---

*Phase 13 Sprint 10 — Founder Guide. Not legal advice.*
