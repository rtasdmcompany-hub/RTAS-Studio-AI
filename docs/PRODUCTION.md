# Production operations overview — RTAS Studio AI

Commercial production posture for the web application and its dependencies.

---

## Product surface

- **App:** Next.js 14 (`apps/web`) on Vercel
- **Auth:** NextAuth (credentials + Google) — not Supabase Auth
- **Data:** Prisma → Postgres (Supabase/Neon)
- **Payments:** Paddle (default) or Lemon Squeezy
- **Email:** Resend (preferred) or SMTP
- **Generation:** FastAPI worker + fal.ai / Replicate

---

## Production readiness gates

Before calling a release “production”:

| Gate | Command / check |
|------|-----------------|
| Lint | `npm run lint -w @rtas/web` |
| Types | `npm run typecheck -w @rtas/web` |
| Smoke | `npm run test -w @rtas/web` |
| Env checklist | `npm run verify:production -w @rtas/web` (without `RTAS_ALLOW_INCOMPLETE_ENV`) |
| Live probes | `npm run probe:services -w @rtas/web` |
| Build | `npm run build -w @rtas/web` |
| Health | `GET /api/health` → 200 |
| Ready | `GET /api/ready` → 200 |

Full checklist: [RELEASE-CHECKLIST.md](./RELEASE-CHECKLIST.md).

---

## Runtime fail-closed behavior

| Condition | Behavior |
|-----------|----------|
| Missing `NEXTAUTH_SECRET` in production runtime | Auth fails closed |
| Missing `FASTAPI_URL` in production | Generation APIs return configuration error |
| Missing Paddle webhook secret (provider=paddle) | Webhook verify fails closed |
| Demo checkout in production | Returns 503 |
| OAuth email account linking | Dangerous linking disabled; password accounts protected |

Boot validation: `apps/web/src/instrumentation.ts` → `validateProductionServerEnv()`.

---

## Environment

- Templates: `apps/web/.env.example`, `apps/web/.env.production.example`
- Matrix: [ENVIRONMENT.md](./ENVIRONMENT.md)
- Domains/placeholders: [INFRASTRUCTURE.md](./INFRASTRUCTURE.md)

Until real domain/credentials exist, keep placeholders (`REPLACE_*`). Do not block engineering on missing external accounts.

---

## Security baseline

See [SECURITY.md](./SECURITY.md). Highlights:

- Security headers in `vercel.json` (HSTS, frame deny, nosniff, referrer, permissions)
- API `Cache-Control: no-store`
- Secrets only in Vercel / `.env.local` (gitignored)
- Rotate any secret exposed in chat or tickets

---

## Monitoring

| Signal | Endpoint / sink |
|--------|-----------------|
| Liveness | `GET /api/health` |
| Readiness | `GET /api/ready` |
| Auth/runtime flags | `GET /api/auth/config` |
| Email mode | `GET /api/auth/email-config` |
| Payments config | `GET /api/payments/config` |
| Structured logs | `apps/web/src/lib/observability.ts` |
| Sentry / analytics | Env placeholders — wire when accounts ready |

---

## Change management

1. PR → CI green (`ci-web.yml`).
2. Merge to protected `main`/`master`.
3. Vercel production deploy (auto or manual).
4. Smoke `/api/health`, `/api/ready`, critical user paths.
5. On failure → [RECOVERY.md](./RECOVERY.md).

---

## What is intentionally deferred

These are **external** and do not block “deployment-ready” engineering:

- Final production domain + DNS
- Paddle production account + live checkout URLs
- Resend verified production domain
- Public GPU endpoint (`FASTAPI_URL` HTTPS)
- Sentry / PostHog accounts
- CDN hostname

When they arrive, follow the 30-minute path in [DEPLOYMENT.md](./DEPLOYMENT.md).
