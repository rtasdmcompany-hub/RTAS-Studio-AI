"""Video / Director / Timeline / Music / Voice adaptation for SFX & ambient."""

from __future__ import annotations

from typing import Any

from app.services.sfx_ambient.categories import is_known_category, normalize_category
from app.services.sfx_ambient.scene_intelligence import build_environment_profile


def _duration_from_scenes(scenes: list[dict[str, Any]] | None) -> float:
    if not scenes:
        return 12.0
    total = 0.0
    for s in scenes:
        if not isinstance(s, dict):
            continue
        d = s.get("duration_sec") or s.get("duration") or s.get("estimated_duration")
        if d is not None:
            try:
                total += float(d)
            except (TypeError, ValueError):
                pass
    return max(4.0, total or 12.0)


def _categories_from_director(audio_director: dict[str, Any] | None) -> list[str]:
    out: list[str] = []
    if not audio_director:
        return out
    for key in ("sfx_timeline", "ambient_timeline"):
        timeline = audio_director.get(key) or []
        if not isinstance(timeline, list):
            continue
        for item in timeline[:12]:
            if not isinstance(item, dict):
                continue
            cat = item.get("category") or item.get("label") or item.get("kind")
            if cat and is_known_category(str(cat).split()[0]):
                try:
                    out.append(normalize_category(str(cat).split()[0]))
                except ValueError:
                    pass
            meta = item.get("metadata") or {}
            if isinstance(meta, dict):
                mc = meta.get("category") or meta.get("style")
                if mc and is_known_category(str(mc)):
                    try:
                        out.append(normalize_category(str(mc)))
                    except ValueError:
                        pass
    # dedupe
    seen: set[str] = set()
    uniq: list[str] = []
    for c in out:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


def adapt_from_video_context(
    *,
    prompt: str | None = None,
    audio_director: dict[str, Any] | None = None,
    video_engine: dict[str, Any] | None = None,
    director: dict[str, Any] | None = None,
    scenes: list[dict[str, Any]] | None = None,
    music_summary: dict[str, Any] | None = None,
    camera_motion: dict[str, Any] | str | None = None,
    explicit_categories: list[str] | None = None,
    explicit_environment: str | None = None,
) -> dict[str, Any]:
    """Derive SFX/ambient params that sync with scene, camera, music, timeline."""
    profile = build_environment_profile(
        prompt=prompt,
        scenes=scenes,
        audio_director=audio_director,
        explicit_environment=explicit_environment,
    )
    duration = _duration_from_scenes(scenes)
    if video_engine and isinstance(video_engine, dict):
        d = video_engine.get("duration_sec") or video_engine.get("duration")
        if d is not None:
            try:
                duration = max(duration, float(d))
            except (TypeError, ValueError):
                pass

    cats = list(explicit_categories or [])
    if not cats:
        cats = _categories_from_director(audio_director)
    if not cats:
        cats = list(profile.recommended_categories)

    # Camera motion → volume / distance
    cam = "static"
    if isinstance(camera_motion, str):
        cam = camera_motion.lower()
    elif isinstance(camera_motion, dict):
        cam = str(
            camera_motion.get("motion")
            or camera_motion.get("type")
            or camera_motion.get("camera_motion")
            or "static"
        ).lower()

    volume = 0.45
    if cam in ("handheld", "whip", "orbit"):
        volume = 0.65
    elif cam in ("static", "pan"):
        volume = 0.4

    # Duck ambient under music slightly when music is intense
    if music_summary and float(music_summary.get("energy") or 0) >= 0.75:
        volume = max(0.2, volume - 0.15)

    story_beat = None
    if director and isinstance(director, dict):
        notes = director.get("director_notes") or director.get("emotional_pacing")
        if isinstance(notes, list) and notes:
            story_beat = str(notes[0])
        elif isinstance(notes, str):
            story_beat = notes

    return {
        "environment": profile.environment,
        "mood": profile.mood,
        "energy": profile.energy,
        "categories": cats[:8],
        "duration_sec": round(duration, 3),
        "volume": round(volume, 3),
        "scene_id": profile.scene_id,
        "camera_motion": cam,
        "story_beat": story_beat,
        "recommended": profile.recommended_categories,
        "environment_profile": profile,
    }
