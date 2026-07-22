# Phase 12 · Sprint 1 — Launch Blockers

**Product:** RTAS Studio AI · https://rtasstudio.com  
**As-of:** 23 July 2026  
**Rule:** Only **real** blockers. No invented issues. Soft preferences that do not stop a careful first customer are omitted or marked Low.

**Companion:** [`COMMERCIAL_LAUNCH_CHECKLIST.md`](./COMMERCIAL_LAUNCH_CHECKLIST.md) · [`FIRST_CUSTOMER_READINESS.md`](./FIRST_CUSTOMER_READINESS.md)

---

## Critical

Must be green before **public paid launch / paid acquisition spend**.

| ID | Blocker | Evidence | Owner action |
|----|---------|----------|--------------|
| C1 | **Live Paddle checkout + credit grant not E2E proven** | Checkout code fail-closes with **503** when price IDs / static checkout URLs missing (`apps/web/src/app/api/checkout/route.ts`). Phase 10 verification recorded missing webhook secret / incomplete checkout enablement. Prod `/api/payments/config` now shows provider `paddle` and a non-null `clientToken`, but a **real Tester/Standard/Premium purchase → webhook → credits** was **not** verified in this sprint. | Confirm Paddle seller domain/checkout enabled; set price IDs and/or checkout URLs; set `PADDLE_WEBHOOK_SECRET`; remove defer flags; run one live purchase per plan and screenshot ledger |
| C2 | **Live generation may still be blocked** | Phase 10 production health: `live_generation: false` / Fal credit issues documented. A paying customer who cannot render receives no value. | Confirm Fal wallet + production generate path; one successful paid render after C1 |

---

## High

Should be fixed before broad marketing; acceptable only for closed founder tests.

| ID | Blocker | Evidence | Owner action |
|----|---------|----------|--------------|
| H1 | **`/contact` returns 404** | Prod HEAD `https://rtasstudio.com/contact` → **404**. Canonical contact is `/help/contact`; `/support` redirects correctly. Users typing `/contact` dead-end. | Add redirect `/contact` → `/help/contact` (minimal change; no redesign) |
| H2 | **Plan naming split (marketing vs product)** | Marketing: Creator Starter / Pro Studio / Production Enterprise (`pricing-tiers.ts`, homepage). Product/paywall/dashboard: Tester / Standard / Premium. Support and conversion risk. | Map names clearly on pricing (e.g. “Creator Starter (Tester)”) or align labels to shared constants |
| H3 | **Stale “free trial” / free-preview copy** | `how-to-use-content.ts`, help billing, and related copy still describe free/watermarked free tiers while product entry is **paid Tester** and new accounts start at **0** credits. | Remove or rewrite free-trial language to match Tester $5 entry |
| H4 | **Auth email delivery must remain proven** | Signup / verify / password reset depend on Resend (`auth@rtasstudio.com`). Without delivery, journey dies before checkout. | Periodic test: signup + forgot-password inbox receipt |

---

## Medium

Does not stop a careful early customer; damages trust or ops if ignored.

| ID | Blocker | Evidence | Owner action |
|----|---------|----------|--------------|
| M1 | Soft trust overclaims | `SITE_TRUST_BADGES`: “Enterprise Ready”, “99.9% Availability” without published SLA/certs | Soften copy or substantiate |
| M2 | Status page messaging | `/status` presents operational posture; not a substitute for real incident process | Keep honest; wire to real probes / do not overclaim |
| M3 | Discord invite unverified | Footer/contact use `https://discord.gg/rtas` | Validate invite or remove until live |
| M4 | Contact/feedback = mailto only | No ticket CRM | Acceptable at stage; set response-time expectation |
| M5 | Thin content hubs | Blog / careers / developers / docs are real pages but not deep CMS/SDK experiences | OK for early launch; do not sell as enterprise developer platform |
| M6 | Brand asset repo sync | Prod serves `rtas-favicon.png` / `rtas-logo.png`; local `apps/web/public/` is sparse (`logo.svg`, `og-image.png`, manifest). Risk of future deploy drift. | Ensure brand PNGs are versioned or deploy-synced |
| M7 | Payments config naming confusion | `/api/payments/config` exposes `premium.priceUsd: 89` (Standard monthly constant naming) | Clarify API/docs labels to avoid internal mistakes |

---

## Low

Polish; not launch-stopping.

| ID | Item | Note |
|----|------|------|
| L1 | Homepage “Start creating” → login for guests | Intentional auth gate; optional microcopy “Sign in to open Studio” |
| L2 | `/logo.png` 404 | Unused primary path; primary marks use `/rtas-logo.png` / `/logo.svg` |
| L3 | Full CWV / Lighthouse program | Not executed this sprint |
| L4 | JSON-LD richness | Page metadata strong; optional Product/Organization schema later |

---

## Explicitly NOT blockers

| Item | Why excluded |
|------|--------------|
| Missing fake testimonials / logos | Correct integrity — absence is good |
| Missing SOC 2 / ISO claims | Correctly not claimed |
| No invented MRR | Correct |
| Engineering redesign / new experimental features | Out of Phase 12 Sprint 1 scope |

---

## Clearance order (recommended)

1. **C1** Paddle purchase E2E (Tester first, then Standard, then Premium)  
2. **C2** One live generation after credits land  
3. **H1** `/contact` redirect  
4. **H2 + H3** Naming + free-trial copy hygiene  
5. **H4** Email delivery spot-check  
6. Medium claim / Discord / asset sync as capacity allows  

---

## Status legend for Sprint 2 tracking

| State | Meaning |
|-------|---------|
| Open | Still blocks or risks launch |
| Verifying | Fix deployed; awaiting live proof |
| Cleared | Evidence attached (timestamp + method) |

*Only real blockers. Update this file when Cleared — do not delete history; mark status.*
