# Production release notes — RTAS Studio AI (web)

> **Canonical docs (deployment-ready pack):**
> [DEPLOYMENT.md](./DEPLOYMENT.md) · [PRODUCTION.md](./PRODUCTION.md) · [ENVIRONMENT.md](./ENVIRONMENT.md) · [RELEASE-CHECKLIST.md](./RELEASE-CHECKLIST.md) · [SECURITY.md](./SECURITY.md) · [OPERATIONS.md](./OPERATIONS.md)
>
> Templates: `apps/web/.env.example`, `apps/web/.env.production.example`
> Gate: `npm run verify:deployment-ready -w @rtas/web`

## Vercel project settings (Root Directory)

Prefer deploying from the **monorepo root** with root `vercel.json`:

- Install: `npm install --workspace=@rtas/web --include-workspace-root --legacy-peer-deps --no-audit --no-fund`
- Build: `npm run build -w @rtas/web`
- Framework: Next.js (auto-detected from apps/web)

If the Vercel project Root Directory is set to `apps/web`, use `apps/web/vercel.json` instead.

## Required Production environment variables

See `apps/web/.env.example` and run:

```bash
npm run verify:production -w @rtas/web
npm run probe:services -w @rtas/web
npm run env:vercel -w @rtas/web   # requires VERCEL_TOKEN in .env.local
```

Critical keys: `NEXTAUTH_SECRET`, `NEXTAUTH_URL`, `NEXT_PUBLIC_APP_URL`, `DATABASE_URL`, `FASTAPI_URL`, payment webhook secret + checkout URLs, `RESEND_API_KEY` + verified `EMAIL_FROM`, `FAL_KEY`, KV/Redis for serverless.

## Auth model

- **NextAuth** (credentials + Google) — not Supabase Auth
- **Prisma** against Postgres (typically Supabase/Neon pooled `DATABASE_URL`)
- Supabase URL/anon/service keys are optional for REST/storage; RLS must still protect any exposed tables

## GitHub

- CI workflow: `.github/workflows/ci-web.yml`
- Install GitHub CLI (`gh`) for branch protection automation
- Protect `master`/`main`: require CI status checks before merge

## Domains / SSL

Configure custom domain in Vercel Dashboard → Domains (SSL automatic).
Set `NEXTAUTH_URL` and `NEXT_PUBLIC_APP_URL` to the canonical HTTPS origin.
Update Google OAuth redirect URIs to match production.
