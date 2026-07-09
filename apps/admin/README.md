# RTAS Admin

Owner dashboard for RTAS Studio AI. Reads Fal pool status from `@rtas/web` admin APIs and exposes backend guard controls.

## Dev

```bash
npm run dev:admin
```

Open http://localhost:3002

## Environment

| Variable | Purpose |
|----------|---------|
| `WEB_APP_URL` | Base URL for `@rtas/web` (default `http://localhost:3000`) |
| `FASTAPI_URL` | FastAPI backend for guard reset (default `http://localhost:8000`) |
| `RTAS_ADMIN_SECRET` | Must match web + backend admin secret |
| `AI_BACKEND_SECRET` | Optional backend-only secret for guard reset |

User-facing studio UI lives in `apps/web`. Admin does not duplicate Prisma or payment webhooks.
