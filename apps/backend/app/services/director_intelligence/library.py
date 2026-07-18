"""Film formats, beats, camera/emotion/environment libraries — extensible."""

from __future__ import annotations

from typing import Any

from app.services.director_intelligence.models import FILM_BEATS

_FORMATS: dict[str, dict[str, Any]] = {
    "short_film": {"runtime_sec": 180.0, "scenes": 8, "shots_per_scene": 3, "audience": "general"},
    "advertisement": {"runtime_sec": 30.0, "scenes": 4, "shots_per_scene": 2, "audience": "consumers"},
    "music_video": {"runtime_sec": 210.0, "scenes": 6, "shots_per_scene": 4, "audience": "music_fans"},
    "podcast": {"runtime_sec": 600.0, "scenes": 5, "shots_per_scene": 1, "audience": "listeners"},
    "islamic_video": {"runtime_sec": 240.0, "scenes": 6, "shots_per_scene": 2, "audience": "faith_community"},
    "educational": {"runtime_sec": 300.0, "scenes": 7, "shots_per_scene": 2, "audience": "learners"},
    "documentary": {"runtime_sec": 480.0, "scenes": 8, "shots_per_scene": 3, "audience": "general"},
    "corporate": {"runtime_sec": 120.0, "scenes": 5, "shots_per_scene": 2, "audience": "professionals"},
    "youtube": {"runtime_sec": 480.0, "scenes": 7, "shots_per_scene": 3, "audience": "youtube"},
    "shorts": {"runtime_sec": 45.0, "scenes": 4, "shots_per_scene": 2, "audience": "mobile"},
    "reels": {"runtime_sec": 30.0, "scenes": 4, "shots_per_scene": 2, "audience": "mobile"},
    "tiktok": {"runtime_sec": 30.0, "scenes": 4, "shots_per_scene": 2, "audience": "mobile"},
}

_CUSTOM_FORMATS: dict[str, dict[str, Any]] = {}

_GENRES = {
    "drama": ("emotional", "serious"),
    "action": ("excited", "tense"),
    "romance": ("romantic", "warm"),
    "comedy": ("happy", "light"),
    "thriller": ("suspense", "fear"),
    "inspirational": ("motivational", "hopeful"),
    "faith": ("calm", "reverent"),
    "documentary": ("serious", "curious"),
    "educational": ("calm", "focused"),
    "corporate": ("professional", "confident"),
}

_CAMERA_ANGLES = (
    "wide",
    "medium",
    "close_up",
    "extreme_close_up",
    "over_shoulder",
    "low_angle",
    "high_angle",
    "tracking",
    "drone",
    "pov",
)

_ENVIRONMENTS = (
    "city",
    "home",
    "office",
    "studio",
    "nature",
    "mosque",
    "school",
    "stage",
    "abstract",
    "custom",
)

_TRANSITIONS = ("cut", "fade", "dissolve", "wipe", "match_cut", "smash_cut")

_MUSIC_CUES = {
    "intro": "ambient_rise",
    "hook": "pulse_hit",
    "story_build": "underscore_build",
    "conflict": "tension_swell",
    "climax": "peak_impact",
    "resolution": "resolve_warm",
    "outro": "fade_outro",
    "credits": "credits_theme",
}


def register_format(format_id: str, spec: dict[str, Any]) -> None:
    key = (format_id or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not key:
        raise ValueError("format_id is required")
    _CUSTOM_FORMATS[key] = {
        "runtime_sec": float(spec.get("runtime_sec") or 60.0),
        "scenes": int(spec.get("scenes") or 4),
        "shots_per_scene": int(spec.get("shots_per_scene") or 2),
        "audience": str(spec.get("audience") or "general"),
        "custom": True,
    }


def resolve_format(fmt: str | None) -> str:
    key = (fmt or "youtube").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "ad": "advertisement",
        "ads": "advertisement",
        "commercial": "advertisement",
        "mv": "music_video",
        "islamic": "islamic_video",
        "edu": "educational",
        "doc": "documentary",
        "yt": "youtube",
        "short": "shorts",
        "reel": "reels",
        "tik_tok": "tiktok",
    }
    key = aliases.get(key, key)
    catalog = {**_FORMATS, **_CUSTOM_FORMATS}
    if key not in catalog:
        register_format(key, {})
    return key


def get_format_spec(fmt: str) -> dict[str, Any]:
    key = resolve_format(fmt)
    return dict({**_FORMATS, **_CUSTOM_FORMATS}[key])


def resolve_genre(genre: str | None) -> str:
    key = (genre or "drama").strip().lower().replace(" ", "_")
    if key not in _GENRES:
        return "drama"
    return key


def beat_sequence_for(fmt: str) -> list[str]:
    spec = get_format_spec(fmt)
    n = int(spec.get("scenes") or 8)
    if n >= 8:
        return list(FILM_BEATS)
    if n >= 6:
        return ["intro", "hook", "story_build", "conflict", "climax", "resolution"]
    if n >= 4:
        return ["hook", "story_build", "climax", "outro"]
    return ["hook", "climax", "outro"][:n]


def camera_for_beat(beat: str, shot_index: int) -> str:
    mapping = {
        "intro": ("wide", "medium"),
        "hook": ("close_up", "tracking"),
        "story_build": ("medium", "over_shoulder", "wide"),
        "conflict": ("low_angle", "close_up", "tracking"),
        "climax": ("extreme_close_up", "drone", "low_angle"),
        "resolution": ("medium", "wide"),
        "outro": ("wide", "high_angle"),
        "credits": ("wide",),
    }
    opts = mapping.get(beat, _CAMERA_ANGLES)
    return opts[shot_index % len(opts)]


def environment_for_beat(beat: str, format_type: str) -> str:
    if format_type == "islamic_video":
        return "mosque" if beat in ("intro", "resolution", "outro") else "studio"
    if format_type in ("corporate", "educational"):
        return "office" if beat != "hook" else "studio"
    if format_type == "podcast":
        return "studio"
    if beat in ("climax", "conflict"):
        return "city"
    if beat in ("resolution", "outro"):
        return "nature"
    if beat == "intro":
        return "home"
    return "custom"


def emotion_for_beat(beat: str, genre: str) -> str:
    moods = _GENRES.get(resolve_genre(genre), ("calm", "serious"))
    beat_map = {
        "intro": moods[0],
        "hook": "excited" if genre == "action" else moods[0],
        "story_build": moods[0],
        "conflict": "tense" if len(moods) > 1 else "serious",
        "climax": moods[-1] if moods else "excited",
        "resolution": "calm",
        "outro": "warm",
        "credits": "calm",
    }
    return beat_map.get(beat, "calm")


def music_for_beat(beat: str) -> str:
    return _MUSIC_CUES.get(beat, "underscore_build")


def list_director_library() -> dict[str, Any]:
    catalog = {**_FORMATS, **_CUSTOM_FORMATS}
    return {
        "formats": [{"format_id": k, **v} for k, v in sorted(catalog.items())],
        "beats": list(FILM_BEATS),
        "genres": list(_GENRES.keys()),
        "camera_angles": list(_CAMERA_ANGLES),
        "environments": list(_ENVIRONMENTS),
        "transitions": list(_TRANSITIONS),
        "format_count": len(catalog),
        "extensible": True,
    }
