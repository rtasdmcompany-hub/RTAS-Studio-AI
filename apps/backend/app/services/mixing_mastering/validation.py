"""Validate mix / master requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    target_lufs: float = -14.0
    true_peak_ceiling: float = -1.0
    export_format: str = "wav"
    sample_rate: int = 48000
    bit_depth: int = 24

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "target_lufs": self.target_lufs,
            "true_peak_ceiling": self.true_peak_ceiling,
            "export_format": self.export_format,
            "sample_rate": self.sample_rate,
            "bit_depth": self.bit_depth,
        }


_ALLOWED_FORMATS = {"wav", "mp3", "flac", "aac", "ogg"}
_ALLOWED_RATES = {44100, 48000, 96000}
_ALLOWED_DEPTHS = {16, 24, 32}


def validate_mix_master_request(
    *,
    target_lufs: float | None = None,
    true_peak_ceiling: float | None = None,
    export_format: str | None = None,
    sample_rate: int | None = None,
    bit_depth: int | None = None,
    music_ducking_db: float | None = None,
    compression_ratio: float | None = None,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    lufs = -14.0 if target_lufs is None else float(target_lufs)
    if lufs > -6.0 or lufs < -30.0:
        errors.append("target_lufs must be between -30 and -6")

    peak = -1.0 if true_peak_ceiling is None else float(true_peak_ceiling)
    if peak > 0.0 or peak < -6.0:
        errors.append("true_peak_ceiling must be between -6 and 0 dBTP")

    fmt = (export_format or "wav").lower().strip()
    if fmt not in _ALLOWED_FORMATS:
        errors.append(f"export_format must be one of {sorted(_ALLOWED_FORMATS)}")

    rate = 48000 if sample_rate is None else int(sample_rate)
    if rate not in _ALLOWED_RATES:
        errors.append(f"sample_rate must be one of {sorted(_ALLOWED_RATES)}")

    depth = 24 if bit_depth is None else int(bit_depth)
    if depth not in _ALLOWED_DEPTHS:
        errors.append(f"bit_depth must be one of {sorted(_ALLOWED_DEPTHS)}")

    if music_ducking_db is not None and (music_ducking_db > 0 or music_ducking_db < -24):
        errors.append("music_ducking_db must be between -24 and 0")

    if compression_ratio is not None and (compression_ratio < 1.0 or compression_ratio > 20.0):
        errors.append("compression_ratio must be between 1 and 20")

    if fmt == "mp3" and depth > 16:
        warnings.append("mp3 ignores bit_depth; encoded as lossy")

    return ValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        target_lufs=lufs,
        true_peak_ceiling=peak,
        export_format=fmt,
        sample_rate=rate,
        bit_depth=depth,
    )
