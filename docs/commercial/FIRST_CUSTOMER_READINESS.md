# Phase 12 · Sprint 1 — First Customer Readiness

**Product:** RTAS Studio AI · https://rtasstudio.com  
**Operator:** RTAS Digital Marketing Company (operating from Pakistan)  
**As-of:** 23 July 2026  
**Question:** Can a **real new visitor** become a successful first customer without inventing traction or redesigning the product?

**Companions:** [`COMMERCIAL_LAUNCH_CHECKLIST.md`](./COMMERCIAL_LAUNCH_CHECKLIST.md) · [`LAUNCH_BLOCKERS.md`](./LAUNCH_BLOCKERS.md)

---

## 1. Verdict for “first customer”

| Mode | Ready? | Meaning |
|------|--------|---------|
| **Founder-guided closed test** (you watch the journey) | **Conditional Yes** | Surfaces work; you can rescue email/checkout issues live |
| **Unguided public paid customer** | **Not yet** | Critical: checkout E2E + live generation unproven |
| **Paid ads / affiliates at scale** | **No** | Do not spend until C1/C2 cleared |

---

## 2. Evaluation questions

### Can a new visitor understand the product?

**Yes — with caveats.**

- Homepage presents brand, cinematic studio promise, Identity Preservation, credits (1 credit = 1 second), and pricing teaser.
- Features / Showcase / How-to-use deepen understanding.
- Caveat: marketing plan names (Creator Starter / Pro Studio / Production Enterprise) differ from product names (Tester / Standard / Premium), which can confuse support conversations.

### Can they sign up?

**Yes (UI verified).**

- `/auth/signup` returns **200**.
- Flow continues toward `/auth/check-email`.
- Google OAuth may be available when configured; credentials path exists.

### Can they verify email?

**Yes if Resend delivery works; UI ready.**

- `/auth/check-email` **200**.
- Delivery depends on production email (Resend / `auth@rtasstudio.com`). Treat as High operational dependency (H4), not a missing page.

### Can they access the dashboard?

**Yes after verified session.**

- `/profile` and `/studio` return **200** (auth-gated for real use).
- New unpaid users correctly see **0** credits and Tester as entry — do not promise free generation seconds.

### Can they understand pricing?

**Mostly yes.**

- `/pricing` **200**; dollar amounts match source of truth ($5 / $89 / $249).
- Profile/paywall uses Tester / Standard / Premium language.
- Confusion risk from dual naming + leftover free-trial copy (H2/H3).

### Can they complete checkout / get credits?

**Not proven.**

- Checkout API is implemented and fail-closed (good engineering hygiene).
- Production payments config shows Paddle provider and a client token present as of this audit.
- A live purchase → webhook → credit balance success path was **not** verified in Sprint 1.
- Until C1 is Cleared, the first customer may reach a dead end at pay.

### Can they generate a video after paying?

**Not proven (C2).**

- Historically Phase 10 reported live generation blocked (`live_generation: false`).
- Re-confirm after C1 before calling the product “commercially complete.”

### Can they contact support?

**Yes — with one gap.**

- `/help`, `/help/contact`, `/support` work (**200**).
- Emails: contact@ / support@ @rtasstudio.com.
- **`/contact` is 404** — common URL expectation fails (H1).
- Contact is mailto / Discord / FAQ — not a ticket desk (acceptable early).

### Can they trust the product?

**Partially.**

| Trust builder | Present? |
|---------------|----------|
| Live legal suite (Terms, Privacy, Refund, Cookies, AI Policy, Trust & Safety) | Yes |
| No fake testimonials / logos / counters | Yes (correct) |
| Transparent credits & MoR language | Yes |
| Soft unverifiable claims (99.9%, Enterprise Ready) | Present — weakens sophisticated buyers |
| Status / Discord | Soft / unverified elements |

Honest trust posture is stronger than fake social proof — keep it that way. Soften overclaims rather than invent logos.

---

## 3. Ideal first-customer path (when Critical cleared)

1. Land on https://rtasstudio.com  
2. Read pricing → understand Tester $5 entry  
3. Sign up → verify email → login  
4. Open Profile → start Tester checkout  
5. Pay via Paddle → credits appear  
6. Open Studio → generate short authorized clip  
7. Know where Help / Refund / Trust & Safety live  

Until steps 5–6 are proven in production, “first customer readiness” remains **conditional**.

---

## 4. Scores (honest)

| Score | Value | Band | One-line |
|-------|------:|------|----------|
| Commercial Readiness | **70** | B− | UI + pricing + MoR wiring; E2E pay unproven |
| Launch Readiness | **62** | C+ | Foundation surfaces strong; money/render gates open |
| Customer Journey | **74** | B | Understand → auth → dashboard works; pay/render gap |
| Trust Score | **58** | C+ | Legal strong; soft claims + thin social proof |
| Enterprise Score | **42** | Early | Self-serve SaaS, not enterprise motion |
| **First-customer readiness (unguided paid)** | **55** | C | Not ready for unguided paid public |
| **Foundation readiness (Sprint 1 goal)** | **72** | B− | Enough to enter Sprint 2 hardening |

---

## 5. Overall verdict

# READY WITH MINOR FIXES

**Interpretation:** Phase 12 Sprint 1 **foundation** is complete enough to start Sprint 2 commercial hardening. It is **not** a green light for unguided public paid acquisition.

**Before declaring first public customer success:** clear **C1** and **C2** in [`LAUNCH_BLOCKERS.md`](./LAUNCH_BLOCKERS.md), plus High items H1–H3 at minimum.

---

## 6. What “done” looks like for first customer

| Proof | Required evidence |
|-------|-------------------|
| Understand | Screenshot of homepage + pricing without contradictory free-trial claims |
| Signup + verify | Test inbox received verification mail |
| Dashboard | Logged-in profile shows 0 → then credits after pay |
| Checkout | Paddle receipt + matching credit ledger entry |
| Generate | One completed studio job on paid credits |
| Support | `/help/contact` (and `/contact` redirect) reachable |
| Trust | Legal pages linked; no fake logos added |

---

*First customer readiness — honest executive assessment. No score inflation.*
