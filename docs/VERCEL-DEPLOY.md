# Deploy RTAS Studio AI on Vercel

## One-time setup (GitHub)

1. Open [vercel.com/new](https://vercel.com/new) and import **rtasdmcompany-hub/RTAS-Studio-AI**.
2. **Project Settings → General → Root Directory:** set to **`apps/web`** and click Save.
3. **Project Settings → Build & Development Settings** — clear ALL overrides (leave empty so `apps/web/vercel.json` is used):
   - **Install Command:** *(empty)* — do **not** use `cd ../.. && npm install`
   - **Build Command:** *(empty)*
   - **Output Directory:** *(empty)* — default `.next` inside `apps/web`
4. Framework: **Next.js** (auto-detected).
5. Add environment variables from `apps/web/.env.example` (see below).
6. Deploy.

**If you see `idealTree already exists` or `cd ../.. && npm install` in logs:** the Dashboard Install Command override is still set — clear it and redeploy.

**If you see `.next was not found at /vercel/path0/.next`:** Root Directory is not `apps/web` — fix step 2 and redeploy.

## Environment variables (production)

| Variable | Notes |
|----------|--------|
| `NEXTAUTH_URL` | `https://your-app.vercel.app` |
| `NEXTAUTH_SECRET` | Same as local or generate new |
| `NEXT_PUBLIC_APP_URL` | Same as `NEXTAUTH_URL` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Add Vercel URL to Google OAuth console |
| `GOOGLE_OAUTH_REDIRECT_URI` | `https://your-app.vercel.app/api/auth/callback/google` |
| `GOOGLE_OAUTH_JS_ORIGIN` | `https://your-app.vercel.app` |
| `FAL_KEY` | For live video generation |
| `NEXT_PUBLIC_FASTAPI_URL` | URL of Python backend (Railway/Render) if hosted separately |

**Note:** Video generation (`/api/generate`, FFmpeg compile) needs the **FastAPI backend** on a separate host. Vercel serves the Next.js frontend, auth, pricing, and studio UI.

## CLI deploy

```bash
cd apps/web
npx vercel --prod
```
