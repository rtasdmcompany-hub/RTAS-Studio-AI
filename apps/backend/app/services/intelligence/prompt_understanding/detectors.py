"""Reusable cinematic detectors — one concern per function."""

from __future__ import annotations

import re

from app.services.intelligence.prompt_understanding.lexicon import (
    CAMERA_KEYWORDS,
    CATEGORY_KEYWORDS,
    COLOR_PALETTE_KEYWORDS,
    EMOTION_KEYWORDS,
    ENVIRONMENT_KEYWORDS,
    LENS_KEYWORDS,
    LIGHTING_KEYWORDS,
    MOOD_KEYWORDS,
    MOVEMENT_KEYWORDS,
    MUSIC_KEYWORDS,
    TIME_KEYWORDS,
    TRANSITION_BY_CATEGORY,
    WEATHER_KEYWORDS,
)

_SUBJECT_COUNT_PATTERNS: tuple[tuple[re.Pattern[str], int], ...] = (
    (re.compile(r"\b(crowd|group|team|family|people)\b", re.I), 4),
    (re.compile(r"\b(two|couple|pair|duo)\b", re.I), 2),
    (re.compile(r"\b(three|trio)\b", re.I), 3),
    (re.compile(r"\b(alone|lonely|solitary|one person)\b", re.I), 1),
    (re.compile(r"\b(a man|a woman|a boy|a girl|a person|someone)\b", re.I), 1),
)


def _matches(text: str, keywords: tuple[str, ...]) -> bool:
    return any(k in text for k in keywords)


def collect_labels(text: str, table: dict[str, tuple[str, ...]]) -> list[str]:
    found: list[str] = []
    for label, keys in table.items():
        if _matches(text, keys):
            found.append(label)
    return found


def first_label(
    text: str,
    table: dict[str, tuple[str, ...]],
    default: str,
) -> str:
    for label, keys in table.items():
        if _matches(text, keys):
            return label
    return default


def detect_category(text: str, category_hint: str | None = None) -> str:
    if category_hint:
        hint = category_hint.strip().lower()
        for label in CATEGORY_KEYWORDS:
            if hint in label.lower() or label.lower() in hint:
                return label
        # legacy category hints from Studio
        legacy = {
            "song": "Music Video",
            "religious": "Islamic Video",
            "business": "Advertisement",
            "cartoon": "Anime",
            "story": "Movie Scene",
            "podcast": "Podcast",
        }
        if hint in legacy:
            return legacy[hint]
    return first_label(text, CATEGORY_KEYWORDS, "Movie Scene")


def detect_time(text: str) -> str:
    return first_label(text, TIME_KEYWORDS, "Day")


def detect_weather(text: str) -> str:
    return first_label(text, WEATHER_KEYWORDS, "Clear")


def detect_emotions(text: str) -> list[str]:
    found = collect_labels(text, EMOTION_KEYWORDS)
    return found or ["Calm"]


def detect_mood(text: str, emotions: list[str]) -> str:
    mood = first_label(text, MOOD_KEYWORDS, "")
    if mood:
        return mood
    if any(e in ("Sad", "Lonely", "Melancholy") for e in emotions):
        return "Emotional"
    if "Action" in emotions or "Victory" in emotions:
        return "Epic"
    if "Fear" in emotions or "Suspense" in emotions:
        return "Dark"
    return "Cinematic"


def detect_camera(text: str, emotions: list[str], movement: list[str]) -> list[str]:
    found = collect_labels(text, CAMERA_KEYWORDS)
    if not found:
        # Director inference for emotional walking scenes
        if any(e in ("Sad", "Lonely", "Melancholy") for e in emotions):
            found = ["Slow Dolly", "Close Up", "Medium Shot"]
        elif "Action" in emotions:
            found = ["Tracking Shot", "Handheld", "Wide Shot"]
        elif any("walk" in m.lower() for m in movement):
            found = ["Medium Shot", "Tracking Shot"]
        else:
            found = ["Medium Shot", "Gentle Push-in"]
    return found


def detect_movement(text: str) -> list[str]:
    found = collect_labels(text, MOVEMENT_KEYWORDS)
    if not found and ("walk" in text or "walking" in text):
        found = ["Slow walking"]
    return found or ["Motivated camera follow"]


def detect_lens(text: str, shot_types: list[str]) -> str:
    explicit = first_label(text, LENS_KEYWORDS, "")
    if explicit:
        return explicit
    joined = " ".join(shot_types).lower()
    if "close" in joined:
        return "85mm portrait"
    if "wide" in joined or "aerial" in joined:
        return "24mm wide"
    if "macro" in joined:
        return "Macro lens"
    return "35mm narrative"


def detect_lighting(text: str, time: str, weather: str, emotions: list[str]) -> list[str]:
    found = collect_labels(text, LIGHTING_KEYWORDS)
    # Infer cinematic lighting language when prompt implies it.
    if time == "Night" and "Low Key" not in found:
        found.append("Low Key")
    if time in ("Night", "Blue Hour") and "Blue" not in found:
        found.append("Blue")
    if weather == "Rain" and "Wet reflections" not in found:
        found.append("Wet reflections")
    if time == "Golden Hour" and "Golden" not in found:
        found.append("Golden")
    if any(e in ("Sad", "Lonely") for e in emotions) and "Low Key" not in found:
        found.append("Low Key")
    return found or ["Natural balanced"]


def detect_color_palette(
    text: str,
    time: str,
    weather: str,
    emotions: list[str],
    category: str,
) -> list[str]:
    found = collect_labels(text, COLOR_PALETTE_KEYWORDS)
    if not found:
        if time == "Night" or weather == "Rain" or any(
            e in ("Sad", "Lonely") for e in emotions
        ):
            found = ["Cold Blue"]
        elif time == "Golden Hour":
            found = ["Warm Amber"]
        elif category in ("Advertisement", "Product Video"):
            found = ["Luxury Black-Gold"]
        elif category == "Anime":
            found = ["Pastel Soft"]
        elif category == "Trailer":
            found = ["High Contrast Teal-Orange"]
        elif category == "Documentary":
            found = ["Earth Natural"]
        else:
            found = ["Cinematic Neutral"]
    return found


def detect_music(text: str, emotions: list[str], category: str) -> list[str]:
    found = collect_labels(text, MUSIC_KEYWORDS)
    if not found:
        if any(e in ("Sad", "Lonely", "Melancholy") for e in emotions):
            found = ["Piano", "Ambient"]
        elif category == "Music Video":
            found = ["Electronic Beat"]
        elif category == "Islamic Video":
            found = ["Nasheed / Spiritual"]
        elif category in ("Advertisement", "Product Video"):
            found = ["Corporate Clean"]
        elif category == "Trailer":
            found = ["Orchestral"]
        elif category == "Podcast":
            found = ["Lo-fi"]
        else:
            found = ["Ambient"]
    return found


def detect_environment(text: str, weather: str) -> str:
    env = first_label(text, ENVIRONMENT_KEYWORDS, "")
    if env:
        # Prefer empty road for solitary walking cues
        if ("alone" in text or "lonely" in text) and (
            "road" in text or "street" in text or "walk" in text
        ):
            return "Empty road"
        return env
    if "alone" in text and ("walk" in text or "road" in text or "street" in text):
        return "Empty road"
    if weather == "Rain":
        return "Rain-soaked street"
    return "Cinematic location"


def detect_subject_count(text: str) -> int:
    for pattern, count in _SUBJECT_COUNT_PATTERNS:
        if pattern.search(text):
            return count
    return 1


def detect_transition(category: str, mood: str) -> str:
    base = TRANSITION_BY_CATEGORY.get(category, "motivated narrative cuts")
    if mood == "Emotional":
        return f"{base}; linger on emotional beats"
    return base


def detect_atmosphere(
    time: str,
    weather: str,
    mood: str,
    emotions: list[str],
    environment: str,
) -> str:
    emotion_part = ", ".join(emotions[:3])
    return (
        f"{mood} {time.lower()} atmosphere — {weather.lower()} over {environment}; "
        f"emotion focus: {emotion_part}"
    )


def detect_color_grading(palette: list[str], time: str, weather: str) -> str:
    lead = palette[0] if palette else "Cinematic Neutral"
    if weather == "Rain" or time == "Night":
        return f"{lead} grade with crushed blacks and specular wet highlights"
    if time == "Golden Hour":
        return f"{lead} grade with warm highlight roll-off"
    return f"{lead} cinematic grade"
