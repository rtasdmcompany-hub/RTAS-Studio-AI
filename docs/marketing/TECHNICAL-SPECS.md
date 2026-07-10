# Technical specifications — RTAS Studio AI

## Application

| Item | Spec |
|------|------|
| Web app | Next.js 14, React 18, TypeScript |
| Hosting | Vercel (`rtas-studio-ai-web`) |
| Auth | NextAuth (credentials + Google OAuth) |
| Database | Prisma → Postgres (Supabase/Neon) |
| Persistence | Vercel KV / Upstash Redis |
| Payments | Paddle or Lemon Squeezy (MoR) |
| Email | Resend or SMTP |
| AI generation | FastAPI GPU worker + fal.ai (and alternatives) |

## Client requirements

| Item | Requirement |
|------|-------------|
| Browser | Latest Chrome, Edge, Firefox, Safari |
| Network | HTTPS; stable connection for uploads |
| Account | Verified email (or Google) |
| Mobile | Responsive web; native shells optional |

## Security highlights

- Session-guarded Studio APIs; email verification enforced
- Signed payment webhooks (fail closed)
- Rate limiting (Redis when configured)
- Upload MIME + magic-byte checks
- Share URL allowlist
- Security headers + CSP Report-Only
- No card data on RTAS servers

## Performance highlights

- Compressed responses; static asset caching
- Dynamic modal code-splitting in Studio
- Server-side generation gateway (no client GPU bypass)
- Health `/api/health` and readiness `/api/ready`

## System limits (product)

- Upload size capped server-side (see upload guard)
- Concurrent render slots per account
- Credit-based duration metering

Credentials and production domains are configured via environment placeholders — never hardcoded.
