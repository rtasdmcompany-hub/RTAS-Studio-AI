"""Export request validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.audio_export.profiles import (
    AUDIO_FORMATS,
    VIDEO_FORMATS,
    get_profile,
)


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    platform: str = "youtube"
    quality: str = "high"
    watermark: bool = False
    formats: list[str] = field(default_factory=list)
    expire_hours: float = 24.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "platform": self.platform,
            "quality": self.quality,
            "watermark": self.watermark,
            "formats": list(self.formats),
            "expire_hours": self.expire_hours,
        }


def validate_export_request(
    *,
    platform: str | None = None,
    quality: str | None = None,
    formats: list[str] | None = None,
    watermark: bool = False,
    expire_hours: float | None = None,
) -> ValidationResult:
    errors: list[str] = []
    resolved_platform = (platform or "youtube").strip().lower()
    profile = get_profile(resolved_platform)
    if profile is None:
        errors.append(f"unsupported platform: {resolved_platform}")
        resolved_platform = "youtube"
    else:
        resolved_platform = profile.platform

    q = (quality or "high").strip().lower()
    if q not in ("low", "medium", "high", "broadcast"):
        errors.append("quality must be one of: low, medium, high, broadcast")
        q = "high"

    resolved_formats: list[str] = []
    if formats:
        for fmt in formats:
            f = str(fmt).strip().lower()
            if f not in AUDIO_FORMATS and f not in VIDEO_FORMATS and f not in ("json", "xml"):
                errors.append(f"unsupported format: {f}")
            else:
                resolved_formats.append(f)

    hours = float(expire_hours) if expire_hours is not None else 24.0
    if hours <= 0 or hours > 168:
        errors.append("expire_hours must be between 0 exclusive and 168 inclusive")
        hours = 24.0

    return ValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        platform=resolved_platform,
        quality=q,
        watermark=bool(watermark),
        formats=resolved_formats,
        expire_hours=hours,
    )
