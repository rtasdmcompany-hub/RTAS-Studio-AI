# Environment variables — RTAS Studio AI

Canonical reference for every configuration key used by `@rtas/web` and related tooling.

| Template | Purpose |
|----------|---------|
| `apps/web/.env.example` | Local development |
| `apps/web/.env.production.example` | Production / Vercel checklist |
| `apps/backend/.env.example` | FastAPI GPU worker |
| Root `.env.example` | Pointer only |

**Rules**

- Never commit `.env.local`, `.env`, or real secrets.
- Never hardcode secrets in source, docs, or CI logs.
- Prefer Vercel Dashboard or `npm run env:vercel -w @rtas/web` for production sync.
- Validate: `npm run verify:production -w @rtas/web` then `npm run probe:services -w @rtas/web`.

---

## Required for production (web)

| Variable | Required | Description | Example / placeholder |
|----------|----------|-------------|------------------------|
| `NEXTAUTH_SECRET` | **Yes** | NextAuth JWT/session signing | `openssl rand -base64 32` |
| `NEXTAUTH_URL` | **Yes** | Canonical HTTPS origin | `https://REPLACE_APP_DOMAIN` |
| `NEXT_PUBLIC_APP_URL` | **Yes** | Public app URL (must match domain) | `https://REPLACE_APP_DOMAIN` |
| `DATABASE_URL` | **Yes** | Prisma Postgres (pooled) | Supabase/Neon pooler URI |
| `FASTAPI_URL` | **Yes** | Server-side GPU worker base URL | `https://api.REPLACE_APP_DOMAIN` |
| `KV_REST_API_URL` + `KV_REST_API_TOKEN` | **Yes on Vercel** | Persistent store (or Upstash aliases) | Link Vercel KV |
| `PADDLE_WEBHOOK_SECRET` | **Yes if provider=paddle** | Webhook HMAC secret | From Paddle dashboard |
| Checkout URL(s) | **Yes if paddle** | At least one `NEXT_PUBLIC_PADDLE_*_CHECKOUT_URL` | Paddle payment link |
| `RESEND_API_KEY` or SMTP | **Yes** | Transactional email | Resend API key |
| `EMAIL_FROM` | **Yes** | Verified sender | `noreply@REPLACE_EMAIL_DOMAIN` |
| `FAL_KEY` (or other AI key) | **Yes for live gen** | Cloud renderer | fal.ai key |

---

## Auth (NextAuth + Google)

| Variable | Required | Notes |
|----------|----------|-------|
| `GOOGLE_CLIENT_ID` | Optional | `.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Optional | Server only |
| `NEXT_PUBLIC_GOOGLE_AUTH_ENABLED` | Optional | `false` disables Google button |
| `GOOGLE_OAUTH_REDIRECT_URI` | Recommended | Must match Google Cloud Console |
| `GOOGLE_OAUTH_JS_ORIGIN` | Recommended | Must match authorized JS origin |
| `GOOGLE_OAUTH_*_ALT` | Optional | www / preview aliases |
| `AUTH_GOOGLE_ID` / `AUTH_GOOGLE_SECRET` | Aliases | Accepted by `env.ts` |

---

## Database & Supabase

| Variable | Required | Notes |
|----------|----------|-------|
| `DATABASE_URL` | **Yes** | Prisma; prefer pooler + `sslmode=require` |
| `DATABASE_URL_DIRECT` | Optional | Direct host for migrations |
| `NEXT_PUBLIC_SUPABASE_URL` | Optional | REST/storage; **not** used for auth |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Optional | Publishable / anon JWT |
| `SUPABASE_SERVICE_ROLE_KEY` | Optional | Server only — never expose |

Auth model: **NextAuth + Prisma**, not Supabase Auth.

---

## Payments

| Variable | When | Notes |
|----------|------|-------|
| `NEXT_PUBLIC_PAYMENT_PROVIDER` | Always | `paddle` (default) or `lemon_squeezy` |
| `PADDLE_WEBHOOK_SECRET` | paddle | Fail-closed in production if missing |
| `NEXT_PUBLIC_PADDLE_CLIENT_TOKEN` | paddle | Client token |
| `NEXT_PUBLIC_PADDLE_*_CHECKOUT_URL` | paddle | Tester / Standard / Premium links |
| `PADDLE_*_PRICE_ID` | Optional | Price IDs if used |
| `LEMONSQUEEZY_*` | lemon_squeezy | Webhook + store + variants + checkout URLs |
| `FAL_ADMIN_API_KEY` | Optional | Post-payment fal balance monitor |
| `FAL_USD_PER_CREDIT` | Optional | Default `0.0195` |
| `FAL_POOL_BUFFER_PERCENT` | Optional | Default `20` |
| `RTAS_ADMIN_SECRET` | Recommended | Protects admin fal-funding APIs |
| `JAZZCASH_*` / `EASYPAISA_*` | Future | Placeholders only — not wired in code |

Webhook endpoints (after domain is live):

- Paddle: `https://REPLACE_APP_DOMAIN/api/webhooks/paddle`
- Lemon Squeezy: `https://REPLACE_APP_DOMAIN/api/webhooks/lemon-squeezy`

---

## Email

| Variable | Notes |
|----------|-------|
| `RESEND_API_KEY` | Preferred |
| `EMAIL_FROM` / `SMTP_FROM` | Must use verified domain in production |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURE`, `SMTP_USER`, `SMTP_PASS` | Fallback |

Sandbox `onboarding@resend.dev` only delivers to the Resend account owner.

---

## AI / GPU worker

| Variable | Notes |
|----------|-------|
| `FASTAPI_URL` | **Server** proxy target — never `localhost` in production |
| `NEXT_PUBLIC_FASTAPI_URL` | Client health banner / config probe |
| `FAL_KEY` | Primary cloud AI |
| `REPLICATE_API_TOKEN`, `RUNWAY_API_KEY`, `KLING_API_KEY` | Alternatives |
| `RTAS_GENERATION_WEBHOOK_SECRET` / `AI_BACKEND_SECRET` | Worker → web job callbacks |

Backend worker env: see `apps/backend/.env.example` (`CORS_ORIGINS` must include production app origin).

---

## Persistent store (Vercel)

| Variable | Notes |
|----------|-------|
| `KV_REST_API_URL` / `KV_REST_API_TOKEN` | Vercel KV (auto when linked) |
| `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN` | Aliases |

Required for serverless auth durability.

---

## Observability (placeholders)

| Variable | Notes |
|----------|-------|
| `NEXT_PUBLIC_SENTRY_DSN` / `SENTRY_DSN` | Error tracking when account ready |
| `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, `SENTRY_PROJECT` | Source maps upload |
| `NEXT_PUBLIC_ANALYTICS_ID` | Generic analytics |
| `NEXT_PUBLIC_POSTHOG_KEY` / `NEXT_PUBLIC_POSTHOG_HOST` | Product analytics |
| `NEXT_PUBLIC_GA_MEASUREMENT_ID` | GA4 |

Hooks live in `apps/web/src/lib/observability.ts` (no-op until configured).

---

## Future infrastructure placeholders

| Variable | Intended use |
|----------|--------------|
| `NEXT_PUBLIC_CDN_URL` | `https://cdn.REPLACE_APP_DOMAIN` |
| `NEXT_PUBLIC_ASSETS_URL` | `https://assets.REPLACE_APP_DOMAIN` |

See `docs/INFRASTRUCTURE.md`.

---

## Ops CLI only (local)

| Variable | Notes |
|----------|-------|
| `VERCEL_TOKEN` | `npm run env:vercel` |
| `GITHUB_TOKEN` | Branch protection / `gh` automation |
| `RTAS_ALLOW_INCOMPLETE_ENV` | CI only — softens `verify:production` |

---

## Verification commands

```bash
npm run verify:env -w @rtas/web
npm run verify:production -w @rtas/web
npm run probe:services -w @rtas/web
npm run env:vercel -w @rtas/web
```

Health endpoints (after deploy):

- `GET /api/health` — liveness
- `GET /api/ready` — readiness (503 if critical deps missing)
