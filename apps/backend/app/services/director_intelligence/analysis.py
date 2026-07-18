"""AI story analysis — genre, audience, complexity, runtime."""

from __future__ import annotations

from app.services.director_intelligence.library import get_format_spec, resolve_format, resolve_genre
from app.services.director_intelligence.models import StoryAnalysis

_FORMAT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "advertisement": ("ad", "advert", "commercial", "brand", "promo"),
    "music_video": ("music video", "mv", "lyrics", "song"),
    "podcast": ("podcast", "interview", "episode"),
    "islamic_video": ("islamic", "quran", "mosque", "ramadan", "deen"),
    "educational": ("tutorial", "learn", "lesson", "educational", "how to"),
    "documentary": ("documentary", "real story", "investigation"),
    "corporate": ("corporate", "company", "enterprise", "b2b"),
    "shorts": ("short form", "shorts"),
    "reels": ("reels", "instagram reel"),
    "tiktok": ("tiktok", "tik tok"),
    "youtube": ("youtube", "vlog", "channel"),
    "short_film": ("short film", "narrative", "cinematic story"),
}

_GENRE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "action": ("action", "chase", "fight", "battle"),
    "romance": ("love", "romance", "romantic"),
    "comedy": ("funny", "comedy", "humor"),
    "thriller": ("thriller", "mystery", "suspense", "danger"),
    "inspirational": ("inspire", "motivational", "overcome"),
    "faith": ("faith", "spiritual", "islamic", "worship"),
    "documentary": ("documentary", "true story"),
    "educational": ("teach", "explain", "lesson"),
    "corporate": ("brand", "business", "startup"),
    "drama": ("drama", "emotional", "family"),
}


def analyze_story(
    prompt: str,
    *,
    format_hint: str | None = None,
    genre_hint: str | None = None,
    runtime_hint: float | None = None,
    audience_hint: str | None = None,
) -> StoryAnalysis:
    text = (prompt or "").lower()
    fmt_scores = {k: 0.0 for k in _FORMAT_KEYWORDS}
    for fmt, kws in _FORMAT_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                fmt_scores[fmt] += 1.0
    genre_scores = {k: 0.0 for k in _GENRE_KEYWORDS}
    for g, kws in _GENRE_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                genre_scores[g] += 1.0

    if format_hint:
        fmt = resolve_format(format_hint)
    else:
        best = max(fmt_scores.items(), key=lambda kv: kv[1])
        fmt = resolve_format(best[0] if best[1] > 0 else "youtube")

    if genre_hint:
        genre = resolve_genre(genre_hint)
    else:
        best_g = max(genre_scores.items(), key=lambda kv: kv[1])
        genre = resolve_genre(best_g[0] if best_g[1] > 0 else "drama")

    spec = get_format_spec(fmt)
    runtime = float(runtime_hint) if runtime_hint and runtime_hint > 0 else float(spec["runtime_sec"])
    audience = (audience_hint or spec.get("audience") or "general").strip()

    journey = {
        "drama": ["calm", "emotional", "tension", "hope"],
        "action": ["calm", "excited", "tense", "triumphant"],
        "romance": ["warm", "romantic", "conflict", "warm"],
        "faith": ["calm", "reverent", "hopeful", "peace"],
        "comedy": ["light", "happy", "surprise", "happy"],
    }.get(genre, ["calm", "build", "peak", "resolve"])

    characters = ["protagonist"]
    if "friend" in text or "team" in text:
        characters.append("supporting")
    if "villain" in text or "antagonist" in text or "conflict" in text:
        characters.append("antagonist")
    relationships = []
    if len(characters) >= 2:
        relationships.append(f"{characters[0]}->{characters[1]}")
    if "antagonist" in characters:
        relationships.append("protagonist<->antagonist")

    visual = 0.55
    audio = 0.5
    if any(w in text for w in ("cinematic", "epic", "drone", "vfx")):
        visual += 0.25
    if any(w in text for w in ("music", "score", "sound design", "voiceover")):
        audio += 0.25
    if fmt in ("music_video", "shorts", "reels", "tiktok"):
        visual = min(0.98, visual + 0.15)
        audio = min(0.98, audio + 0.2)

    scene_importance = {
        "intro": 0.5,
        "hook": 0.85,
        "story_build": 0.7,
        "conflict": 0.9,
        "climax": 1.0,
        "resolution": 0.75,
        "outro": 0.45,
        "credits": 0.2,
    }

    peak = max(list(fmt_scores.values()) + list(genre_scores.values()) + [0])
    confidence = min(0.98, 0.55 + peak * 0.12)
    notes = [f"format={fmt}", f"genre={genre}", f"runtime={runtime}s"]

    return StoryAnalysis(
        genre=genre,
        format_type=fmt,
        target_audience=audience,
        emotional_journey=journey,
        character_relationships=relationships or ["protagonist"],
        scene_importance=scene_importance,
        visual_complexity=round(min(1.0, visual), 3),
        audio_complexity=round(min(1.0, audio), 3),
        estimated_runtime_sec=runtime,
        confidence=round(confidence, 3),
        notes=notes,
    )
