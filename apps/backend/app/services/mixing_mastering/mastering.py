"""Mastering — LUFS normalize, true peak, stereo width, export opts."""

from __future__ import annotations

from app.services.mixing_mastering.models import MasterProfile
from app.services.mixing_mastering.version import TARGET_LUFS, TRUE_PEAK_CEILING_DBTP


def build_master_profile(
    *,
    target_lufs: float | None = None,
    true_peak_ceiling: float | None = None,
    stereo_width: float | None = None,
    noise_reduction: bool = True,
    dynamic_range_target_db: float | None = None,
) -> MasterProfile:
    return MasterProfile(
        target_lufs=TARGET_LUFS if target_lufs is None else float(target_lufs),
        true_peak_ceiling_dbtp=(
            TRUE_PEAK_CEILING_DBTP
            if true_peak_ceiling is None
            else float(true_peak_ceiling)
        ),
        stereo_width=1.15 if stereo_width is None else float(stereo_width),
        tonal_balance="broadcast",
        noise_reduction=noise_reduction,
        dynamic_range_target_db=(
            8.0 if dynamic_range_target_db is None else float(dynamic_range_target_db)
        ),
    )


def describe_master_chain(profile: MasterProfile) -> list[str]:
    return [
        f"lufs_normalize:{profile.target_lufs}",
        f"true_peak_limit:{profile.true_peak_ceiling_dbtp}dBTP",
        f"stereo_width:{profile.stereo_width}",
        f"noise_reduction:{profile.noise_reduction}",
        f"dynamic_range_target:{profile.dynamic_range_target_db}dB",
        f"tonal_balance:{profile.tonal_balance}",
    ]
