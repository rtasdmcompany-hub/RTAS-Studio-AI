"""Validate music generation requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.music_generation.genres import get_genre, is_known_genre, normalize_genre
from app.services.music_generation.instruments import resolve_instruments

VALID_ROLES = {"background", "intro", "outro", "theme", "loop", "instrumental"}
MIN_BPM, MAX_BPM = 40, 220
MIN_DURATION, MAX_DURATION = 2.0, 600.0
VALID_KEYS = {
    "C", "Cm", "C#", "C#m", "Db", "Dbm", "D", "Dm", "Eb", "Ebm", "E", "Em",
    "F", "Fm", "F#", "F#m", "Gb", "G", "Gm", "Ab", "Abm", "A", "Am", "Bb", "Bbm", "B", "Bm",
}


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    genre: str = "cinematic"
    role: str = "background"
    bpm: int = 90
    key: str = "Cm"
    mood: str = "dramatic"
    energy: float = 0.6
    intensity: float = 0.5
    duration_sec: float = 30.0
    instruments: list[str] = field(default_factory=list)
    loop: bool = False
    fade_in_sec: float = 1.0
    fade_out_sec: float = 2.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "genre": self.genre,
            "role": self.role,
            "bpm": self.bpm,
            "key": self.key,
            "mood": self.mood,
            "energy": self.energy,
            "intensity": self.intensity,
            "duration_sec": self.duration_sec,
            "instruments": list(self.instruments),
            "loop": self.loop,
            "fade_in_sec": self.fade_in_sec,
            "fade_out_sec": self.fade_out_sec,
        }


def detect_key(genre_code: str, bpm: int) -> str:
    g = get_genre(genre_code)
    # Light variation by BPM parity for deterministic "detection"
    return g.default_key if bpm % 2 == 0 else (g.default_key if "m" in g.default_key else g.default_key + "m").replace("mm", "m")


def validate_generate_request(
    *,
    genre: str | None = None,
    role: str | None = "background",
    bpm: int | None = None,
    key: str | None = None,
    mood: str | None = None,
    energy: float | None = None,
    intensity: float | None = None,
    duration_sec: float | None = None,
    instruments: list[str] | None = None,
    loop: bool | None = None,
    fade_in_sec: float | None = None,
    fade_out_sec: float | None = None,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not is_known_genre(genre or "cinematic"):
        errors.append(f"Invalid genre '{genre}'")
        genre_code = "cinematic"
    else:
        genre_code = normalize_genre(genre)

    g = get_genre(genre_code)
    role_s = (role or "background").lower().strip()
    if role_s not in VALID_ROLES:
        errors.append(f"Invalid role '{role}'. Allowed: {sorted(VALID_ROLES)}")
        role_s = "background"

    bpm_v = int(bpm if bpm is not None else g.default_bpm)
    if bpm_v < MIN_BPM or bpm_v > MAX_BPM:
        errors.append(f"BPM {bpm_v} out of range {MIN_BPM}–{MAX_BPM}")

    key_v = (key or detect_key(genre_code, bpm_v)).strip()
    if key_v not in VALID_KEYS:
        warnings.append(f"Unusual key '{key_v}' — accepting for composition")

    mood_v = (mood or g.default_mood).strip()[:40]
    energy_v = float(energy if energy is not None else g.default_energy)
    intensity_v = float(intensity if intensity is not None else 0.5)
    if not 0.0 <= energy_v <= 1.0:
        errors.append("energy must be between 0 and 1")
    if not 0.0 <= intensity_v <= 1.0:
        errors.append("intensity must be between 0 and 1")

    dur = float(duration_sec if duration_sec is not None else 30.0)
    if dur < MIN_DURATION or dur > MAX_DURATION:
        errors.append(f"duration_sec {dur} out of range {MIN_DURATION}–{MAX_DURATION}")

    try:
        inst = resolve_instruments(instruments, genre_code)
    except ValueError as exc:
        errors.append(str(exc))
        inst = []

    loop_v = bool(loop) if loop is not None else (role_s in ("loop", "background"))
    fade_in = float(fade_in_sec if fade_in_sec is not None else 1.0)
    fade_out = float(fade_out_sec if fade_out_sec is not None else 2.0)
    if fade_in < 0 or fade_out < 0:
        errors.append("fade_in_sec and fade_out_sec must be >= 0")
    if fade_in + fade_out > dur:
        warnings.append("Fade in+out exceeds duration; will clamp at mix time")

    return ValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        genre=genre_code,
        role=role_s,
        bpm=bpm_v,
        key=key_v,
        mood=mood_v,
        energy=energy_v,
        intensity=intensity_v,
        duration_sec=dur,
        instruments=inst,
        loop=loop_v,
        fade_in_sec=fade_in,
        fade_out_sec=fade_out,
    )
