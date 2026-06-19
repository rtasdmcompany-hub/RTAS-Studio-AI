# RTAS Studio AI — Python API (FastAPI)

## Quick start (Windows)

```powershell
cd "H:\PERSONAL\RTAS Digital Marketing Company\RTAS Softwear\RTAS Studio AI\RTAS Studio AI\apps\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health
- Generate: `POST http://localhost:8000/api/generate`

## Connect Next.js frontend

In `apps/web/.env.local`:

```env
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000
```

Restart `npm run dev`. The studio will call the FastAPI backend for generation.

## Structure

```
apps/backend/
  main.py
  requirements.txt
  data/uploads/           # Incoming assets (multipart phase 2)
  data/outputs/           # Generated MP4s → /media/outputs/{jobId}.mp4
  app/
    core/config.py        # .env settings
    api/routes/
      generate.py         # POST /api/generate
      ai.py               # GET /api/ai/status
    services/
      ai_service.py       # Ingest → provider → delivery URL
      storage.py          # Local / S3-ready publish
      providers/
        replicate.py
        comfyui.py
        diffusers_local.py
```

## AI provider config

Copy `.env.example` → `.env` and set:

| Variable | Purpose |
|----------|---------|
| `REPLICATE_API_TOKEN` | Replicate video/image models |
| `COMFYUI_API_URL` | ComfyUI workflow server |
| `AI_BACKEND_SECRET` | Worker callback auth |
| `AI_PROVIDER_MODE` | `auto`, `simulation`, `replicate`, … |
| `PUBLIC_BASE_URL` | Base for delivery URLs |

Check config: `GET http://localhost:8000/api/ai/status`

## POST /api/generate

Accepts JSON matching the web studio payload:

- `mode`, `category`, `visualStyle`, `durationSeconds`
- `fields` (lyrics, musicStyle, directionPrompt, …)
- `files` (metadata: name, mimeType, size)
- `identityPipeline` (Instant-ID / IP-Adapter flags)
- `previewOnly`, `useFreeTrial`, `profile`

Returns `200` with `steps[]` (0–100% pipeline) and final `videoUrl`.
