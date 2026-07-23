# Customer Acquisition Plan

**Phase:** 13 · Sprint 9  
**Dashboard:** `/admin/acquisition` (admin secret)  
**Code:** `apps/web/src/lib/launch/acquisition.ts`

---

## Funnel stages

| Stage | Definition | Data source |
|-------|------------|-------------|
| Visitors | Unique site traffic | Ready for Integration (GA4/PostHog) — display null/0 |
| Registrations | User rows | `User.count` |
| Verified | `emailVerified = true` | Prisma |
| Activated | Trial used or any generation job | Prisma |
| Free | `tier=free` & no active sub | Prisma |
| Paid | Active sub or tester/standard/premium tier | Prisma |
| Enterprise leads | `EnterpriseLead` rows | Prisma |
| Sources | `EnterpriseLead.source` groupBy | Prisma |

Zeros are valid. Never invent traffic or paid conversions.

---

## Motions → funnel

1. **Organic / content** — Campaign Center CTAs → signup.
2. **PLG** — Tester $5 path after live billing clearance.
3. **Sales-assisted** — `/enterprise`, `/demo` → CRM.
4. **Partners / affiliates** — `/partners`, `/affiliate` → applications (metrics start at 0).
5. **Paid** — Google/Meta plans only after conversion events verified.

---

## Weekly operating rhythm

1. Review `/admin/acquisition` aggregates.
2. Compare to RevOps (`/admin/revenue`) — no double-counting invented MRR.
3. Move Launch checklist items when evidence exists.
4. Triage `/feedback` board (real votes only).

---

## Integrity rules

- No fabricated downloads, rankings, or campaign ROAS.
- Visitor field stays **Ready for Integration** until analytics vendor is live.
- Paid acquisition spend remains $0 until commercial E2E is proven.
