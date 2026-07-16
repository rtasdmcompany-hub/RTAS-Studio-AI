"""Hair and cloth soft-body simulation parameters."""

from __future__ import annotations

from app.services.physics.models import SoftBodySim


def build_hair_sim(
    *,
    wind_strength: float,
    locomotion: str | None = None,
    intensity: float = 0.55,
) -> SoftBodySim:
    loco = (locomotion or "").lower()
    wind_resp = min(1.0, 0.35 + wind_strength * 0.55 + intensity * 0.2)
    if loco == "running":
        wind_resp = min(1.0, wind_resp + 0.2)
    stiffness = 0.45 if loco in ("running", "walking") else 0.55
    return SoftBodySim(
        kind="hair",
        stiffness=round(stiffness, 3),
        damping=0.42,
        wind_response=round(wind_resp, 3),
        gravity_scale=0.9,
        collision=True,
        notes="strand follow-through; avoid stiff helmet hair",
    )


def build_cloth_sim(
    *,
    wind_strength: float,
    locomotion: str | None = None,
    intensity: float = 0.55,
) -> SoftBodySim:
    loco = (locomotion or "").lower()
    wind_resp = min(1.0, 0.4 + wind_strength * 0.5 + intensity * 0.15)
    if loco in ("running", "walking"):
        wind_resp = min(1.0, wind_resp + 0.15)
    return SoftBodySim(
        kind="cloth",
        stiffness=0.38,
        damping=0.5,
        wind_response=round(wind_resp, 3),
        gravity_scale=1.0,
        collision=True,
        notes="fabric secondary motion; folds follow body acceleration",
    )
