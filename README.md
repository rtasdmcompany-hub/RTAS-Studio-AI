# RTAS Studio AI

**RTAS DIGITAL MARKETING COMPANY** · Under **RTAS GROUP OF COMPANIES**

International AI video platform: **Prompt to Video** and **Image to Video** (5 seconds – 10 minutes).

> If you are seeing duplicate folders / mixed APIs, read `docs/ACTIVE-STACK.md` first.

## Quick start (developers)

```bash
# 1. Install Node.js 20 LTS from https://nodejs.org
cd "RTAS Studio AI"
npm install
cp apps/web/.env.example apps/web/.env.local
# Add API keys (see docs/SETUP-DOWNLOADS.md)
npm run dev
```

Open http://localhost:3000

**Optional — Python API:**

```bash
cd apps/backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000
```

Set `NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000` in `apps/web/.env.local`.

## Project structure

| Folder | Purpose |
|--------|---------|
| `apps/web` | Next.js app — desktop + mobile web |
| `apps/backend` | FastAPI — video generation API (`POST /api/generate`) |
| `apps/mobile` | Expo — Android & iOS store builds |
| `packages/shared` | Types, credits, categories, legal text |
| `docs` | Setup, architecture, API providers |

## Your product rules (implemented in code)

- First video: **30 seconds free**
- Subscription: **$89/month**, **500 credits**
- **50 credits** per 5-minute video
- Credits expire end of billing month; early resubscribe **rolls over** remaining credits
- After free tier: subscribe or **Skip for next time** → preview only (watermarked, no download)
- Visual modes: **Real face** (identity-preserving), **Avatar**, **Cartoon**
- Payments: Stripe (international) + Pakistan (JazzCash / EasyPaisa / bank — configure in dashboard)

## Logo

Place your logo at: `apps/web/public/logo.png` (used in app header and video watermark).

## Legal

Terms: in-app `/terms` and `packages/shared/src/legal/terms.ts`

---

See **docs/SETUP-DOWNLOADS.md** for everything to install on your PC.
