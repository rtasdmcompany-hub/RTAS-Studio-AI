# Marketing — feature list & positioning

## Features

- Prompt-to-Video and Image-to-Video in one Studio
- Category wizard with cinematic presets
- Identity Preservation, avatar, and stylized visual modes
- Credit-metered generation (1 credit = 1 second)
- Dashboard: credits, queue, library, notifications
- Merchant of Record checkout (Paddle / Lemon Squeezy)
- Google + email authentication
- Public share links (same-origin media)
- Help Center + feedback capture
- Live chat FAQ on marketing surfaces

## Benefits

- Ship video without a traditional production crew
- Transparent cost model creators understand in seconds
- International tax-ready billing via MoR
- Enterprise-grade security posture (fail-closed webhooks, rate limits)

## Competitive advantages

| vs | Advantage |
|----|-----------|
| Generic AI toys | Full SaaS: billing, credits, library, support |
| Pure API tools | Guided Studio UX + dashboard |
| Local-only editors | Cloud GPU + fal pipeline |
| DIY Stripe stacks | MoR compliance out of the box |

## Enterprise features

- Admin fal-funding monitors (secret-gated)
- Health / readiness probes
- Documented DR, backup, security runbooks
- CSP Report-Only + security headers
- Workspace-ready monorepo

## AI capabilities

- Cloud render via fal.ai (primary)
- Optional Replicate / other keys via env
- Server-side FastAPI worker gateway

## Technical specifications

- Next.js 14 · Node 24 · Prisma · Postgres
- Vercel deploy target: `rtas-studio-ai-web`
- Redis/KV for serverless persistence + rate limits

## System requirements

- Modern Chromium / Safari / Firefox
- Account with verified email
- Optional: GPU worker URL for live generation

## Security highlights

- NextAuth sessions · email verification enforced on APIs
- Signed payment webhooks · no unsigned production accepts
- Upload magic-byte validation · share URL allowlist
- Secrets only via env templates (never hardcoded)

## Performance highlights

- Dynamic imports for heavy modals
- Compressed responses · static asset caching
- Dashboard skeletons + EmptyState clarity
