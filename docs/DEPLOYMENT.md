# Deployment guide — RTAS Studio AI

**Goal:** When production credentials and domain are available, complete go-live in **under 30 minutes** by following this runbook.

This guide assumes the codebase is already deployment-ready (CI green, templates present). It does **not** require credentials to be present while preparing the repo.

Related docs: [PRODUCTION.md](./PRODUCTION.md) · [ENVIRONMENT.md](./ENVIRONMENT.md) · [INFRASTRUCTURE.md](./INFRASTRUCTURE.md) · [SECURITY.md](./SECURITY.md) · [OPERATIONS.md](./OPERATIONS.md)

---

## Architecture (deploy targets)

| Component | Host | Notes |
|-----------|------|-------|
| Next.js web (`@rtas/web`) | **Vercel** | Primary commercial surface |
| Postgres | **Supabase** (or Neon) | Prisma `DATABASE_URL` |
| KV / Redis | **Vercel KV** or Upstash | Serverless persistence |
| FastAPI GPU worker | **Separate host** | `FASTAPI_URL` — not on Vercel serverless |
| Email | **Resend** | Verified domain |
| Payments | **Paddle** (or Lemon Squeezy) | MoR + webhooks |
| AI render | **fal.ai** (or Replicate) | Via worker / web keys |
| Source + CI | **GitHub** | `.github/workflows/ci-web.yml` |

---

## 30-minute go-live sequence

### Minute 0–5 — Secrets into Vercel

1. Open Vercel project linked to this repo (Root Directory = monorepo root; use root `vercel.json`).
2. **Storage** → create/link **KV** (auto-injects `KV_REST_API_*`).
3. **Settings → Environment Variables** → paste from filled `apps/web/.env.production.example` for **Production** (and Preview as needed).
4. Minimum set: `NEXTAUTH_SECRET`, `NEXTAUTH_URL`, `NEXT_PUBLIC_APP_URL`, `DATABASE_URL`, `FASTAPI_URL`, payment webhook + checkout URLs, `RESEND_API_KEY`, `EMAIL_FROM`, `FAL_KEY`, Google OAuth if used.

Optional local sync (requires `VERCEL_TOKEN` in `.env.local`):

```bash
npm run env:vercel -w @rtas/web
```

### Minute 5–10 — Database

```bash
# From monorepo root, with production DATABASE_URL in env:
npm run db:push -w @rtas/web
```

Prefer adding Prisma migrations before high-traffic launch; `db:push` is acceptable for first schema bootstrap.

### Minute 10–15 — Domain + SSL

1. Vercel → **Domains** → add `REPLACE_APP_DOMAIN` (+ www).
2. Configure DNS per Vercel instructions (SSL automatic).
3. Set `NEXTAUTH_URL` + `NEXT_PUBLIC_APP_URL` to `https://REPLACE_APP_DOMAIN`.
4. Point `api.REPLACE_APP_DOMAIN` at the GPU worker; set `FASTAPI_URL`.

### Minute 15–20 — External dashboards

| Service | Action |
|---------|--------|
| **Google Cloud** | Add production JS origin + redirect URI |
| **Resend** | Verify `REPLACE_EMAIL_DOMAIN`; confirm `EMAIL_FROM` |
| **Paddle** | Webhook → `https://REPLACE_APP_DOMAIN/api/webhooks/paddle`; copy secret |
| **fal.ai** | Confirm billing credit + key |
| **GPU host** | Deploy FastAPI; set `CORS_ORIGINS` to app origin; health `/api/health` |

### Minute 20–25 — Deploy

1. Push to `main`/`master` **or** Vercel → **Deploy**.
2. Wait for build (CI should already be green).
3. Confirm deployment URL responds.

### Minute 25–30 — Smoke

```bash
curl -sS https://REPLACE_APP_DOMAIN/api/health
curl -sS https://REPLACE_APP_DOMAIN/api/ready
npm run probe:services -w @rtas/web   # with production-shaped .env.local or exported env
```

Manual: register → verify email → Google login (if enabled) → open Studio → checkout sandbox/test → webhook delivery in Paddle logs.

---

## GitHub

1. Ensure remote is `rtasdmcompany-hub/RTAS-Studio-AI` (or your org).
2. CI: `.github/workflows/ci-web.yml` runs lint, typecheck, smoke, verify:production (soft), build.
3. Protect `main`/`master` — see [GITHUB-BRANCH-PROTECTION.md](./GITHUB-BRANCH-PROTECTION.md).
4. Never commit `.env.local`. Rotate any secret pasted into chat/tickets.

---

## Vercel project settings

Prefer **monorepo root**:

| Setting | Value |
|---------|-------|
| Install | from `vercel.json` |
| Build | `npm run build -w @rtas/web` |
| Framework | Next.js |
| Node | `24.x` |
| Region | `iad1` |

If Root Directory = `apps/web`, use `apps/web/vercel.json` instead.

---

## Supabase

1. Create project; copy **pooled** connection string → `DATABASE_URL`.
2. Optional: set `NEXT_PUBLIC_SUPABASE_URL` + anon/service keys for REST/storage.
3. Auth remains **NextAuth** — do not enable Supabase Auth as the primary path unless product changes.
4. Lock down RLS on any exposed tables.

---

## Resend

1. Add domain → DNS (SPF/DKIM).
2. Create API key → `RESEND_API_KEY`.
3. Set `EMAIL_FROM` to an address on the verified domain.
4. Test via app registration or Resend dashboard.

---

## Paddle

1. Create products/prices + payment links.
2. Set `NEXT_PUBLIC_PAYMENT_PROVIDER=paddle`.
3. Configure webhook URL + `PADDLE_WEBHOOK_SECRET`.
4. Set checkout URL env vars.
5. Details: [PAYMENTS-WEBHOOKS.md](./PAYMENTS-WEBHOOKS.md).

---

## fal.ai

1. Create key → `FAL_KEY` (web and/or backend).
2. Ensure account has credit.
3. Optional: `FAL_ADMIN_API_KEY` for pool monitoring.

---

## DNS & SSL

- SSL: automatic on Vercel custom domains.
- API subdomain: terminate TLS on GPU host or edge proxy.
- After DNS: update OAuth, webhooks, and env URLs; **redeploy** so Next.js picks up env.

---

## Rollback

See [RECOVERY.md](./RECOVERY.md). Short path:

1. Vercel → Deployments → **Promote** previous healthy deployment.
2. If bad migration: restore DB from backup ([BACKUP.md](./BACKUP.md)) then redeploy last good app.
3. If bad env: revert variable → Redeploy.

---

## Post-deploy monitoring

- Uptime: poll `GET /api/health` every 60s.
- Readiness: poll `GET /api/ready` (alert on 503).
- Vercel runtime logs + fal/Paddle/Resend dashboards.
- Optional: set `NEXT_PUBLIC_SENTRY_DSN` when Sentry is ready.
