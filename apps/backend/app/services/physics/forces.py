"""Gravity, wind, and related force fields."""

from __future__ import annotations

from app.services.physics.models import ForceField


def build_gravity(*, strength: float = 1.0, low_gravity: bool = False) -> ForceField:
    g = 0.15 if low_gravity else strength
    return ForceField(
        kind="gravity",
        vector=(0.0, -9.81 * g, 0.0),
        strength=round(g, 3),
        turbulence=0.0,
        notes="world gravity" if not low_gravity else "reduced gravity",
    )


def build_wind(
    text: str,
    *,
    intensity: float,
    storm: bool = False,
) -> ForceField:
    t = (text or "").lower()
    # Direction heuristics
    x, z = 1.0, 0.2
    if "left" in t:
        x = -1.0
    elif "right" in t:
        x = 1.0
    if "toward camera" in t or "into camera" in t:
        z = 1.0
    elif "away" in t:
        z = -1.0

    strength = min(1.5, max(0.15, intensity * (1.35 if storm else 1.0)))
    turb = min(1.0, 0.2 + strength * 0.45)
    return ForceField(
        kind="wind",
        vector=(round(x * strength * 4.0, 3), round(0.15 * strength, 3), round(z * strength * 2.5, 3)),
        strength=round(strength, 3),
        turbulence=round(turb, 3),
        notes="gusting" if storm or strength > 0.85 else "steady breeze",
    )


def build_explosion_impulse(*, intensity: float) -> ForceField:
    s = min(2.0, max(0.4, intensity * 1.6))
    return ForceField(
        kind="turbulence",
        vector=(0.0, s * 3.0, 0.0),
        strength=round(s, 3),
        turbulence=round(min(1.0, s), 3),
        notes="radial blast impulse",
    )


def build_drag(*, intensity: float = 0.35) -> ForceField:
    return ForceField(
        kind="drag",
        vector=(0.0, 0.0, 0.0),
        strength=round(max(0.1, min(1.0, intensity)), 3),
        turbulence=0.0,
        notes="air resistance",
    )


def build_buoyancy(*, intensity: float = 0.4) -> ForceField:
    return ForceField(
        kind="buoyancy",
        vector=(0.0, round(2.5 * intensity, 3), 0.0),
        strength=round(intensity, 3),
        turbulence=0.15,
        notes="thermal / fluid rise",
    )
