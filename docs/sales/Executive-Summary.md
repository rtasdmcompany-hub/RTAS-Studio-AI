# RTAS Studio AI — Executive Summary

**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**Product:** RTAS Studio AI · https://rtasstudio.com  
**Document class:** Investor / enterprise sales — Phase 11 Sprint 2  
**Fact policy:** Verified product and legal facts only; no invented traction, MRR, or user counts.

---

## What it is

RTAS Studio AI is a cloud AI video studio that turns text prompts and images into finished video for music videos, commercials, social content, animation, and brand campaigns. It is positioned as a full SaaS product—guided Studio UX, credit metering, dashboard, library, auth, and Merchant of Record billing—not a raw model API.

**Identity Preservation** keeps likeness continuity for **original, licensed, owned, or authorized** content only. Public positioning is Paddle Acceptable Use Policy (AUP) compliant: no face-swapping, celebrity impersonation, or unauthorized deepfake framing.

Legal documentation **v1.1 is APPROVED** for production (Terms, Privacy, Refund, Cookies, AI Policy, Trust & Safety).

---

## Problems solved

| Buyer pain | How RTAS addresses it |
|------------|------------------------|
| Fragmented AI tools + editors | One Studio: prompt/image → generate → preview → library |
| Opaque GPU / API cost | **1 credit = 1 second**; clear Tester / Standard / Premium pools |
| Tax, invoices, card compliance | **Paddle** as Merchant of Record (checkout/domain activation may still be pending — honest) |
| Enterprise risk on likeness misuse | Authorized-content Identity Preservation + Trust & Safety / AI Policy |
| Building own render stack | Managed pipeline: Next.js app + FastAPI + Fal GPU |

---

## AI pipeline (verified architecture)

1. User selects mode (prompt or image), category, and visual style.  
2. Shared category validation and server-side credit/generation guards.  
3. Job queued (`QUEUED` → … → `COMPLETED` / `FAILED`).  
4. Fal.ai models routed by billing-tier cost policy; optional worker gateway via FastAPI.  
5. Studio polls progress/ETA; output stored and download entitlement applied.  

**Stack (verified):** Next.js (Vercel) · FastAPI · Prisma / Supabase Postgres · Fal GPU · Resend · Cloudflare DNS · Paddle MoR.

---

## Revenue model

| Plan | Price | Credits | Role |
|------|------:|--------:|------|
| Tester | **$5** (5 days) | **30 seconds** | Low-risk evaluation |
| Standard | **$89 / month** | **2,000 seconds** | Primary recurring plan |
| Premium | **$249 / month** | **2,000 seconds** (cinematic / 4K positioning) | Quality / priority upgrade |

Credit rule: **1 credit = 1 second** of generated video. Recurring SaaS subscriptions are the commercial core; MoR handles tax and invoicing once live checkout is fully activated.

**Verified:** Pricing constants and legal alignment.  
**Not claimed:** Live MRR, ARR, paid seats, or conversion rates (none invented).

---

## Competitive advantage

- **Product surface, not a toy:** Studio + Dashboard + credits + library + support, vs. single-model demos.  
- **Transparent economics:** Second-based credits buyers understand immediately.  
- **Compliance-first identity:** Identity Preservation under authorized-content policy; Paddle AUP-aligned public copy.  
- **Ops posture:** Auth, fail-closed webhooks pattern, health/readiness, security and DR documentation.  
- **RTAS brand ecosystem:** Operated by RTAS Digital Marketing Company with group brand continuity.

---

## Why enterprises buy

- Faster creative iteration without standing up a production crew or private GPU fleet.  
- Predictable monthly spend and auditable credit usage.  
- Merchant of Record checkout reduces buyer procurement friction on tax/invoicing (when Paddle live paths are fully enabled).  
- Clear Acceptable Use, Trust & Safety, and AI Policy for risk, legal, and brand teams.  
- Categories spanning commercials, social, music video, and animation in one workflow.

---

## Why investors like it

- **Category:** Generative video SaaS with subscription unit economics.  
- **Model clarity:** Metered usage tied to output seconds; upgradable tiers.  
- **Infrastructure leverage:** Cloud GPU via Fal rather than owning silicon on day one.  
- **Distribution-ready surface:** Marketing site, Studio, help, legal v1.1 approved.  
- **Honest stage:** Engineering and productization advanced; commercial go-live gated by external MoR/domain activation—not by inventing traction.

---

## Related materials

- [Pitch Deck](./Pitch-Deck.md) · [Product One-Pager](./Product-OnePager.md) · [Acquisition Memo](./Acquisition-Memo.md)  
- [Competitive Analysis](./Competitive-Analysis.md) · [Investor FAQ](./Investor-FAQ.md) · [Business Metrics](./Business-Metrics.md)  
- Cross-link (Sprint 1 readiness): [docs/business/](../business/) phase readiness notes  
- Sprint report: [PHASE11-SPRINT2-REPORT.md](../business/PHASE11-SPRINT2-REPORT.md)

---

*Classification legend used throughout this kit: **Verified fact** vs **Estimate / projection** (illustrative models with stated assumptions).*
