"""Physics effect catalog — kinds, display names, default specs."""

from __future__ import annotations

from typing import Any

from app.services.physics.models import PhysicsEffectKind

EFFECT_KINDS: tuple[PhysicsEffectKind, ...] = (
    "hair_motion",
    "cloth_motion",
    "rain",
    "smoke",
    "dust",
    "wind",
    "explosion",
    "water",
    "fire",
    "particles",
    "gravity",
)

DISPLAY_NAME: dict[PhysicsEffectKind, str] = {
    "hair_motion": "Hair Motion",
    "cloth_motion": "Cloth Motion",
    "rain": "Rain",
    "smoke": "Smoke",
    "dust": "Dust",
    "wind": "Wind",
    "explosion": "Explosion",
    "water": "Water",
    "fire": "Fire",
    "particles": "Particle Simulation",
    "gravity": "Gravity",
}

EFFECT_SPECS: dict[PhysicsEffectKind, dict[str, Any]] = {
    "hair_motion": {
        "category": "soft_body",
        "description": "Strand dynamics responding to wind, locomotion, and gravity",
    },
    "cloth_motion": {
        "category": "soft_body",
        "description": "Garment / fabric simulation with wind and body collision",
    },
    "rain": {
        "category": "particles",
        "description": "Precipitation streaks with gravity-dominant fall and splash",
    },
    "smoke": {
        "category": "particles",
        "description": "Buoyant volumetric smoke with turbulence and drag",
    },
    "dust": {
        "category": "particles",
        "description": "Fine particulate suspended / kicked by motion and wind",
    },
    "wind": {
        "category": "force",
        "description": "Directional air force driving hair, cloth, and particles",
    },
    "explosion": {
        "category": "impulse",
        "description": "Radial impulse + debris / fire / smoke burst",
    },
    "water": {
        "category": "fluid",
        "description": "Liquid surface, splash, and foam particle response",
    },
    "fire": {
        "category": "particles",
        "description": "Combustion plume with heat rise and flicker",
    },
    "particles": {
        "category": "particles",
        "description": "Generic particle simulation layer",
    },
    "gravity": {
        "category": "force",
        "description": "Downward acceleration baseline for all dynamic sims",
    },
}


def display(kind: PhysicsEffectKind) -> str:
    return DISPLAY_NAME.get(kind, kind)


def spec(kind: PhysicsEffectKind) -> dict[str, Any]:
    return dict(EFFECT_SPECS.get(kind, {}))
