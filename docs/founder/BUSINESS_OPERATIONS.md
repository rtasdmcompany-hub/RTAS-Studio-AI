# Business Operations — RTAS Studio AI

**Operator:** RTAS Digital Marketing Company (Pakistan)  
**Product:** https://rtasstudio.com  
**Phase:** 13 · Sprint 10 · 23 July 2026  

**Companions:** [`FOUNDER_GUIDE.md`](./FOUNDER_GUIDE.md) · [`FOUNDER_CHECKLIST.md`](./FOUNDER_CHECKLIST.md) · [`OPERATIONS_RUNBOOK.md`](./OPERATIONS_RUNBOOK.md) · [`../business/COMPANY_OPERATING_SYSTEM.md`](../business/COMPANY_OPERATING_SYSTEM.md)

---

## 1. Operating model (today)

Single founder-operator covering CEO/CTO/COO/CRO/CPO/CISO/CFO functions. No separate NOC, sales team, or CS org is claimed.

| Function | How it runs |
|----------|-------------|
| Product & eng | Repo + Vercel deploys |
| Commerce | Paddle MoR (LS adapter ready) |
| Support | Email + help center |
| Marketing | Docs + site; paid ads **off** until GO |
| Finance | MoR payouts + private spreadsheet (actuals only) |
| Security | Fail-closed APIs; prior audit; monthly access review |

---

## 2. Business readiness snapshot (Sprint 10)

| Area | Result | Evidence |
|------|--------|----------|
| Brand positioning | **PASS** (docs) | `marketing/brand-positioning.md` + Sprint 1 report |
| Pricing truth | **PASS** | Live `/pricing` $5/$89/$249; shared constants |
| Funnel surfaces | **PARTIAL** | Core journey up; GTM pages 404; conversion E2E open |
| Affiliate program | **FAIL / not live** | `/affiliate` **404** |
| Partners program | **FAIL / not live** | `/partners` **404** |
| Customer success | **PARTIAL** | Help/feedback live; no CRM; CS checklist in profile code |
| Marketing automation | **PARTIAL** | Auth email path; lifecycle automation not proven |
| BI / analytics | **FAIL / off** | health `analytics: false`; dashboard formulas blank |
| Launch assets | **PARTIAL** | Legal/sales docs strong; some Sprint 8 pages undeployed |
| Ops docs | **PASS** | Ops manual + this founder pack |

---

## 3. Commercial policy (binding for founder)

1. **Paid acquisition spend = $0** until GLOBAL_LAUNCH_APPROVAL flips from NOT APPROVED.  
2. Speak MoR honestly — never invent checkout success.  
3. Identity Preservation = authorized only.  
4. Refunds via Paddle; product support via RTAS email.  
5. Collections = MoR reports + ledger — no fictional MRR slides.

---

## 4. Cadence summary

| Cadence | Primary doc |
|---------|-------------|
| Daily | [`FOUNDER_CHECKLIST.md`](./FOUNDER_CHECKLIST.md) § Daily |
| Weekly | Checklist + [`EXECUTIVE_DASHBOARD.md`](./EXECUTIVE_DASHBOARD.md) |
| Monthly | Access, backup drill, vendor invoices, risk register |
| Release | [`OPERATIONS_RUNBOOK.md`](./OPERATIONS_RUNBOOK.md) § Release |
| Incident | [`BUSINESS_CONTINUITY_PLAN.md`](./BUSINESS_CONTINUITY_PLAN.md) |

---

## 5. Vendor map

| Vendor | Role |
|--------|------|
| Vercel | Web hosting / edge |
| Supabase | Postgres / auth data plane |
| Paddle | Merchant of Record |
| Fal.ai | Primary generation |
| Resend | Transactional email |
| Cloudflare | DNS / edge (as configured) |
| Google | OAuth |
| GitHub | Source |

Vendor detail: [`../operations/VENDOR_MANAGEMENT.md`](../operations/VENDOR_MANAGEMENT.md).

---

## 6. First-customer execution (when gates clear)

Follow [`../commercial/FIRST_CUSTOMER_EXECUTION_PLAN.md`](../commercial/FIRST_CUSTOMER_EXECUTION_PLAN.md) with real emails only. Soft invite cohort before ads.

---

## 7. Hiring triggers (Recommended — not commitments)

| Trigger | Consider |
|---------|----------|
| Sustained SEV load > founder capacity | Part-time support |
| Proven MRR + conversion | Growth marketer |
| Enterprise pipeline real | Solutions / AE |
| Compliance customer demand | Security contractor |

Do not hire to “look funded.”

---

*Phase 13 Sprint 10 — Business Operations.*
