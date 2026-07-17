"""Validate SFX / ambient generate requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.sfx_ambient.categories import get_category, normalize_category


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    duration_sec: float = 12.0
    volume: float = 0.5
    fade_in_sec: float = 0.5
    fade_out_sec: float = 1.0
    loop: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "categories": list(self.categories),
            "duration_sec": self.duration_sec,
            "volume": self.volume,
            "fade_in_sec": self.fade_in_sec,
            "fade_out_sec": self.fade_out_sec,
            "loop": self.loop,
        }


def validate_generate_request(
    *,
    categories: list[str] | None = None,
    category: str | None = None,
    duration_sec: float | None = None,
    volume: float | None = None,
    fade_in_sec: float | None = None,
    fade_out_sec: float | None = None,
    loop: bool | None = None,
    kind: str | None = None,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    cats: list[str] = []

    raw = list(categories or [])
    if category:
        raw.insert(0, category)
    if not raw:
        errors.append("At least one category is required")
    else:
        for c in raw:
            try:
                cats.append(normalize_category(c))
            except ValueError as exc:
                errors.append(str(exc))

    # Deduplicate preserving order
    seen: set[str] = set()
    uniq: list[str] = []
    for c in cats:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    cats = uniq[:12]

    dur = 12.0 if duration_sec is None else float(duration_sec)
    if dur < 0.1:
        errors.append("duration_sec must be >= 0.1")
    if dur > 600:
        errors.append("duration_sec must be <= 600")

    vol = 0.5 if volume is None else float(volume)
    if vol < 0.0 or vol > 1.0:
        errors.append("volume must be between 0 and 1")

    fi = 0.5 if fade_in_sec is None else float(fade_in_sec)
    fo = 1.0 if fade_out_sec is None else float(fade_out_sec)
    if fi < 0 or fo < 0:
        errors.append("fade times must be >= 0")
    if fi + fo > dur and dur > 0:
        warnings.append("fade_in + fade_out exceed duration; will compress")

    do_loop = bool(loop) if loop is not None else False
    if cats and do_loop is False:
        # Ambient categories prefer loop
        try:
            if get_category(cats[0]).loopable and kind in (None, "ambient"):
                do_loop = True
        except ValueError:
            pass

    return ValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        categories=cats,
        duration_sec=round(dur, 3),
        volume=round(vol, 3),
        fade_in_sec=round(fi, 3),
        fade_out_sec=round(fo, 3),
        loop=do_loop,
    )
