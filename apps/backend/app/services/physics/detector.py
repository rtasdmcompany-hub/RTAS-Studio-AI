"""Detect physics effects from prompt, weather, environment, and actions."""

from __future__ import annotations

import re
from typing import Any

from app.services.physics.models import PhysicsEffectKind

_PATTERNS: list[tuple[PhysicsEffectKind, re.Pattern[str], float]] = [
    ("explosion", re.compile(r"\b(explosions?|explosive|explodes?|exploding|blast|detonation|boom)\b", re.I), 1.0),
    ("fire", re.compile(r"\b(fire|flames?|burning|inferno|embers?|blaze)\b", re.I), 0.95),
    ("rain", re.compile(r"\b(rain|raining|rainfall|downpour|drizzle|storm)\b", re.I), 0.95),
    ("water", re.compile(r"\b(water|ocean|sea|river|lake|splash|waves?|flood|wet)\b", re.I), 0.9),
    ("smoke", re.compile(r"\b(smoke|smoky|haze|fog|mist)\b", re.I), 0.88),
    ("dust", re.compile(r"\b(dust|dusty|sand|particles? in air|debris)\b", re.I), 0.85),
    ("wind", re.compile(r"\b(wind|windy|breeze|gust|gale|blowing)\b", re.I), 0.9),
    ("hair_motion", re.compile(r"\b(hair|locks?|mane|braid)\b", re.I), 0.7),
    ("cloth_motion", re.compile(r"\b(cloth|clothing|fabric|dress|cape|coat|scarf|skirt|robe)\b", re.I), 0.7),
    ("particles", re.compile(r"\b(particles?|sparks?|embers?|ash|confetti)\b", re.I), 0.75),
    ("gravity", re.compile(r"\b(gravity|falling|falls|drop|weightless|zero.?g)\b", re.I), 0.65),
]


def score_effects(text: str) -> dict[PhysicsEffectKind, float]:
    blob = (text or "").strip()
    scores: dict[PhysicsEffectKind, float] = {}
    if not blob:
        return scores
    for kind, pat, weight in _PATTERNS:
        if pat.search(blob):
            scores[kind] = max(scores.get(kind, 0.0), weight)
    return scores


def detect_effects(
    text: str,
    *,
    weather: str | None = None,
    environment: str | None = None,
    actions: list[str] | None = None,
    prompt_understanding: dict[str, Any] | None = None,
    always_soft_body: bool = True,
) -> list[tuple[PhysicsEffectKind, float]]:
    parts = [
        text or "",
        weather or "",
        environment or "",
        " ".join(actions or []),
    ]
    pu = prompt_understanding or {}
    for key in ("weather", "environment", "scene_type", "lighting"):
        if pu.get(key):
            parts.append(str(pu[key]))
    blob = " ".join(p for p in parts if p)

    scores = score_effects(blob)

    # Weather shortcuts
    w = (weather or str(pu.get("weather") or "")).lower()
    if "rain" in w or "storm" in w:
        scores["rain"] = max(scores.get("rain", 0.0), 0.95)
        scores["wind"] = max(scores.get("wind", 0.0), 0.55)
    if "wind" in w:
        scores["wind"] = max(scores.get("wind", 0.0), 0.9)

    # Soft-body defaults when characters implied
    if always_soft_body:
        if any(x in blob.lower() for x in ("person", "woman", "man", "character", "girl", "boy", "actor")):
            scores["hair_motion"] = max(scores.get("hair_motion", 0.0), 0.55)
            scores["cloth_motion"] = max(scores.get("cloth_motion", 0.0), 0.55)
        # Locomotion / wind implies secondary soft body
        if scores.get("wind", 0) >= 0.5 or any(
            a in blob.lower() for a in ("walk", "run", "turn")
        ):
            scores["hair_motion"] = max(scores.get("hair_motion", 0.0), 0.5)
            scores["cloth_motion"] = max(scores.get("cloth_motion", 0.0), 0.5)

    # Gravity always present as baseline field (low score unless explicit)
    scores["gravity"] = max(scores.get("gravity", 0.0), 0.4)

    # Explosion implies fire/smoke/dust particles
    if scores.get("explosion", 0) >= 0.8:
        scores["fire"] = max(scores.get("fire", 0.0), 0.7)
        scores["smoke"] = max(scores.get("smoke", 0.0), 0.75)
        scores["dust"] = max(scores.get("dust", 0.0), 0.6)
        scores["particles"] = max(scores.get("particles", 0.0), 0.8)

    if scores.get("fire", 0) >= 0.8:
        scores["smoke"] = max(scores.get("smoke", 0.0), 0.55)
        scores["particles"] = max(scores.get("particles", 0.0), 0.6)

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    # Keep meaningful effects
    return [(k, s) for k, s in ranked if s >= 0.45]
