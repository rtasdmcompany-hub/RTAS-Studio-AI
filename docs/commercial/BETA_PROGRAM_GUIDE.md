# Beta Program Guide

**Product:** RTAS Studio AI (`https://rtasstudio.com`)  
**Operator:** RTAS Digital Marketing Company  
**Public page:** `/beta`  
**Phase:** 12 · Sprint 7

## Purpose

Honest early access for creators and teams evaluating Identity Preservation video — not a fake waitlist, not invented capacity claims.

## What beta users receive

| Area | Details |
|------|---------|
| Studio | Full Compose → Render → Publish workflow |
| Credits | 1 credit = 1 second; published plans (Tester $5 / Standard $89 / Premium $249) |
| Identity Preservation | Authorized likeness only — rights required |
| Support | Help Center, `/feedback`, `contact@rtasstudio.com` |

## Known limitations

- Paid checkout depends on Merchant-of-Record (Paddle) enablement.
- Cloud GPU generation needs provider wallet balance; empty pool → queue/fail.
- Enterprise SSO, custom SLAs, dedicated VPC are **not** public beta features.
- No fake seat counts, logos, or acceptance-rate marketing.

## Feedback expectations

1. File Bug / Feature / General feedback via `/feedback` after first real use.
2. Share one concrete project outcome when possible.
3. Do not invent public testimonials; RTAS only publishes explicitly approved quotes.

## Support channels

- **Email:** contact@rtasstudio.com  
- **Feedback form:** `/feedback` → `POST /api/feedback` (Resend/SMTP when configured)  
- **Help:** `/help`, FAQ, troubleshooting, changelog  
- **Enterprise path:** `/enterprise` or `/demo` if the evaluation becomes a team purchase

## Application flow

1. User opens `/beta` and reviews eligibility, features, limitations, privacy.
2. Validated form (`CommercialLeadForm` kind=`beta`) requires use case + Terms/Privacy.
3. `POST /api/commercial/lead` emails the commercial inbox when delivery is configured.
4. If env missing → **503 `EMAIL_NOT_CONFIGURED`** with honest copy + mailto fallback.

## Privacy

Application data (name, email, use case) is used only to evaluate access and reply. See `/privacy`, `/terms`, `/ai-policy`.

## Integrity rules

- No fake customers, reviews, testimonials, or revenue claims tied to beta.
- Applications are **not** stored as CRM “customers” in-app — email notification only.
