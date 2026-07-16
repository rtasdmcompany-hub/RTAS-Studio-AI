"""Story beat detection — decides which cinematic scenes are required."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.intelligence.prompt_understanding.models import (
    CinematicPromptUnderstanding,
)


@dataclass(frozen=True)
class StoryBeat:
    key: str
    title: str
    purpose: str
    preferred_shot_type: str
    camera_angle: str
    camera_movement: str
    lens: str
    emotion_bias: str
    is_flashback: bool = False
    is_detail: bool = False


def detect_story_beats(
    prompt: str,
    understanding: CinematicPromptUnderstanding,
) -> list[StoryBeat]:
    text = (prompt or "").lower()
    emotions = {e.lower() for e in understanding.emotion}
    category = understanding.category

    has_walk = any(w in text for w in ("walk", "walking", "stroll"))
    has_memory = any(
        w in text
        for w in ("remember", "remembering", "memory", "flashback", "lost love", "nostalgia")
    )
    has_rain = understanding.weather.lower() == "rain" or "rain" in text
    has_face_focus = any(
        e in emotions for e in ("sad", "lonely", "melancholy", "romance", "fear")
    ) or any(w in text for w in ("face", "tears", "eyes"))
    emotional = understanding.mood.lower() in ("emotional", "dark", "intimate") or has_face_focus

    beats: list[StoryBeat] = []

    # Always open.
    beats.append(
        StoryBeat(
            key="opening",
            title="Opening Establishing Shot",
            purpose="Establish world, weather, and subject presence",
            preferred_shot_type="Extreme Wide" if has_rain or understanding.time == "Night" else "Wide Shot",
            camera_angle="High Angle" if understanding.time == "Night" else "Eye Level",
            camera_movement="Reveal",
            lens="24mm wide",
            emotion_bias=understanding.emotion[0] if understanding.emotion else "Calm",
        )
    )

    if category == "Podcast":
        beats.append(
            StoryBeat(
                key="talk",
                title="Host Talking Shot",
                purpose="Primary talk / interview coverage",
                preferred_shot_type="Medium Shot",
                camera_angle="Eye Level",
                camera_movement="Push In",
                lens="50mm natural",
                emotion_bias="Calm",
            )
        )
    elif category in ("Advertisement", "Product Video"):
        beats.append(
            StoryBeat(
                key="product",
                title="Product Hero Shot",
                purpose="Showcase product with premium clarity",
                preferred_shot_type="Close Up",
                camera_angle="Low Angle",
                camera_movement="Orbit",
                lens="85mm portrait",
                emotion_bias="Hope",
            )
        )
        beats.append(
            StoryBeat(
                key="benefit",
                title="Lifestyle Benefit Shot",
                purpose="Show product in human context",
                preferred_shot_type="Medium Shot",
                camera_angle="Eye Level",
                camera_movement="Tracking",
                lens="35mm narrative",
                emotion_bias="Joy",
            )
        )
    elif category == "Music Video":
        beats.append(
            StoryBeat(
                key="performance",
                title="Performance Shot",
                purpose="Capture performance energy on beat",
                preferred_shot_type="Tracking",
                camera_angle="Low Angle",
                camera_movement="Steadicam",
                lens="35mm narrative",
                emotion_bias="Action",
            )
        )
        beats.append(
            StoryBeat(
                key="hook",
                title="Hook Close Up",
                purpose="Face / detail on musical hook",
                preferred_shot_type="Close Up",
                camera_angle="Eye Level",
                camera_movement="Push In",
                lens="85mm portrait",
                emotion_bias=understanding.emotion[0] if understanding.emotion else "Joy",
            )
        )
    else:
        if has_walk:
            beats.append(
                StoryBeat(
                    key="walking",
                    title="Walking Shot",
                    purpose="Follow subject through environment with emotional pacing",
                    preferred_shot_type="Tracking",
                    camera_angle="Eye Level",
                    camera_movement="Tracking",
                    lens="35mm narrative",
                    emotion_bias="Lonely" if "lonely" in emotions or "alone" in text else "Calm",
                )
            )

        if has_face_focus or emotional:
            beats.append(
                StoryBeat(
                    key="close_up",
                    title="Close Up Face",
                    purpose="Read emotion through facial micro-expression",
                    preferred_shot_type="Close Up",
                    camera_angle="Eye Level",
                    camera_movement="Push In",
                    lens="85mm portrait",
                    emotion_bias=understanding.emotion[0] if understanding.emotion else "Sad",
                )
            )

        if has_memory:
            beats.append(
                StoryBeat(
                    key="flashback",
                    title="Memory Flashback",
                    purpose="Reveal remembered love / past emotional world",
                    preferred_shot_type="Over Shoulder",
                    camera_angle="Soft High Angle",
                    camera_movement="Slow Dolly",
                    lens="50mm natural",
                    emotion_bias="Romance",
                    is_flashback=True,
                )
            )

        if has_rain or understanding.weather.lower() in ("snow", "fog"):
            beats.append(
                StoryBeat(
                    key="detail",
                    title="Rain Detail Shot" if has_rain else "Atmosphere Detail Shot",
                    purpose="Texture the world with weather detail and mood",
                    preferred_shot_type="Extreme Close Up",
                    camera_angle="Top View" if has_rain else "Dutch Angle",
                    camera_movement="Slider",
                    lens="Macro lens",
                    emotion_bias="Melancholy",
                    is_detail=True,
                )
            )

        # Ensure narrative depth for short film / movie scene
        if category in ("Movie Scene", "Short Film", "Documentary", "Islamic Video") and len(beats) < 4:
            beats.append(
                StoryBeat(
                    key="mid",
                    title="Character Journey Shot",
                    purpose="Advance story through character action",
                    preferred_shot_type="Medium Shot",
                    camera_angle="Eye Level",
                    camera_movement="Steadicam",
                    lens="35mm narrative",
                    emotion_bias=understanding.emotion[0] if understanding.emotion else "Calm",
                )
            )

    # Always close with emotional / brand ending.
    ending_title = "Emotional Ending" if emotional or has_memory else "Closing Resolve"
    beats.append(
        StoryBeat(
            key="ending",
            title=ending_title,
            purpose="Resolve emotional arc and leave lasting image",
            preferred_shot_type="Medium Shot",
            camera_angle="Low Angle" if emotional else "Eye Level",
            camera_movement="Pull Out",
            lens="50mm natural",
            emotion_bias=understanding.emotion[0] if understanding.emotion else "Hope",
        )
    )

    return beats
