"""
Secure multipart uploads → data/uploads/{jobId}/
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.core.runtime import is_production
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
_JOB_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


def new_job_id() -> str:
    return f"job_{int(datetime.now(timezone.utc).timestamp() * 1000)}"


def sanitize_job_id(job_id: str | None) -> str:
    """Reject path traversal / odd characters in job ids."""
    if not job_id:
        return new_job_id()
    cleaned = job_id.strip()
    if ".." in cleaned or "/" in cleaned or "\\" in cleaned or not _JOB_ID_RE.match(cleaned):
        raise HTTPException(status_code=400, detail="Invalid job_id")
    return cleaned


def _starts_with(buf: bytes, sig: bytes) -> bool:
    return len(buf) >= len(sig) and buf[: len(sig)] == sig


def assert_magic_bytes(field_id: str, raw: bytes) -> None:
    """Reject uploads whose content does not match allowed image/audio signatures."""
    header = raw[:32]
    if field_id in IMAGE_FIELDS:
        ok = (
            _starts_with(header, b"\xff\xd8\xff")
            or _starts_with(header, b"\x89PNG\r\n\x1a\n")
            or _starts_with(header, b"GIF87a")
            or _starts_with(header, b"GIF89a")
            or (
                _starts_with(header, b"RIFF")
                and len(header) >= 12
                and header[8:12] == b"WEBP"
            )
        )
        if not ok:
            raise HTTPException(
                status_code=400,
                detail=f"File content does not match an allowed image format for {field_id}.",
            )
        return

    if field_id in AUDIO_FIELDS:
        ok = (
            _starts_with(header, b"ID3")
            or (len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0)
            or (
                _starts_with(header, b"RIFF")
                and len(header) >= 12
                and header[8:12] == b"WAVE"
            )
            or (len(header) >= 8 and header[4:8] == b"ftyp")
        )
        if not ok:
            raise HTTPException(
                status_code=400,
                detail=f"File content does not match an allowed audio format for {field_id}.",
            )


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
    jid = sanitize_job_id(job_id)

    raw = await upload.read()
    size = len(raw)
    if size == 0:
        raise HTTPException(status_code=400, detail=f"Empty file for {field_id}")

    validate_upload(field_id, upload, size)
    assert_magic_bytes(field_id, raw)

    filename = safe_filename(upload.filename or f"{field_id}.bin")
    dest: Path = resolve_upload_path(jid, field_id, filename)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)

    # In production uploads are not publicly mounted; URL is an internal reference.
    if is_production():
        public_url = f"rtas-upload://{jid}/{dest.name}"
    else:
        public_url = (
            f"{settings.public_base_url.rstrip('/')}/media/uploads/"
            f"{jid}/{dest.name}"
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
    jid = sanitize_job_id(job_id)
    job_upload_dir(jid)

    saved: dict[str, dict] = {}
    for field_id, upload in uploads:
        if not upload.filename:
            continue
        saved[field_id] = await save_upload_file(jid, field_id, upload)

    return {"jobId": jid, "files": saved}
