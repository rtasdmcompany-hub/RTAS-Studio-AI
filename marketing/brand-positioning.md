# RTAS Studio AI — Brand Positioning

**Phase:** 13 · Sprint 1 · Global Brand Positioning  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan) · RTAS brand ecosystem  
**Integrity:** No invented customers, revenue, rankings, partnerships, certifications, or awards.  
**Billing note:** Merchant of Record has historically been Paddle; migration may be in progress — do not invent live payment status.

---

## 1. Homepage messaging audit (Sprint 1)

### Sources reviewed

| Source | Path |
|--------|------|
| Hero + outcomes copy | `apps/web/src/lib/landing-copy.ts` |
| Homepage composition | `apps/web/src/app/page.tsx` |
| Trust badge labels | `apps/web/src/lib/site-links.ts` |
| Prior messaging | `docs/branding/MESSAGING_FRAMEWORK.md`, `docs/branding/BRAND_STRATEGY.md` |
| Prior positioning | `business/company/PRODUCT_POSITIONING.md`, `business/company/USP.md` |
| Landing guide | `docs/marketing/LANDING-MESSAGING.md` |

### Findings

| Area | Assessment | Action |
|------|------------|--------|
| Brand-first hero | **Strong** — `RTAS STUDIO AI` leads before headline | Keep |
| Identity posture | Headline said “identity consistency” without **Authorized** framing; risk of deepfake adjacency | **Fixed** — Authorized Identity Preservation in hero |
| Value clarity | Credits (1 = 1s), compose→render→publish, commercial exports — clear | Keep |
| MoR / checkout language | “Global checkout” / “worldwide” risked implying fully settled commerce | **Softened** — credit clarity over checkout geography |
| Trust badges | “Enterprise Ready” and “99.9% Availability” overclaimed early-stage maturity / unverified SLA | **Softened** — team-ready + monitored hosting |
| Audience map | Artists, brands/agencies, creators/studios — aligned to ICP | Keep |
| Fake social proof | No invented customer logos or counters on homepage | Keep |
| Anti-deepfake | Support and outcomes now explicitly authorized / not face-swap | Keep |

### Minimal copy files changed this sprint

- `apps/web/src/lib/landing-copy.ts`
- `apps/web/src/app/page.tsx`
- `apps/web/src/lib/site-links.ts` (trust badge labels only)

---

## 2. One consistent value proposition

**Canonical value proposition (use everywhere):**

> RTAS Studio AI is the international AI video studio that helps creators, agencies, and marketing teams produce commercials, music videos, and stories with **Authorized Identity Preservation**, transparent second-based credits (**1 credit = 1 second**), and a clear path from Tester to Standard HD to Premium 4K.

**Short form (ads / social):**

> Cinematic AI video with authorized identity consistency — priced by the second.

---

## 3. Positioning statement

**External (primary):**

> For creators, agencies, and marketing teams who need professional AI video faster than traditional production, **RTAS Studio AI** is the **trust-forward international AI video studio** that delivers multi-format generation with **Authorized Identity Preservation** and **transparent second-based credits** — so teams can evaluate on Tester ($5 / 30s / 5 days), ship on Standard ($89/mo / 2000s), or go cinematic on Premium ($249/mo / 2000s).

**Anti-positioning (never claim):**

- Face-swap platform · deepfake tool · “#1 AI video” · model parity with Veo / Runway / Kling · fabricated traction or awards

**Category:** Generative AI video studio / commercial creative SaaS  
**Differentiation axis:** Authorized identity + studio packaging + credit clarity + operator marketing DNA — **not** “we own the best closed model.”

---

## 4. Brand architecture

| Layer | Name | Role |
|-------|------|------|
| Ecosystem | **RTAS** | Parent brand umbrella |
| Operator | **RTAS Digital Marketing Company** | Legal/commercial operator; Pakistan base; global digital distribution |
| Product | **RTAS Studio AI** | Customer-facing product at rtasstudio.com |

**Naming rule:** Lead with **RTAS Studio AI** in product marketing; cite the operator in legal, about, investor, and partner contexts.

---

## 5. Message house

| Level | Line |
|-------|------|
| **Category** | International AI video studio |
| **Primary benefit** | Ship commercials, music videos, and stories faster with clear credit economics |
| **Differentiator** | Authorized Identity Preservation + trust/legal packaging + marketing-operator empathy |
| **Proof today** | Live product, published pricing, legal suite, Identity Preservation framing |
| **Proof not yet** | Named customer logos, audited ARR, press awards, verified SLA marketing |

---

## 6. Investor-ready positioning (honest)

### Narrative (approved facts only)

RTAS Studio AI is an early-stage international AI video SaaS operated by RTAS Digital Marketing Company from Pakistan within the RTAS brand ecosystem. The product sells studio generation for commercials, music videos, animation, and brand storytelling with a published seconds-based credit model (1 credit = 1 second):

| Plan | Price | Capacity |
|------|-------|----------|
| Tester | $5 (one-time window) | 30 seconds · 5 days |
| Standard | $89 / month | 2,000 seconds |
| Premium 4K | $249 / month | 2,000 seconds |

**Strategic wedge:** Trust-forward commercial packaging — Authorized Identity Preservation (not deepfake/face-swap marketing), transparent metering, and live policy surfaces — aimed at creators, agencies, and marketing teams underserved by novelty clip apps and by enterprise avatar suites optimized for talking-head L&D.

**MoR:** Checkout architecture has historically used Paddle as Merchant of Record; do not assert global payment completion or invent migration outcomes in investor materials.

**What investors should not hear:** Fabricated MAU/ARR, Fortune-500 logos, “SOTA vs Veo/Kling,” or awards that do not exist.

### Investment thesis framing (hypothesis — labeled)

| Thesis element | Status |
|----------------|--------|
| Category growth in generative video | Market hypothesis |
| Trust / AUP-aligned studio wedge | Positioning hypothesis with product + legal proof |
| Clear land-and-expand ladder ($5 → $89 → $249) | Verified packaging |
| Marketing-company distribution intuition | Operator fact; GTM results not invented |
| Traction metrics | Disclose only when finance verifies |

### Elevator (investor, ~30s)

Early-stage AI video studio SaaS from RTAS Digital Marketing Company. We package commercial generation with authorized identity consistency and second-based credits — Tester at $5, Standard at $89/mo, Premium 4K at $249/mo. We compete on trust posture and studio packaging for marketing buyers, not on claimed frontier-model ownership or undisclosed traction.

---

## 7. Tone of voice (summary)

Confident · precise · cinematic · international SaaS — not hype-bro, not academic whitepaper, not deepfake-adjacent.

Full verbal + visual system: [`enterprise-brand-guide.md`](./enterprise-brand-guide.md) · Mission/vision: [`mission-vision.md`](./mission-vision.md) · USP: [`unique-selling-proposition.md`](./unique-selling-proposition.md).

---

*Phase 13 Sprint 1 — positioning documentation readiness, not a claim of category leadership.*
