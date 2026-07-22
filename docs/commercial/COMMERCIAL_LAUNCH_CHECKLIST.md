# Phase 12 · Sprint 1 — Commercial Launch Checklist

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Sprint:** Phase 12 · Sprint 1 — Commercial Launch Foundation  
**As-of:** 23 July 2026  
**Constraint:** Launch-readiness audit & documentation only — **no application redesign**, no experimental features  

**Integrity:** Distinguishes **Verified** (live/code confirmed) · **Partial** · **Blocked** · **Planned**. Does not invent customers, revenue, logos, testimonials, or certifications.

---

## 1. Executive snapshot

| Area | Status | Notes |
|------|--------|-------|
| Marketing surfaces (HTTP) | **Verified** | Core pages return **200** on production |
| Auth journey routes | **Verified** | Signup / login / forgot / reset / check-email **200** |
| Legal suite | **Verified** | Terms, Privacy, Refund, Cookies, AI Policy, Trust & Safety **200** |
| SEO shell | **Verified** | robots, sitemap, OG image, canonical helper, manifest **200** |
| Fake social proof | **Verified clean** | No fake testimonials, logo walls, or fake counters found |
| `/contact` alias | **Blocked (404)** | Use `/help/contact` or `/support` (redirect) |
| Live Paddle checkout E2E | **Blocked / unverified** | Code fail-closed; production E2E purchase + credit grant **not proven** this sprint |
| Live generation | **Risk / historically blocked** | Prior Phase 10: Fal `live_generation: false` — re-confirm before paid ads |

---

## 2. Homepage review

| Check | Result | Evidence |
|-------|--------|----------|
| Brand hero present | **Pass** | `apps/web/src/app/page.tsx` — brand, headline, support, CTAs |
| Primary CTA | **Pass** | “Start creating” → `/studio` (auth gate via middleware) |
| Pricing CTA | **Pass** | “View pricing” → `/pricing` |
| Secondary discovery | **Pass** | Features / showcase / category paths linked |
| Pricing numbers visible | **Pass** | `$5` / `$89` / `$249` from `@rtas/shared` |
| Plan **marketing names** | **Partial** | “Creator Starter / Pro Studio / Production Enterprise” vs product **Tester / Standard / Premium** |
| Trust signals | **Partial** | Capability badges (`SITE_TRUST_BADGES`) — not customer logos; includes soft claims (“Enterprise Ready”, “99.9% Availability”) |
| Fake testimonials / logos / counters | **Pass** | Not found |
| Placeholder / dead CTAs (`href="#"`) | **Pass** | Not found on homepage |
| Production HTTP | **Pass** | `GET https://rtasstudio.com/` → **200** |

---

## 3. User journey (customer perspective)

```
Visitor → Homepage → Pricing / Features / Showcase
       → Signup → Check email → Verify → Login
       → Profile / Studio (0 credits if unpaid)
       → Pricing / Profile checkout CTA
       → Paddle MoR checkout  ← CRITICAL GATE
       → Webhook credit grant → Generate → Support/Legal
```

| Step | Route(s) | Prod HTTP | Assessment |
|------|----------|-----------|------------|
| Land | `/` | 200 | Clear product story |
| Understand pricing | `/pricing` | 200 | Numbers correct; naming split Partial |
| Sign up | `/auth/signup` | 200 | Present |
| Email verify UI | `/auth/check-email` | 200 | Present; delivery depends on Resend |
| Login | `/auth/login` | 200 | Credentials + optional Google |
| Forgot / reset | `/auth/forgot-password`, `/auth/reset-password` | 200 | Present |
| Dashboard | `/profile` | 200 | Protected; credits / plan CTAs |
| Studio | `/studio` | 200 | Protected |
| Checkout | `POST /api/checkout` | N/A (API) | Fail-closed **503** if live Paddle not configured |
| Support | `/help`, `/help/contact`, `/support`→contact | 200 | Mailto + Discord; no ticket backend |
| Legal | `/terms` … `/trust-safety` | 200 | Complete suite |

---

## 4. Conversion funnel

| Stage | Definition | Launch-ready? |
|-------|------------|---------------|
| Awareness | Organic / direct / OG share → homepage | **Yes** (SEO shell live) |
| Consideration | Features, showcase, how-to-use, pricing | **Yes** (pages live; some hubs thin) |
| Signup | Auth register + verify | **Yes** (UI); email deliverability must stay green |
| Activation | First dashboard visit; understand 0 credits + Tester entry | **Partial** — dashboard copy OK; marketing “free trial” remnants confuse |
| Purchase | Tester $5 / Standard $89 / Premium $249 via Paddle | **No — not E2E verified** |
| Retention | Credits → generate → return | Depends on purchase + live generation |

**CTA placement**

| Surface | CTAs | Working links? |
|---------|------|----------------|
| Homepage hero | Studio, Pricing | Yes |
| Homepage pricing teaser | Plan cards → pricing | Yes |
| Pricing page | Checkout per plan (`startCheckout`) | Wired; live MoR unproven |
| Profile / Studio paywall | Tester / Standard / Premium | Wired; same gate |
| Footer | Legal, Help, Social | Mostly yes; Discord invite unverified |

---

## 5. Pricing visibility

| Fact | Value | Status |
|------|-------|--------|
| Tester | $5 · 30 seconds · 5 days | **Verified** in shared constants + UI numbers |
| Standard | $89/mo · 2000 seconds | **Verified** |
| Premium 4K | $249/mo · 2000 seconds | **Verified** |
| Credit model | 1 credit = 1 second | **Verified** |
| MoR | Paddle | **Verified** provider; enablement/E2E **Partial/Blocked** |
| Marketing names | Creator Starter / Pro Studio / Production Enterprise | **Partial** — diverge from Tester/Standard/Premium used in product/paywall |
| Free plan | 0 starting credits | **Verified** product truth; some help/how-to copy still implies free trial |

---

## 6. Trust signals

| Signal | Status | Note |
|--------|--------|------|
| Live legal policies | **Pass** | Footer + dedicated pages |
| Trust & Safety / AI Policy | **Pass** | AUP / Identity Preservation posture |
| Merchant of Record language | **Pass** | Pricing / refund reference Paddle |
| Customer logos | **None claimed** | Correct |
| Testimonials | **None fabricated** | Correct |
| Counters (users/MRR) | **None fabricated** | Correct |
| “Enterprise Ready” / “99.9% Availability” | **Soft claim** | Capability marketing — not audited SLA |
| Status page | **Partial** | Page live; treat “all green” as operational messaging, not certified uptime |
| Discord community | **Unverified invite** | `discord.gg/rtas` — do not rely until validated |

---

## 7. Legal visibility

| Page | Path | Prod |
|------|------|------|
| Terms of Service | `/terms` | 200 |
| Privacy Policy | `/privacy` | 200 |
| Refund Policy | `/refund` | 200 |
| Cookie Policy | `/cookies` | 200 |
| AI Usage Policy | `/ai-policy` | 200 |
| Trust & Safety | `/trust-safety` | 200 |

Footer legal links present via shared site link config. Legal Documentation Sign-Off v1.1 remains the governance anchor (`docs/LEGAL_DOCUMENTATION_SIGNOFF.md`).

---

## 8. Support visibility

| Channel | Path / address | Status |
|---------|----------------|--------|
| Help hub | `/help` | 200 |
| Contact | `/help/contact` | 200 |
| Support alias | `/support` → `/help/contact` | 200 |
| Bare `/contact` | — | **404** — real gap |
| Emails | contact@ · support@ · info@ @rtasstudio.com | Configured in `site-links.ts` |
| Feedback | `/feedback` | 200 (mailto handoff) |
| Live chat widget | In-app | Scripted FAQ replies — not a human ticket system |

---

## 9. Brand consistency

| Item | Status |
|------|--------|
| Product name RTAS Studio AI | Consistent on marketing/auth |
| Operator RTAS Digital Marketing Company | Consistent in Phase 11/12 docs; site footers |
| Apex URL https://rtasstudio.com | Canonical |
| Identity Preservation (authorized only) | Consistent positioning |
| Plan naming (marketing vs product) | **Inconsistent** — fix in Sprint 2 copy pass |
| Logo assets on prod | `rtas-favicon.png`, `rtas-logo.png`, `logo.svg`, `og-image.png` → **200**; local `apps/web/public/` tree is thin (SVG + OG + manifest) — keep deploy assets in sync |
| `logo.png` | **404** on prod (path not used as primary brand mark) |

---

## 10. Enterprise readiness (honest)

| Expectation | Reality |
|-------------|---------|
| Self-serve SaaS studio | Strong |
| Transparent credits | Strong |
| SSO / SAML | Not a launch claim |
| MSA / custom SLA | Not proven |
| Dedicated success / SOC 2 | Not claimed |
| “Production Enterprise” plan name | Packaging only — not enterprise sales motion |

**Enterprise score remains early-stage.** Do not sell “Enterprise Ready” as certified compliance.

---

## 11. SEO & metadata verification

| Asset | Status | Evidence |
|-------|--------|----------|
| `robots.ts` | **Pass** | Allows public; disallows `/api/`, `/auth/`, `/studio`, `/profile`, `/admin`, `/share/` |
| `sitemap.ts` | **Pass** | Indexable marketing/legal/help paths; apex `https://rtasstudio.com` |
| Canonical helper | **Pass** | `site-url.ts` / `site-metadata.ts` |
| Open Graph | **Pass** | Title/description/image via shared metadata; `/og-image.png` **200** |
| Twitter cards | **Pass** | `summary_large_image` + `@RTASDigital` |
| Favicon | **Pass (prod)** | `/rtas-favicon.png` + `/favicon.ico` **200** |
| Manifest | **Pass** | `/site.webmanifest` **200** (icon → `/logo.svg`) |
| Structured metadata | **Partial** | Strong page metadata; do not claim full Organization/Product JSON-LD coverage without separate audit |

Prod spot-check (23 Jul 2026): `robots.txt`, `sitemap.xml`, `site.webmanifest`, `og-image.png`, favicons → **200**.

---

## 12. Checkout / subscription / credits

| Check | Status |
|-------|--------|
| Pricing UI plans | Present |
| Profile subscription CTAs | Present (Tester / Standard / Premium labels) |
| `POST /api/checkout` | Implements Paddle transaction API + static URL fallback; production **503** if neither configured |
| `/api/payments/config` | Provider `paddle`; `clientToken` **non-null** on prod (as of this audit) |
| Webhook credit grant | Code present; historically deferred without `PADDLE_WEBHOOK_SECRET` — **re-verify live** |
| Demo checkout in production | Disabled by design (good) |

---

## 13. Performance (foundation view)

| Check | Status |
|-------|--------|
| Core routes respond | **Pass** (200s observed) |
| Full Lighthouse / Core Web Vitals campaign | **Not run this sprint** — defer to Sprint 2+ measurement |
| Showcase media | Marketing depends on showcase assets; treat broken media as High if users see empty hero |

---

## 14. Sprint 1 scores (honest)

| Score | Value | Band |
|-------|------:|------|
| **Commercial Readiness** | **70** | B− |
| **Launch Readiness** | **62** | C+ |
| **Customer Journey** | **74** | B |
| **Trust Score** | **58** | C+ |
| **Enterprise Score** | **42** | D+ / early |
| **Overall (foundation)** | **64** | C+ |

### Overall verdict

# READY WITH MINOR FIXES

Foundation surfaces, legal, auth routes, and SEO shell are sufficient to proceed into **Sprint 2** (payments hardening, copy alignment, contact alias, claim hygiene). **Public paid acquisition must not scale** until Critical blockers in [`LAUNCH_BLOCKERS.md`](./LAUNCH_BLOCKERS.md) are cleared.

---

## 15. Related documents

| Doc | Path |
|-----|------|
| Launch blockers | [`LAUNCH_BLOCKERS.md`](./LAUNCH_BLOCKERS.md) |
| First customer readiness | [`FIRST_CUSTOMER_READINESS.md`](./FIRST_CUSTOMER_READINESS.md) |
| Phase 11 handover | [`../business/PHASE12_HANDOVER.md`](../business/PHASE12_HANDOVER.md) |
| Prior commercial note | [`../launch/COMMERCIAL-READINESS.md`](../launch/COMMERCIAL-READINESS.md) |

---

*Phase 12 Sprint 1 — Commercial Launch Foundation checklist. No score inflation.*
