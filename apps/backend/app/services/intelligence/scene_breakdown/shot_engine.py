"""Generate professional detailed shots for each story beat / scene."""

from __future__ import annotations

from app.services.intelligence.prompt_understanding.models import (
    CinematicPromptUnderstanding,
)
from app.services.intelligence.scene_breakdown.beats import StoryBeat
from app.services.intelligence.scene_breakdown.models import DetailedShot
from app.services.intelligence.scene_breakdown.shot_catalog import (
    angle_for_shot,
    composition_for_shot,
    dof_for_shot,
    lens_for_shot,
    normalize_shot_type,
)

_EXPRESSION: dict[str, str] = {
    "Sad": "downcast eyes, soft frown",
    "Lonely": "distant gaze, restrained sorrow",
    "Romance": "tender eyes, slight smile",
    "Fear": "wide eyes, tense jaw",
    "Hope": "lifted brows, softening face",
    "Joy": "open smile, bright eyes",
    "Melancholy": "faraway look, quiet grief",
    "Action": "focused intensity",
    "Calm": "relaxed neutral expression",
}

_BODY: dict[str, str] = {
    "Sad": "slumped shoulders, slow gait",
    "Lonely": "closed posture, hands in pockets",
    "Romance": "open chest, gentle reach",
    "Fear": "tightened stance, guarded arms",
    "Hope": "upright, forward lean",
    "Joy": "light energetic movement",
    "Melancholy": "stillness with small sighs",
    "Action": "dynamic athletic posture",
    "Calm": "balanced grounded stance",
}

_SOUND: dict[str, list[str]] = {
    "rain": ["rain on pavement", "distant thunder bed", "wet footsteps"],
    "night": ["city hush", "soft wind"],
    "flashback": ["filtered memory bed", "soft piano motif"],
    "detail": ["close raindrop hits", "fabric / water texture FX"],
    "walk": ["footsteps", "clothing rustle"],
    "default": ["ambient room tone", "subtle whoosh transitions"],
}


def _emotion_label(beat: StoryBeat, understanding: CinematicPromptUnderstanding) -> str:
    if beat.emotion_bias:
        return beat.emotion_bias
    return understanding.emotion[0] if understanding.emotion else "Calm"


def _character_position(beat: StoryBeat, shot_type: str) -> str:
    if beat.is_detail:
        return "off-frame / implied presence"
    if shot_type in ("Extreme Wide", "Wide Shot", "Drone"):
        return "small in frame — lower third / mid-distance"
    if shot_type in ("Close Up", "Extreme Close Up"):
        return "fills frame — face centered-right"
    if shot_type == "Tracking":
        return "mid-frame walking left-to-right or toward camera"
    if beat.is_flashback:
        return "soft-centered memory placement"
    return "mid-ground, rule-of-thirds subject"


def generate_shots_for_scene(
    *,
    scene_number: int,
    beat: StoryBeat,
    understanding: CinematicPromptUnderstanding,
    scene_duration: float,
    shots_per_scene: int,
    transition_type: str,
    character_name: str = "lead subject",
) -> list[DetailedShot]:
    primary = normalize_shot_type(beat.preferred_shot_type)
    emotion = _emotion_label(beat, understanding)
    lighting = list(understanding.lighting) or ["Natural balanced"]
    palette = list(understanding.color_palette) or ["Cinematic Neutral"]
    music = ", ".join(understanding.music_style) if understanding.music_style else "Ambient"
    env = understanding.environment
    weather = understanding.weather
    time = understanding.time

    # Optional second coverage shot for pacing.
    variants: list[tuple[str, str, str]] = [
        (primary, beat.camera_movement, beat.purpose),
    ]
    if shots_per_scene >= 2 and not beat.is_detail:
        coverage = "Medium Shot" if primary != "Medium Shot" else "Close Up"
        variants.append(
            (
                coverage,
                "Push In" if emotion in ("Sad", "Lonely", "Romance") else "Static hold",
                f"Coverage for {beat.title}",
            )
        )

    # Split duration across shots.
    n = len(variants)
    base = round(scene_duration / n, 2)
    durations = [base] * n
    durations[-1] = round(scene_duration - base * (n - 1), 2)

    shots: list[DetailedShot] = []
    for idx, ((shot_type, movement, purpose), dur) in enumerate(
        zip(variants, durations), start=1
    ):
        sound = list(_SOUND["default"])
        if weather.lower() == "rain":
            sound = list(_SOUND["rain"])
        if beat.is_flashback:
            sound = list(_SOUND["flashback"])
        elif beat.is_detail:
            sound = list(_SOUND["detail"])
        elif "walk" in beat.key:
            sound = list(_SOUND["walk"]) + (
                list(_SOUND["rain"]) if weather.lower() == "rain" else []
            )
        if time == "Night" and "city hush" not in sound:
            sound.extend(_SOUND["night"])

        flashback_lighting = lighting
        flashback_palette = palette
        if beat.is_flashback:
            flashback_lighting = ["Soft diffused", "Warm memory glow"]
            flashback_palette = ["Warm Amber", "Soft Desaturate"]

        shots.append(
            DetailedShot(
                scene_number=scene_number,
                shot_number=idx,
                shot_type=shot_type,
                camera_angle=angle_for_shot(shot_type, beat.camera_angle),
                lens=lens_for_shot(shot_type, beat.lens or understanding.lens),
                camera_movement=movement,
                lighting=flashback_lighting if beat.is_flashback else lighting,
                environment=(
                    "remembered warm interior / past location"
                    if beat.is_flashback
                    else env
                ),
                weather="Clear memory haze" if beat.is_flashback else weather,
                time="Day memory" if beat.is_flashback else time,
                character_position=_character_position(beat, shot_type),
                character_emotion=emotion,
                facial_expression=_EXPRESSION.get(emotion, "natural cinematic face"),
                body_language=_BODY.get(emotion, "natural grounded posture"),
                color_palette=flashback_palette if beat.is_flashback else palette,
                depth_of_field=dof_for_shot(shot_type),
                composition=composition_for_shot(
                    shot_type, flashback=beat.is_flashback
                ),
                transition_type=transition_type if idx == n else "cut",
                sound_design=sound,
                music_mood=music if not beat.is_flashback else "Piano, soft nostalgia",
                estimated_duration_seconds=dur,
                purpose=f"{character_name}: {purpose}",
            )
        )
    return shots
