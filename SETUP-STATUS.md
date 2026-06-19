# RTAS Studio AI — Setup Status

Last updated: 2026-06-14 — autonomous setup finalized.

## Applied & saved on disk

| Item | Status |
|------|--------|
| Google OAuth (`.env.local`) | Configured — Client ID + secret |
| 3 pricing tiers ($5 / $89 / $249) | `packages/shared/src/credits.ts` |
| Credit gate + recharge popup | Studio + `/pricing#plans` |
| Rotating 5 background videos | Global layout |
| Footer RTAS Group logo | `public/rtas-group-logo.png` |
| Tester 30s duration limit | `duration-limits.ts` |
| Standard 5min → 15s segments + stitch | `video-pipeline.ts`, compile API |
| Processing ETA modal | `GenerationStartedModal.tsx` |
| Video-ready email/notification | `/api/notify/video-ready` |
| Fal.ai key | In `.env.local` |
| Showcase videos (5 loops) | Present in `public/showcase/` |
| Dev server | Run `start-rtas-studio.cmd` or `npm run dev:fast` in `apps/web` |
| Git repo | Not initialized (optional — say the word to create initial commit) |

## Start dev

```cmd
start-rtas-studio.cmd
```

Or: `apps\web\start-web.cmd`

## Still needs your secret (cannot auto-fill)

1. **Gmail SMTP** — set `SMTP_PASS` in `apps/web/.env.local` (Google App Password)
2. **Google OAuth** — if login fails with `invalid_client`, regenerate Client Secret in Google Cloud Console
3. **Paddle/Lemon checkout URLs** — when going live with real payments

## Showcase videos

All five loops are installed: `rap.mp4`, `solo.mp4`, `commercial.mp4`, `cartoon.mp4`, `islamic.mp4`.
