"""Validate voice clone / train reference audio payloads."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".webm"}
ALLOWED_MIME_HINTS = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/ogg",
    "audio/flac",
    "audio/mp4",
    "audio/webm",
}
MIN_DURATION_SEC = 1.0
MAX_DURATION_SEC = 120.0
MIN_SAMPLE_RATE = 16000
MAX_SAMPLE_RATE = 48000
MIN_QUALITY = 0.35


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checksum: str = ""
    duration_sec: float = 0.0
    sample_rate: int = 0
    file_type: str = ""
    quality_hint: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "checksum": self.checksum,
            "duration_sec": self.duration_sec,
            "sample_rate": self.sample_rate,
            "file_type": self.file_type,
            "quality_hint": self.quality_hint,
        }


def _ext_from_url(url: str) -> str:
    path = urlparse(url).path.lower()
    for ext in ALLOWED_EXTENSIONS:
        if path.endswith(ext):
            return ext
    return ""


def estimate_reference_stats(
    reference_url: str,
    *,
    duration_sec: float | None = None,
    sample_rate: int | None = None,
    file_type: str | None = None,
    quality_hint: float | None = None,
) -> tuple[float, int, str, float, str]:
    """Derive reference stats for simulation when client omits metadata."""
    url = (reference_url or "").strip()
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    # Deterministic pseudo-stats from URL hash (stable across runs)
    n = int(digest[:8], 16)
    dur = float(duration_sec) if duration_sec is not None else 3.0 + (n % 170) / 10.0
    rate = int(sample_rate) if sample_rate is not None else (16000 if n % 2 == 0 else 24000)
    ext = (file_type or _ext_from_url(url) or ".wav").lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    q = float(quality_hint) if quality_hint is not None else 0.55 + (n % 40) / 100.0
    return round(dur, 3), rate, ext, round(min(0.99, q), 3), digest


def validate_clone_reference(
    reference_url: str,
    *,
    duration_sec: float | None = None,
    sample_rate: int | None = None,
    file_type: str | None = None,
    mime_type: str | None = None,
    quality_hint: float | None = None,
    known_checksums: set[str] | None = None,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    url = (reference_url or "").strip()
    if not url:
        return ValidationResult(ok=False, errors=["reference_url is required"])

    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in ("http", "https", "file", "media", ""):
        # Allow relative /media paths (empty scheme)
        if not url.startswith("/"):
            errors.append(f"Unsupported URL scheme '{parsed.scheme}'")

    dur, rate, ext, q, digest = estimate_reference_stats(
        url,
        duration_sec=duration_sec,
        sample_rate=sample_rate,
        file_type=file_type,
        quality_hint=quality_hint,
    )

    if ext not in ALLOWED_EXTENSIONS:
        errors.append(f"Invalid file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}")

    if mime_type and mime_type.lower() not in ALLOWED_MIME_HINTS:
        warnings.append(f"Unusual mime_type '{mime_type}'")

    if dur < MIN_DURATION_SEC:
        errors.append(f"Audio too short ({dur}s). Minimum {MIN_DURATION_SEC}s")
    if dur > MAX_DURATION_SEC:
        errors.append(f"Audio too long ({dur}s). Maximum {MAX_DURATION_SEC}s")

    if rate < MIN_SAMPLE_RATE:
        errors.append(f"Sample rate {rate} below minimum {MIN_SAMPLE_RATE}")
    if rate > MAX_SAMPLE_RATE:
        errors.append(f"Sample rate {rate} above maximum {MAX_SAMPLE_RATE}")

    if q < MIN_QUALITY:
        errors.append(f"Audio quality too low ({q}). Minimum {MIN_QUALITY}")

    checksum = hashlib.sha256(f"{url}|{dur}|{rate}|{ext}".encode()).hexdigest()
    if known_checksums and checksum in known_checksums:
        errors.append("Duplicate training sample detected")

    return ValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        checksum=checksum,
        duration_sec=dur,
        sample_rate=rate,
        file_type=ext,
        quality_hint=q,
    )
