"""AudioValidator — structural checks for production readiness."""

from __future__ import annotations

from app.services.audio_engine.models import (
    AmbientClip,
    MusicClip,
    SfxClip,
    ValidationResult,
    VoiceClip,
)


def validate_audio_plan(
    *,
    prompt: str,
    voice: list[VoiceClip],
    music: list[MusicClip],
    ambient: list[AmbientClip],
    sfx: list[SfxClip],
    duration_sec: float,
) -> ValidationResult:
    issues: list[str] = []
    warnings: list[str] = []

    if not prompt.strip():
        issues.append("Prompt is empty")
    if not voice:
        issues.append("No voice clips planned")
    if duration_sec <= 0:
        issues.append("Timeline duration must be > 0")
    if not music:
        warnings.append("No music bed planned")
    if not ambient:
        warnings.append("No ambient layer planned")
    if not sfx:
        warnings.append("No SFX planned")

    for clip in voice:
        if clip.end_sec <= clip.start_sec:
            issues.append(f"Voice clip {clip.clip_id} has invalid timing")
        if not clip.text.strip():
            issues.append(f"Voice clip {clip.clip_id} has empty text")

    for clip in music:
        if clip.end_sec <= clip.start_sec:
            issues.append(f"Music clip {clip.clip_id} has invalid timing")

    passed = len(issues) == 0 and len(voice) > 0 and duration_sec > 0
    return ValidationResult(passed=passed, issues=issues, warnings=warnings)
