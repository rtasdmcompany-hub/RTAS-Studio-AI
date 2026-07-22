# Enterprise Sales Pipeline

**Product:** RTAS Studio AI  
**Operator:** RTAS Digital Marketing Company  
**Phase:** 12 · Sprint 7

## Surfaces

| Intent | Route | Form |
|--------|-------|------|
| Enterprise overview + inquiry | `/enterprise#contact` | `CommercialLeadForm` kind=`enterprise` |
| Schedule demo | `/demo` | Same API; `requestType=demo` |
| Request quote | `/enterprise` (select Quote) | `requestType=quote` |
| Proposal / meeting | `/enterprise` | `requestType=proposal` \| `meeting` |
| Sales email | `mailto:contact@rtasstudio.com` | Direct |

## Lead path (technical)

```
Form (validated) → POST /api/commercial/lead
  → rate limit 8/hour/IP
  → require company + requestType (demo|proposal|meeting|quote)
  → sendEmail() via Resend → SMTP → fail honestly if unconfigured
  → notify contact@rtasstudio.com
```

**No in-app CRM persistence.** Ops may copy leads into an external CRM (HubSpot/Pipedrive) — outside product scope.

## Recommended sales stages (ops)

1. **Inbound** — demo/enterprise/quote form or email  
2. **Qualify** — team size, use case, Identity Preservation needs, budget band  
3. **Demo** — 30–45 min Studio walkthrough (`/demo` expectations)  
4. **Propose** — Standard $89 or Premium $249 list; custom terms case-by-case only  
5. **Close** — self-serve Paddle checkout when MoR enabled, or assisted invoice process  
6. **Onboard** — `/profile` checklist → Studio → first export  

## Pricing anchors (public)

| Plan | Price | Credits |
|------|-------|---------|
| Tester | $5 one-time · 5 days | 30 seconds |
| Standard | $89/mo | 2000 seconds |
| Premium 4K | $249/mo | 2000 seconds |

1 credit = 1 second. Do not invent public discount schedules.

## Integrity

- No fake logos, case studies, SOC2 claims, or revenue figures.
- Security posture described honestly on `/enterprise` and `/trust-safety`.
