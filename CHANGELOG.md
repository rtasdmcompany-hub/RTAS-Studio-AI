# Changelog

All notable changes to RTAS Studio AI are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-07-21

### Production freeze — Release Candidate 2 (RC-2)

#### Added
- Forgot-password / reset-password flow with HMAC-signed tokens and Resend delivery
- Admin operations dashboard (`/admin`) with live Prisma metrics and analytics API
- Login activity audit trail (`SystemLog`)
- Live status probes on `/status`
- Web app manifest (`site.webmanifest`)
- Global 500 error boundary (`global-error.tsx`)
- Production SEO: `robots.ts`, `sitemap.ts`, OG image, canonical apex domain
- Refund policy page for MoR compliance

#### Security
- www → apex permanent redirect (middleware + vercel.json + next.config)
- HSTS, security headers, API `X-Robots-Tag: noindex`
- Admin routes noindex + no-store cache headers
- Rate limiting on auth, password reset, generate, and webhook paths
- Fail-closed Paddle webhook signature verification in production

#### Fixed
- Supabase pooler connectivity for Vercel serverless
- Resend domain verification path for `rtasstudio.com`
- Production robots.txt / sitemap.xml 404 (undeployed metadata routes)

#### Known limitations
- See `docs/KNOWN_LIMITATIONS.md`
- Paddle live checkout requires seller-account checkout enablement
- Fal.ai live generation requires wallet balance

### Prior (RC-1 and earlier)
- NextAuth credentials + Google OAuth with email verification
- Studio generation pipeline (Fal primary) with credit metering
- Profile dashboard, credits, job progress UI
- Merchant of Record billing scaffolding (Paddle / Lemon Squeezy)
- Phase 10 fail-closed backend auth migration

[1.0.0]: https://github.com/rtasdmcompany-hub/RTAS-Studio-AI/releases/tag/v1.0.0
