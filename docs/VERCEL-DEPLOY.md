# Deploy RTAS Studio AI on Vercel (fresh project)

## One-time import

1. **https://vercel.com/new** → import **`rtasdmcompany-hub/RTAS-Studio-AI`**
2. **Root Directory:** set to **`apps/web`** → Continue
3. Framework: **Next.js** (auto-detected)
4. **Build & Development Settings** — leave **Install**, **Build**, and **Output Directory** all **empty** (repo root `vercel.json` is used for install/build via monorepo)
5. Add env vars (minimum): `NEXTAUTH_URL`, `NEXTAUTH_SECRET`, `NEXT_PUBLIC_APP_URL`
6. **Deploy**

## Monorepo config

| File | Purpose |
|------|---------|
| `/vercel.json` | Repo-root install/build (`npm` workspaces) |
| `/apps/web/vercel.json` | Used when Vercel **Root Directory = `apps/web`** (required for Next.js) |

Both use the same monorepo install (web workspace only). **Do not** add dashboard overrides.

## After first deploy

Update `NEXTAUTH_URL` and `NEXT_PUBLIC_APP_URL` to your real `.vercel.app` URL, then redeploy once.

## Persistent storage (required for auth on Vercel)

Vercel serverless functions cannot persist files on disk. Link **Vercel KV** (Storage → KV → Create) to the project. Vercel injects `KV_REST_API_URL` and `KV_REST_API_TOKEN` automatically.

Without KV, signup/login will return a clear configuration error on production.

Local development uses `apps/web/.data/` JSON files when KV is not set.

## CLI

```bash
cd apps/web
npx vercel link
npx vercel --prod --yes
```
