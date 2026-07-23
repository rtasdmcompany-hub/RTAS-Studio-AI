# Customer Lifecycle — RTAS Studio AI

**Phase:** 13 · Sprint 3  
**Integrity:** Stages derived from real account signals. Overlapping admin buckets are OK — not a fake funnel chart.

---

## Stages

| Stage | Definition (signals) |
|-------|----------------------|
| Visitor | No account |
| Signup | Account created, email not verified |
| Verified | `emailVerified = true` |
| Activated | Project/job or trial flag present |
| First video | ≥1 completed generation job |
| Paid | Tester / Standard / Premium tier or `subscriptionActive` |
| Retained | Active subscription + completed video |
| Expanded | Active Premium |
| Churn risk / Churned | Prior paid tier, inactive, 0 credits |
| Customer success | Support / Help engagement (operational) |

Helpers: `apps/web/src/lib/customer-lifecycle.ts`  
Dashboard: Getting started checklist + Customer Retention Center  
Admin: `/admin/revenue` lifecycle count buckets (real DB counts)

---

## Wiring

- Client: Retention Center emits `Retention Center Viewed` + `Lifecycle Stage`
- Server: Lead / feedback / commercial lead → `SystemLog` sources for ticket aggregates
- Billing: `BillingTransaction` for recent transactions & ledger collected

---

## Non-goals

- No invented stage conversion %
- No fake cohort charts
- Referral program UI labeled **Proposed** until live
