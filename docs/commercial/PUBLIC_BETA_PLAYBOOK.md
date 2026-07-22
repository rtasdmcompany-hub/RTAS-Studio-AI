# Public Beta Playbook — RTAS Studio AI

**Phase:** 12 · Sprint 8  
**Product:** https://rtasstudio.com  
**Public surface:** `/beta`  
**Integrity:** No fake waitlists, seats, acceptance rates, or beta user counts.

---

## Goal

Recruit early creators and teams who will evaluate Studio honestly and send actionable feedback — without overselling capacity or inventing social proof.

## Eligibility (public copy)

- Creators, freelancers, agencies, brands with a real use case
- Willingness to give feedback via `/feedback` or support email
- Acceptance of Terms + Privacy at application time
- Authorized rights for any Identity Preservation / likeness materials

## Application flow

1. Visitor lands on `/beta` (footer Product column, Customer Success hub, SEO sitemap).
2. Reads overview, eligibility, features, limitations, privacy/terms.
3. Submits **Apply for Beta** form → `POST /api/commercial/lead` (`kind: "beta"`).
4. API validates fields + terms acceptance; rate-limits by IP.
5. On success: Resend/SMTP notifies `contact@rtasstudio.com`.
6. On missing email config: **503** with honest `EMAIL_NOT_CONFIGURED` + mailto fallback.

## Operator response (recommended)

| Step | Action | SLA (aspirational) |
|------|--------|--------------------|
| 1 | Acknowledge application | 2 business days |
| 2 | Confirm use case + rights | Same thread |
| 3 | Invite to Tester/Standard if checkout live | When C1 cleared |
| 4 | Log feedback themes | Weekly review |

Do **not** publish “X beta users” unless measured from real accounts.

## Messaging rules

- State known limits (Paddle enablement, Fal wallet) — see `docs/KNOWN_LIMITATIONS.md`.
- Identity Preservation = **authorized only**.
- Pricing remains Tester $5 · Standard $89 · Premium $249.

## Metrics (honest)

Track only real data: applications received, replies sent, accounts created, successful renders. Never invent conversion rates for decks.
