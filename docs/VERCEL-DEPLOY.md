# Deploy RTAS Studio AI on Vercel (fresh setup from zero)

## Step 1 — Import project (Vercel dashboard)

1. Open **https://vercel.com/new**
2. Import GitHub repo **`rtasdmcompany-hub/RTAS-Studio-AI`**
3. **Root Directory:** click Edit → set to **`apps/web`** → Continue
4. Framework: **Next.js** (auto-detected)

## Step 2 — Build settings (IMPORTANT)

Under **Build & Development Settings**, leave these **empty** (do not override):

| Setting | Value |
|---------|--------|
| Install Command | *(empty)* |
| Build Command | *(empty)* |
| Output Directory | *(empty)* |

`apps/web/vercel.json` handles install + build. **Never** use `cd ../.. && npm install` — it causes `idealTree already exists` on Vercel.

## Step 3 — Environment variables (minimum for live site)

Add in Vercel → Settings → Environment Variables:

| Variable | Example |
|----------|---------|
| `NEXTAUTH_URL` | `https://YOUR-PROJECT.vercel.app` |
| `NEXTAUTH_SECRET` | *(same as local `.env.local` or generate new)* |
| `NEXT_PUBLIC_APP_URL` | `https://YOUR-PROJECT.vercel.app` |

Optional: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `FAL_KEY` — add when ready.

## Step 4 — Deploy

Click **Deploy**. After first deploy, update `NEXTAUTH_URL` and `NEXT_PUBLIC_APP_URL` to the real `.vercel.app` URL and redeploy once.

## CLI alternative (after `npx vercel login`)

```bash
cd apps/web
npx vercel link
npx vercel --prod --yes
```

When linking, choose team **RTAS_Group**, create project name e.g. **rtas-studio-ai**.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `idealTree already exists` | Dashboard Install Command override still set — clear it |
| `.next not found at /vercel/path0/.next` | Root Directory is not `apps/web` |
| `DEPLOYMENT_NOT_FOUND` | Old URL — use latest deployment from dashboard |
| Invalid git author | Commits must use `RTAS-Studio-AI <rtasdmcompany@gmail.com>` |
