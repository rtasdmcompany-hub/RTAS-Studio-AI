# AI Generation Service (Python)

## Flow

```
POST /api/generate
    → ingest_payload()        # lyrics, musicStyle, files, identity pipeline
    → _pick_provider()        # auto | replicate | comfyui | diffusers
    → provider.generate()   # cloud / GPU scaffold
    → storage.publish_*()   # local MP4 + delivery URL
    → GenerateResponse      # videoUrl for Next.js player
```

## Delivery URLs

| Mode | URL pattern |
|------|-------------|
| Simulation | Remote placeholder MP4 (Google sample) |
| Local output | `{PUBLIC_BASE_URL}/media/outputs/{jobId}.mp4` |
| Cloud (future) | `S3_PUBLIC_BASE_URL/...` after upload |

## Enable Replicate (live)

1. Set `REPLICATE_API_TOKEN` in `apps/backend/.env`
2. `pip install -r requirements.txt` (includes `replicate` package)
3. Restart uvicorn — `AI_PROVIDER_MODE=auto` prefers Replicate when token is set
4. Image-to-video uses `wavespeedai/wan-2.1-i2v-480p`; text-only uses `wan-2.1-t2v-480p`
5. Output MP4 is cached to `data/outputs/{jobId}.mp4` and served at `/media/outputs/{jobId}.mp4`

**Note:** File uploads must exist under `data/uploads/{jobId}/` for image/real-face modes (multipart upload phase 2).

## File uploads (phase 2)

Frontend will POST multipart to `/api/upload`; files land in `data/uploads/{jobId}/` so `ingest_payload` resolves real paths for InstantID.
