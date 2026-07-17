"""AI scene emotion analysis + recommendations."""

from __future__ import annotations

import re
from typing import Any

from app.services.emotion_intelligence.library import get_emotion_spec, resolve_emotion
from app.services.emotion_intelligence.models import EmotionAnalysis

_KEYWORD_MAP: dict[str, tuple[str, ...]] = {
    "happy": ("happy", "joy", "celebrate", "smile", "cheerful"),
    "sad": ("sad", "grief", "lonely", "tears", "heartbroken"),
    "angry": ("angry", "furious", "rage", "yell", "betray"),
    "romantic": ("love", "kiss", "romance", "darling", "heart"),
    "excited": ("excited", "amazing", "wow", "thrill", "can't wait"),
    "fear": ("afraid", "scared", "terror", "panic", "danger"),
    "suspense": ("suddenly", "shadow", "unknown", "wait", "tension"),
    "serious": ("must", "critical", "decision", "truth", "duty"),
    "calm": ("calm", "peace", "gentle", "quietly", "breathe"),
    "motivational": ("believe", "achieve", "inspire", "rise", "champion"),
    "emotional": ("feel", "memory", "vulnerable", "touched"),
    "confused": ("confused", "puzzled", "what", "unclear", "lost"),
    "shocked": ("shocked", "unbelievable", "no way", "stunned"),
    "crying": ("crying", "weep", "sob", "tears falling"),
    "laughing": ("laugh", "hilarious", "giggle", "chuckle"),
    "smiling": ("smiling", "grin", "warm smile"),
    "thinking": ("think", "wonder", "ponder", "consider"),
    "proud": ("proud", "accomplished", "honor", "triumph"),
    "nervous": ("nervous", "anxious", "worried", "uneasy"),
    "surprised": ("surprised", "unexpected", "gasp"),
}


def _score_text(text: str) -> dict[str, float]:
    lowered = (text or "").lower()
    scores = {k: 0.0 for k in _KEYWORD_MAP}
    for emotion, keywords in _KEYWORD_MAP.items():
        for kw in keywords:
            if kw in lowered:
                scores[emotion] += 1.0
    if "!" in text:
        scores["excited"] += 0.4
        scores["shocked"] += 0.2
    if "?" in text:
        scores["confused"] += 0.3
        scores["thinking"] += 0.2
    return scores


def _best(scores: dict[str, float], default: str = "calm") -> str:
    best = max(scores.items(), key=lambda kv: kv[1])
    if best[1] <= 0:
        return resolve_emotion(default)
    return resolve_emotion(best[0])


def analyze_scene(
    prompt: str,
    *,
    dialogue: str | None = None,
    story_context: str | None = None,
    character_hint: str | None = None,
    emotion_hint: str | None = None,
) -> EmotionAnalysis:
    scene_scores = _score_text(prompt)
    dialogue_scores = _score_text(dialogue or prompt)
    story_scores = _score_text(story_context or prompt)
    character_scores = _score_text(character_hint or prompt)

    scene_emotion = _best(scene_scores)
    dialogue_emotion = _best(dialogue_scores)
    story_emotion = _best(story_scores)
    character_emotion = (
        resolve_emotion(emotion_hint) if emotion_hint else _best(character_scores)
    )

    if scene_emotion != character_emotion:
        transition = f"{scene_emotion}_to_{character_emotion}"
    else:
        transition = "stable"

    spec = get_emotion_spec(character_emotion)
    intensity = min(1.0, max(0.2, float(spec.get("arousal", 0.5))))

    recommendations = [
        f"Lead with {character_emotion} facial performance",
        f"Match body energy to intensity {intensity:.2f}",
        "Preserve face lock identity across expression changes",
    ]
    if transition != "stable":
        recommendations.append(f"Plan transition: {transition}")
    if dialogue_emotion != character_emotion:
        recommendations.append(
            f"Align delivery: dialogue={dialogue_emotion}, character={character_emotion}"
        )

    peak = max(scene_scores.values()) if scene_scores else 0
    confidence = min(0.98, 0.55 + peak * 0.12)

    return EmotionAnalysis(
        scene_emotion=scene_emotion,
        dialogue_emotion=dialogue_emotion,
        story_emotion=story_emotion,
        character_emotion=character_emotion,
        emotional_transition=transition,
        performance_intensity=round(intensity, 3),
        recommendations=recommendations,
        confidence=round(confidence, 3),
    )
