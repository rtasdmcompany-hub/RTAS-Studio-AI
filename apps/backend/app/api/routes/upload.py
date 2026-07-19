"""
POST /api/upload — multipart asset intake for Replicate / local pipelines.
Requires X-Rtas-Backend-Secret when AI_BACKEND_SECRET is configured (always in prod).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.backend_auth import require_backend_secret
from app.services.upload_service import save_upload_batch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

KNOWN_FILE_FIELDS = [
    "faceReference",
    "audioSource",
    "referenceImage",
    "sourceImage",
    "productImage",
    "coverImage",
    "audio",
]


@router.post("")
async def upload_assets(
    request: Request,
    _: None = Depends(require_backend_secret),
):
    """
    Upload studio assets before generation.

    `multipart/form-data` with optional `job_id` and one file per field id
    (e.g. `faceReference`, `audioSource`, `sourceImage`).
    """
    form = await request.form()
    job_id = form.get("job_id") or form.get("jobId")
    if isinstance(job_id, str):
        job_id = job_id.strip() or None
    else:
        job_id = None

    uploads: list[tuple[str, object]] = []
    for key, value in form.multi_items():
        if key in ("job_id", "jobId"):
            continue
        if hasattr(value, "read") and getattr(value, "filename", None):
            uploads.append((key, value))

    if not uploads:
        raise HTTPException(
            status_code=400,
            detail="No files provided. Attach at least one asset field.",
        )

    logger.info("Upload batch job_id=%s count=%d", job_id, len(uploads))
    result = await save_upload_batch(job_id, uploads)  # type: ignore[arg-type]
    return {"ok": True, **result}


@router.get("/fields")
async def upload_field_help(_: None = Depends(require_backend_secret)):
    return {
        "allowedFieldIds": KNOWN_FILE_FIELDS,
        "pathPattern": "data/uploads/{jobId}/{fieldId}_{filename}",
    }
