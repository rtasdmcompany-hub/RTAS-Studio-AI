# Deploy RTAS Studio AI on Vercel

## One-time setup (GitHub)

1. Open [vercel.com/new](https://vercel.com/new) and import **rtasdmcompany-hub/RTAS-Studio-AI**.
2. Set **Root Directory** to `apps/web` (required — monorepo).
3. Framework: **Next.js** (auto-detected).
4. Add environment variables from `apps/web/.env.example` (see below).
5. Deploy.

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
