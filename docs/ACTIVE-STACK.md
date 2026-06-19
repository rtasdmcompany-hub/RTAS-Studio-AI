# RTAS Studio AI Active Stack

Use this as the single source of truth while developing.

## Which project is active?

- Active frontend: `RTAS Studio AI/apps/web`
- Active backend: `RTAS Studio AI/apps/backend`
- Studio page: `http://localhost:3000/studio` (use `:3001` only if the Web terminal says port 3000 was busy)
- Generation API: `http://localhost:8000`

Do not use `apps/api` for studio generation. That is a legacy Express path.

## Required keys

### Frontend (`apps/web/.env.local`)

- `GOOGLE_CLIENT_ID=...`
- `GOOGLE_CLIENT_SECRET=...`
- `NEXT_PUBLIC_GOOGLE_AUTH_ENABLED=true`
- `NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000`

### Backend (`apps/backend/.env`)

- `FAL_KEY=...` (primary live provider)
- `AI_PROVIDER_MODE=auto`
- `PUBLIC_BASE_URL=http://localhost:8000`

`REPLICATE_API_TOKEN` is optional fallback and not required when `FAL_KEY` is present.

## Startup commands

From outer workspace root:

```powershell
# Easiest — double-click in Explorer:
start-studio.cmd

# Or manual:
npm run dev:api
npm run dev:fast -w @rtas/web
```

## Verification commands

From inner root `RTAS Studio AI/`:

```powershell
npm run verify:google-oauth -w @rtas/web
python apps/backend/scripts/verify_fal_env.py
npm run verify:stack
```

## Provider priority

In `AI_PROVIDER_MODE=auto`, backend picks:

1. `fal` (if `FAL_KEY` configured)
2. `replicate` (if token configured)
3. local simulation fallback
