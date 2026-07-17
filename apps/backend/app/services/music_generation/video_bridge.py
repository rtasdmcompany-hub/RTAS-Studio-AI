"""Video Engine / Director / Scene adaptation for music."""

from __future__ import annotations

from typing import Any

from app.services.music_generation.genres import is_known_genre, normalize_genre


_EMOTION_GENRE = {
    "happy": "corporate",
    "joy": "corporate",
    "sad": "sad",
    "melancholy": "sad",
    "romantic": "romantic",
    "love": "romantic",
    "fear": "horror",
    "tense": "horror",
    "action": "action",
    "intense": "action",
    "epic": "epic",
    "heroic": "epic",
    "calm": "ambient",
    "peaceful": "ambient",
    "futuristic": "sci-fi",
    "tech": "sci-fi",
    "documentary": "documentary",
    "emotional": "emotional",
    "dramatic": "cinematic",
}

_CAMERA_ENERGY = {
    "static": 0.3,
    "pan": 0.45,
    "tilt": 0.45,
    "dolly": 0.55,
    "tracking": 0.65,
    "handheld": 0.75,
    "crane": 0.7,
    "orbit": 0.8,
    "whip": 0.95,
}


def infer_genre_from_context(
    *,
    prompt: str | None = None,
    scene_emotion: str | None = None,
    audio_director: dict[str, Any] | None = None,
    explicit_genre: str | None = None,
) -> str:
    if explicit_genre and is_known_genre(explicit_genre):
        return normalize_genre(explicit_genre)

    mt = (audio_director or {}).get("music_timeline") or []
    if isinstance(mt, list) and mt and isinstance(mt[0], dict):
        g = mt[0].get("genre") or mt[0].get("style")
        if g and is_known_genre(str(g).split()[0]):
            try:
                return normalize_genre(str(g).split()[0])
            except ValueError:
                pass

    emo = (scene_emotion or "").lower().strip()
    if emo in _EMOTION_GENRE:
        return _EMOTION_GENRE[emo]

    lower = (prompt or "").lower()
    for key, genre in _EMOTION_GENRE.items():
        if key in lower:
            return genre
    if "horror" in lower:
        return "horror"
    if "action" in lower:
        return "action"
    if "lofi" in lower or "lo-fi" in lower:
        return "lo-fi"
    return "cinematic"


def adapt_from_video_context(
    *,
    prompt: str | None = None,
    audio_director: dict[str, Any] | None = None,
    video_engine: dict[str, Any] | None = None,
    director: dict[str, Any] | None = None,
    scenes: list[dict[str, Any]] | None = None,
    character_memory: list[dict[str, Any]] | None = None,
    camera_motion: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    """Derive music params that adapt to scene length, emotion, story, camera."""
    scene_emotion = None
    scene_duration = 30.0
    story_beat = None
    cam = "static"

    if scenes and isinstance(scenes[0], dict):
        scene_emotion = str(
            scenes[0].get("emotion")
            or scenes[0].get("emotional_beat")
            or scenes[0].get("mood")
            or ""
        ) or None
        scene_duration = float(
            scenes[0].get("duration_sec")
            or scenes[0].get("duration")
            or scene_duration
        )
        story_beat = str(scenes[0].get("beat") or scenes[0].get("label") or "") or None

    if director:
        pacing = director.get("emotional_pacing") or []
        if isinstance(pacing, list) and pacing:
            scene_emotion = scene_emotion or str(pacing[0])
        decisions = director.get("decisions") or []
        if isinstance(decisions, list) and decisions and isinstance(decisions[0], dict):
            scene_emotion = scene_emotion or str(decisions[0].get("emotional_beat") or "")

    if isinstance(camera_motion, dict):
        cam = str(camera_motion.get("type") or camera_motion.get("motion") or "static")
    elif isinstance(camera_motion, str) and camera_motion:
        cam = camera_motion

    if video_engine:
        scene_duration = float(
            video_engine.get("duration_sec")
            or video_engine.get("estimated_duration_sec")
            or scene_duration
        )

    genre = infer_genre_from_context(
        prompt=prompt,
        scene_emotion=scene_emotion,
        audio_director=audio_director,
    )

    energy = _CAMERA_ENERGY.get(cam.lower().split()[0], 0.55)
    if scene_emotion and scene_emotion.lower() in ("intense", "action", "epic"):
        energy = min(1.0, energy + 0.2)
    if scene_emotion and scene_emotion.lower() in ("sad", "calm", "romantic"):
        energy = max(0.15, energy - 0.2)

    # Character memory can bias mood (e.g. emotion_profile)
    mood_bias = None
    if character_memory and isinstance(character_memory[0], dict):
        mood_bias = character_memory[0].get("emotion_profile")

    role = "background"
    if story_beat and "intro" in str(story_beat).lower():
        role = "intro"
    elif story_beat and "outro" in str(story_beat).lower():
        role = "outro"

    return {
        "genre": genre,
        "role": role,
        "duration_sec": max(2.0, min(600.0, scene_duration)),
        "energy": round(energy, 3),
        "intensity": round(min(1.0, energy * 0.9 + 0.1), 3),
        "scene_emotion": scene_emotion or mood_bias,
        "scene_duration_sec": scene_duration,
        "camera_motion": cam,
        "story_beat": story_beat,
        "loop": role == "background",
    }
