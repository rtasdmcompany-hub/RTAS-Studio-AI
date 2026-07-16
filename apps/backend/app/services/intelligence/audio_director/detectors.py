"""Audio detection — language, accent, gender, emotion, speed, music, mix."""

from __future__ import annotations

import re
from typing import Any

from app.services.intelligence.audio_director.models import AudioCategory, AudioDetection
from app.services.intelligence.models import PromptIntelligenceResult

_URDU_RE = re.compile(r"[\u0600-\u06FF]")


def detect_audio_category(
    prompt: str,
    intelligence: PromptIntelligenceResult,
    understanding: dict[str, Any] | None = None,
) -> AudioCategory:
    text = (prompt or "").lower()
    cat = (understanding or {}).get("category") or intelligence.category
    cat_l = str(cat).lower()
    scene_type = str((understanding or {}).get("scene_type") or "").lower()

    # Social shorts before song/music_video (TikTok legacy maps to song).
    if any(
        k in cat_l or k in scene_type or k in text
        for k in ("tiktok", "youtube short", "shorts", "ig reel", "instagram reel", "reel")
    ):
        return "shorts"
    if "islamic" in cat_l or intelligence.category == "religious" or "mosque" in text:
        return "islamic"
    if "podcast" in cat_l or intelligence.category == "podcast":
        return "podcast"
    if "documentary" in cat_l:
        return "documentary"
    if (
        any(k in cat_l for k in ("advertisement", "commercial", "product"))
        or intelligence.category == "business"
    ):
        return "advertisement"
    if "music video" in cat_l or (
        intelligence.category == "song" and "tiktok" not in text
    ) or "lyrics" in text:
        return "music_video"
    if any(k in cat_l for k in ("movie", "short film", "trailer")) or intelligence.category == "story":
        return "movie"
    return "general"


def detect_language_accent(prompt: str, intelligence: PromptIntelligenceResult) -> tuple[str, str]:
    raw = prompt or ""
    language = intelligence.language or "en"
    if _URDU_RE.search(raw) or any(w in raw.lower() for w in ("urdu", "pakistan", "pakistani")):
        return "ur", "south-asian"
    if any(w in raw.lower() for w in ("arabic", "quran", "nasheed")):
        return "ar", "modern-standard-arabic"
    if language == "ur":
        return "ur", "south-asian"
    if language == "zh":
        return "zh", "neutral"
    return "en", "neutral"


def detect_gender(prompt: str, character_memory: list[dict[str, Any]] | None = None) -> str:
    if character_memory:
        g = str(character_memory[0].get("gender") or "").lower()
        if g in ("male", "female"):
            return g
    lower = (prompt or "").lower()
    if any(w in lower for w in ("she", "her", "woman", "female", "girl", "lady")):
        return "female"
    if any(w in lower for w in ("he", "him", "man", "male", "boy", "gentleman")):
        return "male"
    return "neutral"


def detect_speech_speed(emotion: str, category: AudioCategory) -> str:
    if category == "shorts":
        return "fast"
    if category == "podcast":
        return "conversational"
    if emotion in ("somber", "calm"):
        return "slow"
    if emotion in ("dramatic", "joyful"):
        return "moderate-energetic"
    return "moderate"


def detect_pause_timing(category: AudioCategory, emotion: str) -> list[str]:
    pauses = ["breath before key line", "hold after emotional beat"]
    if category == "advertisement":
        pauses.append("beat before CTA")
    if category == "islamic":
        pauses.append("respectful silence after sacred phrase")
    if category == "podcast":
        pauses.append("host turn-taking pause")
    if emotion in ("somber", "sad"):
        pauses.append("extended silence for grief")
    return pauses


def detect_music_style(category: AudioCategory, emotion: str, understanding: dict | None) -> str:
    styles = (understanding or {}).get("music_style") or []
    if isinstance(styles, list) and styles:
        return ", ".join(str(s) for s in styles[:3])
    table = {
        "music_video": "beat-driven contemporary production",
        "advertisement": "clean modern brand bed",
        "movie": "cinematic orchestral / hybrid score",
        "podcast": "soft lo-fi intro/outro stings",
        "islamic": "nasheed-safe spiritual pads",
        "shorts": "hook-first trending bed",
        "documentary": "subtle observational underscore",
        "general": "ambient cinematic bed",
    }
    base = table.get(category, "ambient cinematic bed")
    if emotion in ("somber", "sad") and category != "music_video":
        return f"{base}; piano-led melancholy"
    return base


def detect_volume_balance(category: AudioCategory, has_voice: bool) -> dict[str, float]:
    """Relative mix levels 0–1 (planning guide, not DSP)."""
    if category == "music_video":
        return {"voice": 0.55, "music": 0.9, "sfx": 0.35, "ambient": 0.25}
    if category == "podcast":
        return {"voice": 0.95, "music": 0.25, "sfx": 0.15, "ambient": 0.1}
    if category == "advertisement":
        return {"voice": 0.85, "music": 0.55, "sfx": 0.4, "ambient": 0.2}
    if category == "islamic":
        return {"voice": 0.8, "music": 0.45, "sfx": 0.25, "ambient": 0.3}
    if has_voice:
        return {"voice": 0.8, "music": 0.5, "sfx": 0.45, "ambient": 0.35}
    return {"voice": 0.0, "music": 0.75, "sfx": 0.5, "ambient": 0.4}


def run_audio_detection(
    prompt: str,
    intelligence: PromptIntelligenceResult,
    *,
    understanding: dict[str, Any] | None = None,
    character_memory: list[dict[str, Any]] | None = None,
) -> AudioDetection:
    category = detect_audio_category(prompt, intelligence, understanding)
    language, accent = detect_language_accent(prompt, intelligence)
    gender = detect_gender(prompt, character_memory)
    emotion = intelligence.emotion
    if understanding and isinstance(understanding.get("emotion"), list) and understanding["emotion"]:
        emotion = str(understanding["emotion"][0]).lower()
        # map cinematic emotions to planner vocabulary
        emotion_map = {
            "sad": "somber",
            "lonely": "somber",
            "joy": "joyful",
            "hope": "inspiring",
            "fear": "dramatic",
            "action": "dramatic",
        }
        emotion = emotion_map.get(emotion, emotion)

    lower = (prompt or "").lower()
    has_singing = category == "music_video" or "lyrics" in lower or "sing" in lower
    has_dialogue = any(w in lower for w in ("says", "dialogue", "talks", "conversation", "podcast"))
    has_narration = (
        category in ("documentary", "advertisement", "islamic", "movie")
        or "narrat" in lower
        or not has_singing
    )
    if category == "music_video":
        has_narration = "narrat" in lower

    speed = detect_speech_speed(emotion, category)
    pauses = detect_pause_timing(category, emotion)
    music_style = detect_music_style(category, emotion, understanding)
    balance = detect_volume_balance(category, has_voice=has_narration or has_dialogue)

    return AudioDetection(
        language=language,
        accent=accent,
        gender=gender,
        emotion=emotion,
        speech_speed=speed,
        pause_timing=pauses,
        music_style=music_style,
        volume_balance=balance,
        category=category,
        has_dialogue=has_dialogue or category == "podcast",
        has_narration=has_narration,
        has_singing=has_singing,
    )
