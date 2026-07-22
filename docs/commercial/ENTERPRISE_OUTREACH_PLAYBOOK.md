# Enterprise Outreach Playbook — RTAS Studio AI

**Phase:** 12 · Sprint 8  
**Product:** https://rtasstudio.com  
**Public surface:** `/enterprise`  
**Integrity:** No fake enterprise clients, logos, case studies, or revenue claims.

---

## Goal

Convert serious brand/agency interest into demos, proposals, or meetings while self-serve plans remain available on `/pricing`.

## Entry points

| Source | Path |
|--------|------|
| Header nav | Enterprise |
| Homepage final CTA | Enterprise |
| Pricing final CTA | Enterprise contact |
| Customer Success hub | `/help` → Enterprise sales |
| Footer | Product → Enterprise |
| Direct | `/enterprise#contact` |

## Request types (form)

- **Demo** — product walkthrough
- **Proposal** — commercial terms / procurement
- **Meeting** — discovery call

All submit to `POST /api/commercial/lead` (`kind: "enterprise"`).

## Discovery checklist (operator)

1. Company, role, markets, timeline  
2. Identity Preservation needs (authorized likeness?)  
3. Volume estimate (seconds / month)  
4. Plan fit: Standard $89 vs Premium $249 vs custom (case-by-case only)  
5. Blockers: Paddle live checkout, Fal wallet (do not promise what infra cannot deliver)

## Security talking points (honest)

- TLS in transit; secrets server-side  
- Fail-closed payment webhooks; rate limits  
- No SOC 2 / ISO claims unless independently attested  
- Point to `/trust-safety` and `/privacy`

## Deployment talking points

- Default: SaaS at rtasstudio.com  
- Custom SLA / dedicated infra: discuss only — do not advertise as shipped  
- Parallel self-serve: Tester $5 or Standard while scoping

## Follow-up cadence

| Day | Action |
|-----|--------|
| 0 | Auto email to contact@ (when delivery configured) |
| 1–2 | Human reply with calendar options or questions |
| 7 | Nudge if no reply |
| 30 | Close or nurture — no fabricated pipeline stages in public |

## Related docs

- `docs/business/sales/Enterprise-Sales-Process.md`
- `docs/business/sales/Enterprise-Demo-Script.md`
- `docs/business/sales/Enterprise-Proposal-Template.md`
- `docs/growth/ENTERPRISE_EXPANSION_PLAN.md`
