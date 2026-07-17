"""Loudness, frequency, and audio quality analysis (simulation-accurate formulas)."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.mixing_mastering.models import (
    AudioQualityReport,
    FrequencyAnalysis,
    LoudnessReport,
)
from app.services.mixing_mastering.version import TARGET_LUFS, TRUE_PEAK_CEILING_DBTP


def _seed(parts: list[str]) -> int:
    digest = hashlib.sha1("|".join(parts).encode()).hexdigest()
    return int(digest[:8], 16)


def analyze_loudness(
    *,
    job_id: str,
    target_lufs: float = TARGET_LUFS,
    true_peak_ceiling: float = TRUE_PEAK_CEILING_DBTP,
    pre_normalized: bool = False,
) -> LoudnessReport:
    n = _seed([job_id, "loudness"])
    # Pre-mix levels slightly hot; post-master snaps to target
    if pre_normalized:
        integrated = target_lufs + ((n % 7) - 3) * 0.05
        peak = true_peak_ceiling - 0.1 - (n % 20) * 0.01
    else:
        integrated = -18.0 + (n % 80) / 10.0  # roughly -18..-10
        peak = -0.2 - (n % 30) * 0.05
    short = integrated + 0.8
    momentary = integrated + 1.5
    lra = 4.0 + (n % 50) / 10.0
    return LoudnessReport(
        integrated_lufs=round(integrated, 2),
        short_term_lufs=round(short, 2),
        momentary_lufs=round(momentary, 2),
        true_peak_dbtp=round(peak, 2),
        peak_dbfs=round(peak - 0.3, 2),
        loudness_range_lu=round(lra, 2),
        normalized=pre_normalized,
    )


def analyze_frequency(*, job_id: str, voice_boost: bool = True) -> FrequencyAnalysis:
    n = _seed([job_id, "freq"])
    low = 0.25 + (n % 20) / 100.0
    mid = 0.4 + (n % 25) / 100.0
    high = 0.2 + (n % 15) / 100.0
    if voice_boost:
        mid = min(0.7, mid + 0.08)
    total = low + mid + high
    low, mid, high = low / total, mid / total, high / total
    centroid = 800 + (n % 2400)
    balance = 1.0 - abs(mid - 0.45) - abs(low - 0.3) * 0.5
    return FrequencyAnalysis(
        low_energy=round(low, 3),
        mid_energy=round(mid, 3),
        high_energy=round(high, 3),
        spectral_centroid_hz=float(centroid),
        tonal_balance_score=round(max(0.0, min(1.0, balance)), 3),
        bands={
            "sub": round(low * 0.4, 3),
            "bass": round(low * 0.6, 3),
            "low_mid": round(mid * 0.4, 3),
            "presence": round(mid * 0.6, 3),
            "air": round(high, 3),
        },
    )


def _grade(score: float) -> str:
    if score >= 0.9:
        return "A"
    if score >= 0.8:
        return "B"
    if score >= 0.7:
        return "C"
    return "D"


def build_quality_report(
    *,
    loudness: LoudnessReport,
    frequency: FrequencyAnalysis,
    stereo_width: float,
    noise_floor_db: float,
    dynamic_range_db: float,
    target_lufs: float = TARGET_LUFS,
    true_peak_ceiling: float = TRUE_PEAK_CEILING_DBTP,
) -> AudioQualityReport:
    lufs_err = abs(loudness.integrated_lufs - target_lufs)
    lufs_score = max(0.0, 1.0 - lufs_err / 6.0)
    peak_ok = loudness.true_peak_dbtp <= true_peak_ceiling + 0.05
    peak_score = 1.0 if peak_ok else 0.5
    clarity = round(
        0.35 * frequency.tonal_balance_score
        + 0.35 * lufs_score
        + 0.15 * min(1.0, stereo_width / 1.2)
        + 0.15 * (1.0 if noise_floor_db <= -50 else 0.6),
        3,
    )
    freq_bal = frequency.tonal_balance_score
    overall = round(
        0.3 * lufs_score
        + 0.2 * peak_score
        + 0.2 * freq_bal
        + 0.15 * clarity
        + 0.15 * min(1.0, dynamic_range_db / 10.0),
        3,
    )
    notes: list[str] = []
    if lufs_err > 1.0:
        notes.append(f"LUFS deviation {lufs_err:.2f} from target {target_lufs}")
    if not peak_ok:
        notes.append("True peak exceeds ceiling")
    if noise_floor_db > -45:
        notes.append("Elevated noise floor")
    production_ready = overall >= 0.75 and peak_ok and lufs_err <= 2.0
    return AudioQualityReport(
        lufs=loudness.integrated_lufs,
        peak_dbfs=loudness.peak_dbfs,
        true_peak_dbtp=loudness.true_peak_dbtp,
        dynamic_range_db=round(dynamic_range_db, 2),
        stereo_width=round(stereo_width, 3),
        noise_floor_db=round(noise_floor_db, 1),
        frequency_balance=round(freq_bal, 3),
        clarity_score=clarity,
        overall_score=overall,
        grade=_grade(overall),
        production_ready=production_ready,
        notes=notes,
    )


def parallel_analyze(
    job_id: str,
    *,
    target_lufs: float,
    true_peak_ceiling: float,
    stereo_width: float,
    normalized: bool,
) -> dict[str, Any]:
    """Run loudness + frequency analysis (conceptually parallel)."""
    loudness = analyze_loudness(
        job_id=job_id,
        target_lufs=target_lufs,
        true_peak_ceiling=true_peak_ceiling,
        pre_normalized=normalized,
    )
    frequency = analyze_frequency(job_id=job_id, voice_boost=True)
    n = _seed([job_id, "noise"])
    noise = -62.0 + (n % 12)
    dyn = 6.0 + (n % 40) / 10.0
    quality = build_quality_report(
        loudness=loudness,
        frequency=frequency,
        stereo_width=stereo_width,
        noise_floor_db=noise,
        dynamic_range_db=dyn,
        target_lufs=target_lufs,
        true_peak_ceiling=true_peak_ceiling,
    )
    return {
        "loudness": loudness,
        "frequency": frequency,
        "quality": quality,
        "noise_floor_db": noise,
        "dynamic_range_db": dyn,
    }
