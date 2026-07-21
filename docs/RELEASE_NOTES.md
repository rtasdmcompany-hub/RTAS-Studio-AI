# Release Notes — RTAS Studio AI v1.0.0

**Codename:** RC-2 Production Freeze  
**Build:** `20260721.1`  
**Date:** 21 July 2026  
**Production:** https://rtasstudio.com  

---

## Highlights

RTAS Studio AI **v1.0.0** is the first production freeze of the international AI video SaaS platform:

- Compose → Render → Publish studio with identity lock and transparent credits (1 credit = 1 second)
- Email + Google authentication, email verification, and password reset via Resend
- Merchant-of-Record billing scaffolding (Paddle) with webhook-driven credit grants
- Admin operations dashboard with live database metrics
- Production SEO (canonical apex domain, robots, sitemap, Open Graph, JSON-LD)

## Plans

| Plan | Price | Credits |
|------|-------|---------|
| Tester | $5 | 30 seconds (5 days) |
| Standard | $89/mo | 2000 seconds |
| Premium 4K | $249/mo | 2000 seconds cinematic |

## What customers can do

1. Sign up / sign in (email or Google)
2. Confirm email and reset forgotten passwords
3. Open Studio, generate videos against credit balance
4. Track jobs (queued → completed / failed) with progress and ETA
5. Manage profile credits and subscription state after webhook activation

## Operator notes

- Admin UI: `/admin` (requires `RTAS_ADMIN_SECRET`)
- Health: `/api/health`, `/api/ready`, `/status`
- Docs: `CHANGELOG.md`, `docs/KNOWN_LIMITATIONS.md`, `docs/SECURITY.md`

## Upgrade / deploy

Push to `master` triggers Vercel production deploy for `rtas-studio-ai-web`.  
Tag: `v1.0.0`.

## Deferred (not blockers for soft launch)

See `docs/KNOWN_LIMITATIONS.md` — primarily Paddle checkout enablement and Fal wallet funding.
