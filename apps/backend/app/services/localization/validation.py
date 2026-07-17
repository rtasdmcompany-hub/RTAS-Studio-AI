"""Validate localization requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.localization.languages import normalize_language


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    source_language: str = "en"
    target_language: str = "en"
    text: str = ""
    duration_sec: float = 12.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "source_language": self.source_language,
            "target_language": self.target_language,
            "text": self.text,
            "duration_sec": self.duration_sec,
        }


def validate_localization_request(
    *,
    text: str | None,
    source_language: str | None = "en",
    target_language: str | None = "en",
    duration_sec: float | None = None,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    cleaned = (text or "").strip()
    if not cleaned:
        errors.append("text is required")
    if len(cleaned) > 20000:
        errors.append("text exceeds 20000 characters")

    try:
        src = normalize_language(source_language)
    except ValueError as exc:
        errors.append(str(exc))
        src = "en"
    try:
        tgt = normalize_language(target_language)
    except ValueError as exc:
        errors.append(str(exc))
        tgt = "en"

    if src == tgt:
        warnings.append("source and target languages are identical")

    dur = 12.0 if duration_sec is None else float(duration_sec)
    if dur < 0.5 or dur > 3600:
        errors.append("duration_sec must be between 0.5 and 3600")

    return ValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        source_language=src,
        target_language=tgt,
        text=cleaned,
        duration_sec=round(dur, 3),
    )
