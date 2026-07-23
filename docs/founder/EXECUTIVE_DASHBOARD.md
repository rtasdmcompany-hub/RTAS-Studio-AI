# Executive Founder Dashboard — RTAS Studio AI

**Phase:** 13 · Sprint 10  
**As-of:** 23 July 2026  
**Rule:** Formulas + verified gates only. **Do not invent DAU, MRR, LTV, CAC, customers, or partners.**

**Live admin (auth required):** [`/admin`](https://rtasstudio.com/admin) · [`/admin/revenue`](https://rtasstudio.com/admin/revenue)  
**Calc-only predecessor:** [`../analytics/EXECUTIVE_DASHBOARD.md`](../analytics/EXECUTIVE_DASHBOARD.md)  
**Launch gate:** [`../business/GLOBAL_LAUNCH_APPROVAL.md`](../business/GLOBAL_LAUNCH_APPROVAL.md)

---

## 1. Launch & readiness gauges (evidence-based)

| Gauge | Score / Status | Evidence (23 Jul 2026) |
|-------|---------------:|------------------------|
| Overall founder readiness | **58 / 100** | Critical commercial path unproven |
| Platform surface health | **72 / 100** | Core pages 200; GTM aliases 404; sitemap 500 |
| Commercial monetization | **40 / 100** | Paddle `clientToken` present; E2E purchase **not** proven |
| Generation fulfillment | **35 / 100** | Public health no longer exposes Fal; Phase 10–12 `fal_credit` / live_generation false **not cleared** |
| Legal / trust docs | **90 / 100** | `/privacy` `/terms` `/refund` `/trust-safety` `/ai-policy` `/cookies` **200** |
| Observability | **30 / 100** | `/api/health` → `sentry: false`, `analytics: false` |
| Ops documentation | **85 / 100** | Founder pack + ops manuals present |
| Integrity posture | **95 / 100** | No fabricated traction found in audit surfaces |

**Verdict line:** GLOBAL LAUNCH **NOT APPROVED** — soft browse OK; paid acquisition blocked.

---

## 2. Production pulse (fill daily)

| Probe | Command / URL | Pass criteria | Last observed |
|-------|---------------|---------------|---------------|
| Liveness | `GET /api/health` | `status: ok` | **PASS** · `2026-07-23T06:02:50Z` · sentry/analytics false |
| Readiness | `GET /api/ready` | `status: ready` | **PASS** · `2026-07-23T06:02:49Z` |
| Payments config | `GET /api/payments/config` | provider + clientToken when Paddle live | **PARTIAL** · `provider: paddle`, `clientToken` non-null; `premium.priceUsd: 89` naming confusing |
| Homepage | `GET /` | 200 | **PASS** |
| Pricing | `GET /pricing` | 200 + $5/$89/$249 | **PASS** |
| Contact alias | `GET /contact` | 200 or redirect | **FAIL** · **404** |
| Sitemap | `GET /sitemap.xml` | 200 XML | **FAIL** · **500** |
| GTM pages | `/enterprise` `/beta` `/partners` `/affiliate` | 200 if marketed | **FAIL** · **404** each |

---

## 3. KPI worksheet (actuals blank until measured)

### A. Funnel

| KPI | Formula | Actual |
|-----|---------|-------:|
| Homepage uniques | Analytics (consented) or Vercel | |
| Signups | Count signup completed | |
| Email verified | Count verified | |
| First paid | Distinct paid entitlements | |
| Signup → paid % | `first_paid / signups` | |

### B. Revenue (Verified pricing inputs only)

| KPI | Formula | Actual |
|-----|---------|-------:|
| Tester revenue (period) | `tester_count × 5` (not MRR) | |
| MRR Standard | `active_standard × 89` | |
| MRR Premium | `active_premium × 249` | |
| MRR total | Standard + Premium | |
| ARR | `MRR × 12` | |

**Unknown until:** live MoR ledger reconcile + webhook proof.

### C. Product

| KPI | Formula | Actual |
|-----|---------|-------:|
| Successful renders | Jobs completed | |
| Credits granted | Ledger credits in | |
| Credits used | Ledger credits out | |
| Generation success rate | `success / started` | |

### D. Support & risk

| KPI | Formula | Actual |
|-----|---------|-------:|
| Open SEV-1 | Count | |
| Time to first response | Median hours | |
| Chargebacks / refunds | MoR dashboard | |
| Fal runway (days) | Balance / daily burn | |

---

## 4. Critical open gates (must be Cleared)

| ID | Gate | State | Clearance evidence required |
|----|------|-------|-----------------------------|
| C1 | Paddle purchase → webhook → credits | **Open** | Receipt + credit screenshot + ledger row |
| C2 | Live generation after credits | **Open** | One successful paid/Studio render download |
| C3 | Deploy drift (contact / GTM / sitemap) | **Open** | Prod 200s matching repo intent |
| C4 | Observability on or deferred in writing | **Open** | Sentry/analytics true **or** signed deferral note |

---

## 5. How to use admin pages

| Page | Use for |
|------|---------|
| `/admin` | Ops overview (authenticated owners only) |
| `/admin/revenue` | Revenue ops dashboard when ledger data exists |

Do **not** screenshot empty dashboards as “traction.” Blank is honest.

---

## 6. Weekly founder scorecard (print / paste)

| Question | Y/N / number |
|----------|--------------|
| Health + ready green all week? | |
| Any SEV-1? | |
| MoR E2E still proven this week? | |
| Fal balance runway > 7 days? | |
| Support inbox < 48h backlog for SEV≥2? | |
| Paid ads spend this week? (must be $0 until GO) | |
| Any claim published without evidence? | |

---

*Phase 13 Sprint 10 — Executive Founder Dashboard. Scores not inflated.*
