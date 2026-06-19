"""
Secure multipart uploads → data/uploads/{jobId}/
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.services.storage import job_upload_dir, resolve_upload_path

# Field ids allowed from studio form
ALLOWED_FIELD_IDS = frozenset(
    {
        "faceReference",
        "audioSource",
        "audio",
        "referenceImage",
        "sourceImage",
        "productImage",
        "coverImage",
    }
)

IMAGE_FIELDS = frozenset(
    {"faceReference", "referenceImage", "sourceImage", "productImage", "coverImage"}
)
AUDIO_FIELDS = frozenset({"audioSource", "audio"})

_FIELD_ID_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,63}$")


def new_job_id() -> str:
    return f"job_{int(datetime.now(timezone.utc).timestamp() * 1000)}"


def _parse_mime_list(raw: str) -> set[str]:
    return {m.strip().lower() for m in raw.split(",") if m.strip()}


def validate_field_id(field_id: str) -> None:
    if field_id not in ALLOWED_FIELD_IDS or not _FIELD_ID_RE.match(field_id):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid upload field id: {field_id}",
        )


def validate_upload(field_id: str, upload: UploadFile, size: int) -> None:
    if size > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {settings.max_upload_bytes // (1024 * 1024)} MB)",
        )

    content_type = (upload.content_type or "").lower()
    image_mimes = _parse_mime_list(settings.allowed_image_mimes)
    audio_mimes = _parse_mime_list(settings.allowed_audio_mimes)

    if field_id in IMAGE_FIELDS:
        if content_type not in image_mimes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image type for {field_id}: {content_type}",
            )
    elif field_id in AUDIO_FIELDS:
        if content_type not in audio_mimes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid audio type for {field_id}: {content_type}",
            )


def safe_filename(name: str) -> str:
    base = Path(name).name
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return cleaned[:180] or "upload.bin"


async def save_upload_file(
    job_id: str,
    field_id: str,
    upload: UploadFile,
) -> dict:
    validate_field_id(field_id)

    raw = await upload.read()
    size = len(raw)
    if size == 0:
        raise HTTPException(status_code=400, detail=f"Empty file for {field_id}")

    validate_upload(field_id, upload, size)

    filename = safe_filename(upload.filename or f"{field_id}.bin")
    dest: Path = resolve_upload_path(job_id, field_id, filename)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)

    public_url = (
        f"{settings.public_base_url.rstrip('/')}/media/uploads/"
        f"{job_id}/{dest.name}"
    )

    return {
        "fieldId": field_id,
        "name": filename,
        "mimeType": upload.content_type or "application/octet-stream",
        "size": size,
        "localPath": str(dest.resolve()),
        "url": public_url,
    }


async def save_upload_batch(
    job_id: str | None,
    uploads: list[tuple[str, UploadFile]],
) -> dict:
    jid = job_id or new_job_id()
    job_upload_dir(jid)

    saved: dict[str, dict] = {}
    for field_id, upload in uploads:
        if not upload.filename:
            continue
        saved[field_id] = await save_upload_file(jid, field_id, upload)

    return {"jobId": jid, "files": saved}
