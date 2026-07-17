"""Scene audio intelligence — detect environment & recommend SFX/ambient."""

from __future__ import annotations

import re
from typing import Any

from app.services.sfx_ambient.categories import recommend_for_mood
from app.services.sfx_ambient.models import EnvironmentProfile

_ENV_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ocean", ("ocean", "beach", "sea", "coast", "shore")),
    ("forest", ("forest", "woods", "jungle", "trees")),
    ("city", ("city", "street", "urban", "traffic", "downtown")),
    ("office", ("office", "desk", "meeting", "corporate")),
    ("factory", ("factory", "industrial", "warehouse", "plant")),
    ("market", ("market", "bazaar", "souk", "stalls")),
    ("desert", ("desert", "dunes", "arid", "sandstorm")),
    ("snow", ("snow", "winter", "blizzard", "ice")),
    ("space", ("space", "spaceship", "orbit", "galaxy")),
    ("sci-fi", ("sci-fi", "scifi", "cyber", "neon", "futuristic")),
    ("rain", ("rain", "storm", "thunderstorm", "downpour")),
    ("nature", ("nature", "park", "garden", "meadow", "field")),
    ("river", ("river", "stream", "creek")),
    ("fire", ("fire", "campfire", "flame", "burning")),
)


def detect_environment(prompt: str | None, scenes: list[dict[str, Any]] | None = None) -> str:
    text_parts: list[str] = [prompt or ""]
    for s in scenes or []:
        if isinstance(s, dict):
            text_parts.append(str(s.get("location") or ""))
            text_parts.append(str(s.get("setting") or ""))
            text_parts.append(str(s.get("description") or ""))
            text_parts.append(str(s.get("environment") or ""))
    lower = " ".join(text_parts).lower()
    for env, keys in _ENV_HINTS:
        for k in keys:
            if re.search(rf"\b{re.escape(k)}\b", lower):
                return env
    return "nature"


def detect_mood(
    *,
    prompt: str | None = None,
    scenes: list[dict[str, Any]] | None = None,
    audio_director: dict[str, Any] | None = None,
) -> str:
    if scenes and isinstance(scenes[0], dict):
        emo = scenes[0].get("emotion") or scenes[0].get("emotional_beat") or scenes[0].get("mood")
        if emo:
            return str(emo).lower().strip()
    mt = (audio_director or {}).get("music_timeline") or []
    if isinstance(mt, list) and mt and isinstance(mt[0], dict):
        m = mt[0].get("mood") or mt[0].get("emotion")
        if m:
            return str(m).lower().strip()
    lower = (prompt or "").lower()
    for mood in ("action", "tense", "sad", "romantic", "calm", "dramatic", "happy", "horror"):
        if mood in lower:
            return mood
    return "neutral"


def build_environment_profile(
    *,
    prompt: str | None = None,
    scenes: list[dict[str, Any]] | None = None,
    audio_director: dict[str, Any] | None = None,
    scene_id: str | None = None,
    explicit_environment: str | None = None,
    explicit_mood: str | None = None,
) -> EnvironmentProfile:
    env = (explicit_environment or detect_environment(prompt, scenes)).lower().strip()
    mood = (explicit_mood or detect_mood(prompt=prompt, scenes=scenes, audio_director=audio_director)).lower()
    energy = 0.5
    if mood in ("action", "tense", "horror", "dramatic"):
        energy = 0.85
    elif mood in ("calm", "peaceful", "romantic", "sad"):
        energy = 0.3

    # Environment → primary categories
    env_map = {
        "ocean": ["ocean", "wind", "birds"],
        "forest": ["forest", "birds", "animals", "wind"],
        "city": ["city-traffic", "crowd", "footsteps"],
        "office": ["office", "ui-sounds", "footsteps"],
        "factory": ["factory", "mechanical"],
        "market": ["market", "crowd", "footsteps"],
        "desert": ["desert", "wind"],
        "snow": ["snow", "wind", "footsteps"],
        "space": ["space", "sci-fi"],
        "sci-fi": ["sci-fi", "mechanical", "ui-sounds"],
        "rain": ["rain", "thunder", "wind"],
        "river": ["river", "birds", "nature"],
        "fire": ["fire", "wind"],
        "nature": ["nature", "birds", "wind"],
    }
    primary = list(env_map.get(env, ["nature", "wind"]))
    mood_recs = recommend_for_mood(mood, limit=4)
    merged: list[str] = []
    for c in primary + mood_recs:
        if c not in merged:
            merged.append(c)

    sid = scene_id
    if not sid and scenes and isinstance(scenes[0], dict):
        sid = str(scenes[0].get("id") or scenes[0].get("scene_id") or "scene_1")

    return EnvironmentProfile(
        environment=env,
        mood=mood,
        energy=energy,
        recommended_categories=merged[:8],
        scene_id=sid,
        metadata={"source": "scene_audio_intelligence"},
    )
