"""
Vercel Python entry — production HTTPS FastAPI worker.
"""

from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path

from fastapi import FastAPI

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("rtas.vercel")

# Top-level ASGI symbols required by Vercel Python runtime.
app: FastAPI
handler = None

try:
    from main import app as application

    app = application
except Exception as exc:  # noqa: BLE001 — must boot diagnostic ASGI on cold start
    logger.exception("Failed to import main FastAPI app")
    _err = f"{type(exc).__name__}: {exc}"
    _tb = traceback.format_exc()
    app = FastAPI(title="RTAS Studio AI API (boot error)")

    @app.get("/api/health")
    @app.get("/api/health/ping")
    async def health_fallback():
        return {"status": "error", "boot_error": _err}

    @app.get("/api/video-engine/version")
    async def version_fallback():
        return {"ok": False, "boot_error": _err, "trace": _tb[:2000]}

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def catchall(path: str = ""):
        return {"ok": False, "path": path, "boot_error": _err, "trace": _tb[:2000]}

try:
    from mangum import Mangum

    handler = Mangum(app, lifespan="auto")
except Exception:
    handler = None
