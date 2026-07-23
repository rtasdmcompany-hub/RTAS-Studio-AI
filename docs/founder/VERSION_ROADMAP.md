# Version Roadmap — RTAS Studio AI

**Product:** https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company  
**Phase:** 13 · Sprint 10 · 23 July 2026  

**Rules:** Honest. No invented shipped features. Labels: **Shipped** · **In repo / not proven live** · **Planned** · **Aspirational**.

Pricing truth for all versions: Tester $5/30s/5d · Standard $89 · Premium $249 · 1 credit = 1 second · Authorized Identity Preservation only.

---

## Version 1.0 — Soft commercial foundation (target: Critical gates Cleared)

**Intent:** First honest “customers can pay and get a video” release — not a marketing slogan.

| Area | Scope | Status |
|------|-------|--------|
| Marketing site + legal v1.1 | Apex, pricing, help, trust | **Shipped** (prod 200s) |
| Auth (email + Google) | Signup/login/reset UI | **Shipped** surfaces; inbox E2E **spot-check required** |
| Studio shell | Auth-gated compose/render UI | **Shipped** gate |
| MoR checkout (Paddle) | Config + adapters + ledger code | **In repo**; live purchase→credits **not proven** |
| Live generation (Fal) | Credit-guarded pipeline | **In repo**; live success **not cleared** (historical `fal_credit`) |
| Credits ledger | Provider billing ledger | **In repo**; prod migration/apply **verify** |
| Observability | Sentry + analytics | **Planned / off in prod** (`false`/`false`) |
| GTM pages | `/enterprise` `/beta` `/partners` `/affiliate` `/contact` | **In repo or docs**; **404 on prod** as of Sprint 10 |
| Sitemap | `/sitemap.xml` | **In repo**; prod **500** |

**Exit criteria for declaring V1.0 live commercially:** C1 + C2 Cleared with evidence; contact path fixed; sitemap 200; status page honest.

---

## Version 1.1 — Hardening & conversion hygiene

| Theme | Items | Label |
|-------|-------|-------|
| Naming | Dual-label marketing ↔ Tester/Standard/Premium | **Planned** |
| Copy | Remove stale free-trial language | **Planned** |
| SEO | Sitemap fix; index GTM pages only when live | **Planned** |
| Observability | Enable Sentry; consented analytics | **Planned** |
| CSP | Move from Report-Only after embed QA | **Planned** |
| Email | Periodic Resend inbox proof automation | **Planned** |
| Support | Light ticket CRM optional | **Aspirational** |
| Payments config API | Rename confusing `premium.priceUsd: 89` | **Planned** |

---

## Version 1.2 — Growth systems (after real cohort exists)

| Theme | Items | Label |
|-------|-------|-------|
| Affiliate | Live `/affiliate` + tracking when program real | **Planned** (page 404 today) |
| Partners | Partner resources + referral ops | **Planned** |
| BI | Founder metrics from ledger + analytics (no invented MRR) | **Planned** |
| Marketing automation | Lifecycle email (welcome, usage, renew) | **Planned** |
| Content | Blog depth per SEO cluster plan | **Planned** |
| Provider optionality | Lemon Squeezy cutover if chosen | **In repo** adapters; live cutover **Planned** |
| Status | Wire status cards to real probes | **Planned** |

---

## Version 2.0 — Scale & enterprise depth

| Theme | Items | Label |
|-------|-------|-------|
| Enterprise | SSO, seats, contracts, published SLA only if operable | **Aspirational** |
| API / developers | Public API beyond marketing page | **Aspirational** |
| Multi-region | Latency / data residency options | **Aspirational** |
| Team workspaces | Shared libraries, roles | **Aspirational** |
| Advanced identity | Stronger authorized continuity tooling | **Planned** / R&D |
| Compliance | SOC 2 / ISO only after real program — never claim early | **Aspirational** |
| Capital | Raise only with evidence — optional | **Aspirational** |

---

## Explicit non-promises

- No timeline guarantees without capacity.  
- No “enterprise ready” certification language without evidence.  
- No customer logos until real opted-in references.  
- No invented integration partnerships.

---

## Near-term engineering/business improvements (priority)

1. Clear C1/C2 (commerce + generation).  
2. Deploy or unpublish GTM routes; fix `/contact` and sitemap.  
3. Observability on.  
4. Naming + free-trial copy hygiene.  
5. Restore drill evidenced.  
6. Only then: paid acquisition experiments with measured CAC.

---

*Phase 13 Sprint 10 — Version Roadmap. Honest labels only.*
