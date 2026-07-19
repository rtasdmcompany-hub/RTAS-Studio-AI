"""
RTAS Studio AI — FastAPI application entry point.

Run locally:
  cd apps/backend
  python -m venv .venv
  .venv\\Scripts\\activate   # Windows
  pip install -r requirements.txt
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.middleware.content_moderation import ContentModerationMiddleware
from app.services.fal_verify import run_startup_verification as run_fal_startup_verification
from app.services.model_routing import get_routing_policy_summary
from app.services.storage import ensure_dirs

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        ensure_dirs()
        settings.local_output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.warning("ensure_dirs skipped on read-only runtime: %s", exc)
    routing = get_routing_policy_summary()
    logger.info(
        "Model routing active: cost optimization, ceiling $%.3f/s, max weight %.1fx",
        routing["hard_budget_ceiling_usd_per_second"],
        routing["max_credit_weight"],
    )
    logger.info("Content moderation active — NSFW filter enabled on /api/generate")
    logger.info(
        "CORS origins (align with NEXTAUTH_URL / Google JS origins): %s",
        ", ".join(settings.cors_origin_list),
    )
    try:
        await run_fal_startup_verification()
    except Exception as exc:  # noqa: BLE001 — worker must stay up for planner APIs
        logger.warning("Fal startup verification skipped: %s", exc)
    yield


app = FastAPI(
    title="RTAS Studio AI API",
    description="Video generation orchestration for RTAS Studio AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compress JSON plan/report payloads (safe bandwidth/latency win for production).
app.add_middleware(GZipMiddleware, minimum_size=500)

# Content safety — must run before any generation route handler.
app.add_middleware(ContentModerationMiddleware)

app.include_router(api_router)

# Static mounts require existing directories at import time (before lifespan).
# On read-only serverless hosts, skip mounts so planner/video-engine APIs still boot.
try:
    ensure_dirs()
    app.mount(
        "/media/outputs",
        StaticFiles(directory=str(settings.local_output_dir)),
        name="generated_outputs",
    )
    app.mount(
        "/media/uploads",
        StaticFiles(directory=str(settings.local_upload_dir)),
        name="uploaded_assets",
    )
except OSError as exc:
    logger.warning("Skipping local media mounts (non-writable runtime): %s", exc)


@app.get("/")
async def root():
    return {
        "name": "RTAS Studio AI API",
        "docs": "/docs",
        "health": "/api/health",
        "generate": "POST /api/generate",
        "media": "/media/outputs",
        "ai_provider_mode": settings.ai_provider_mode,
        "model_routing": get_routing_policy_summary(),
        "content_moderation": {"enabled": True, "target": "POST /api/generate"},
    }
