"""Request validation for audio timeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    fps: float = 24.0
    duration_sec: float = 0.0
    snap_enabled: bool = True
    auto_align: bool = True
    locked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "fps": self.fps,
            "duration_sec": self.duration_sec,
            "snap_enabled": self.snap_enabled,
            "auto_align": self.auto_align,
            "locked": self.locked,
        }


def validate_timeline_request(
    *,
    fps: float | None = None,
    duration_sec: float | None = None,
    scenes: list[dict[str, Any]] | None = None,
    tracks: list[dict[str, Any]] | None = None,
    snap_enabled: bool = True,
    auto_align: bool = True,
    locked: bool = False,
) -> ValidationResult:
    errors: list[str] = []
    resolved_fps = float(fps) if fps is not None else 24.0
    if resolved_fps <= 0 or resolved_fps > 240:
        errors.append("fps must be between 0 exclusive and 240 inclusive")

    resolved_duration = float(duration_sec) if duration_sec is not None else 0.0
    if duration_sec is not None and resolved_duration < 0:
        errors.append("duration_sec must be >= 0")

    if scenes is not None and not isinstance(scenes, list):
        errors.append("scenes must be a list")
    if tracks is not None and not isinstance(tracks, list):
        errors.append("tracks must be a list")

    return ValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        fps=resolved_fps,
        duration_sec=resolved_duration,
        snap_enabled=bool(snap_enabled),
        auto_align=bool(auto_align),
        locked=bool(locked),
    )
