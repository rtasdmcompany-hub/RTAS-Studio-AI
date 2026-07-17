"""Request validation for Voice Generation."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.voice_generation.languages import is_supported_language, normalize_language
from app.services.voice_generation.presets import get_voice


@dataclass
class VoiceValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    language: str = "en"
    voice_id: str = ""

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "language": self.language,
            "voice_id": self.voice_id,
        }


def validate_generate_request(
    *,
    text: str,
    language: str | None,
    voice_id: str | None,
    gender: str | None,
    speed: float,
    pitch: float,
    volume: float,
    pause_ms: int,
) -> VoiceValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    cleaned = (text or "").strip()
    if not cleaned:
        errors.append("text is required")
    elif len(cleaned) > 5000:
        errors.append("text exceeds 5000 characters")

    lang = "en"
    try:
        lang = normalize_language(language)
    except ValueError as exc:
        errors.append(str(exc))

    resolved_voice = (voice_id or "").strip()
    if resolved_voice:
        try:
            preset = get_voice(resolved_voice)
            if preset.language != lang:
                warnings.append(
                    f"voice language {preset.language} differs from request language {lang}"
                )
        except ValueError as exc:
            errors.append(str(exc))
    else:
        # Auto-select preset by language + gender
        g = (gender or "female").strip().lower()
        if g not in ("male", "female", "neutral"):
            errors.append("gender must be male, female, or neutral")
            g = "female"
        candidate = f"rtas_{lang}_{'male' if g == 'male' else 'female'}_01"
        try:
            get_voice(candidate)
            resolved_voice = candidate
        except ValueError:
            errors.append(f"No default voice for language={lang} gender={g}")

    if not (0.5 <= float(speed) <= 2.0):
        errors.append("speed must be between 0.5 and 2.0")
    if not (-12.0 <= float(pitch) <= 12.0):
        errors.append("pitch must be between -12 and 12")
    if not (0.0 <= float(volume) <= 2.0):
        errors.append("volume must be between 0.0 and 2.0")
    if pause_ms < 0 or pause_ms > 5000:
        errors.append("pause_ms must be between 0 and 5000")

    if language and not is_supported_language(language):
        # already captured above when normalize fails
        pass

    return VoiceValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        language=lang,
        voice_id=resolved_voice,
    )
