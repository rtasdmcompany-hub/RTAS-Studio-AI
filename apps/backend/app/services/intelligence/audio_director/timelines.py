"""Voice / Music / SFX timeline builders."""

from __future__ import annotations

from typing import Any

from app.services.intelligence.audio_director.models import (
    AudioDetection,
    TimelineCue,
)
from app.services.intelligence.models import ScenePlan


def _scene_spans(scenes: list[ScenePlan]) -> list[tuple[ScenePlan, float, float]]:
    t = 0.0
    spans = []
    for scene in scenes:
        dur = float(scene.duration_seconds or 1)
        spans.append((scene, t, t + dur))
        t += dur
    return spans


def build_voice_timeline(
    detection: AudioDetection,
    scenes: list[ScenePlan],
    *,
    character_id: str | None = None,
) -> list[TimelineCue]:
    cues: list[TimelineCue] = []
    if not (detection.has_narration or detection.has_dialogue or detection.has_singing):
        return cues

    for scene, start, end in _scene_spans(scenes):
        kind = "narration"
        label = f"VO — {scene.title}"
        if detection.has_singing and detection.category == "music_video":
            kind = "vocals"
            label = f"Vocal line — {scene.title}"
        elif detection.has_dialogue and detection.category == "podcast":
            kind = "dialogue"
            label = f"Host / guest — {scene.title}"
        elif detection.has_dialogue and "close" in scene.title.lower():
            kind = "dialogue"
            label = f"Character line — {scene.title}"

        # Leave head/tail for silence / music breathe
        pad = min(0.35, (end - start) * 0.12)
        cues.append(
            TimelineCue(
                start_sec=round(start + pad, 2),
                end_sec=round(end - pad, 2),
                label=label,
                kind=kind,
                character_id=character_id,
                emotion=detection.emotion,
                metadata={
                    "language": detection.language,
                    "accent": detection.accent,
                    "gender": detection.gender,
                    "speech_speed": detection.speech_speed,
                    "scene_index": scene.index,
                },
            )
        )
    return cues


def build_music_timeline(
    detection: AudioDetection,
    scenes: list[ScenePlan],
) -> list[TimelineCue]:
    cues: list[TimelineCue] = []
    spans = _scene_spans(scenes)
    if not spans:
        return cues

    total_end = spans[-1][2]
    # Bed across full runtime
    cues.append(
        TimelineCue(
            start_sec=0.0,
            end_sec=round(total_end, 2),
            label=f"Music bed — {detection.music_style}",
            kind="background_music",
            emotion=detection.emotion,
            metadata={"style": detection.music_style, "role": "bed"},
        )
    )

    for i, (scene, start, end) in enumerate(spans):
        if i == 0:
            cues.append(
                TimelineCue(
                    start_sec=round(start, 2),
                    end_sec=round(min(start + 1.5, end), 2),
                    label="Music intro swell",
                    kind="music_transition",
                    emotion=detection.emotion,
                    metadata={"scene_index": scene.index},
                )
            )
        if i == len(spans) // 2:
            cues.append(
                TimelineCue(
                    start_sec=round(start, 2),
                    end_sec=round(min(start + 1.2, end), 2),
                    label="Midrise musical hit",
                    kind="music_transition",
                    emotion=detection.emotion,
                    metadata={"scene_index": scene.index},
                )
            )
        if i == len(spans) - 1:
            cues.append(
                TimelineCue(
                    start_sec=round(max(start, end - 2.0), 2),
                    end_sec=round(end, 2),
                    label="Music outro resolve",
                    kind="music_transition",
                    emotion=detection.emotion,
                    metadata={"scene_index": scene.index},
                )
            )
    return cues


def build_sfx_timeline(
    detection: AudioDetection,
    scenes: list[ScenePlan],
    *,
    understanding: dict[str, Any] | None = None,
    sound_plan: dict[str, Any] | None = None,
) -> list[TimelineCue]:
    understanding = understanding or {}
    sound_plan = sound_plan or {}
    weather = str(understanding.get("weather") or "").lower()
    ambient = list(sound_plan.get("ambient") or [])
    foley = list(sound_plan.get("foley") or ["footsteps", "cloth movement"])
    env_fx = list(sound_plan.get("environmental_fx") or [])

    cues: list[TimelineCue] = []
    spans = _scene_spans(scenes)
    if not spans:
        return cues

    total_end = spans[-1][2]
    # Ambient bed
    amb_label = ", ".join(ambient[:3]) if ambient else "room tone"
    if weather == "rain":
        amb_label = f"{amb_label}; rain loop"
    cues.append(
        TimelineCue(
            start_sec=0.0,
            end_sec=round(total_end, 2),
            label=f"Ambient — {amb_label}",
            kind="ambient",
            metadata={"layers": ambient or ["room tone"]},
        )
    )

    for scene, start, end in spans:
        # Foley pulses inside each scene
        mid = (start + end) / 2
        foley_label = foley[0] if foley else "footsteps"
        if "walk" in scene.title.lower() or "walking" in (scene.description or "").lower():
            foley_label = "wet footsteps" if weather == "rain" else "footsteps"
        cues.append(
            TimelineCue(
                start_sec=round(start + 0.2, 2),
                end_sec=round(end - 0.2, 2),
                label=f"Foley — {foley_label}",
                kind="foley",
                metadata={"scene_index": scene.index, "foley": foley},
            )
        )
        # Transition whoosh at scene boundary
        cues.append(
            TimelineCue(
                start_sec=round(max(0.0, end - 0.25), 2),
                end_sec=round(min(total_end, end + 0.25), 2),
                label="Transition whoosh / impact",
                kind="sfx_transition",
                metadata={"scene_index": scene.index},
            )
        )
        if env_fx:
            cues.append(
                TimelineCue(
                    start_sec=round(mid - 0.4, 2),
                    end_sec=round(mid + 0.8, 2),
                    label=f"Env FX — {env_fx[0]}",
                    kind="environmental_fx",
                    metadata={"scene_index": scene.index, "fx": env_fx},
                )
            )
    return cues


def build_silence_windows(
    detection: AudioDetection,
    voice_timeline: list[TimelineCue],
    total_runtime: float,
) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    if total_runtime <= 0:
        return windows

    # Opening breath
    windows.append(
        {
            "start_sec": 0.0,
            "end_sec": 0.35,
            "reason": "opening silence / music establish",
        }
    )

    for cue in voice_timeline:
        # Micro silence before VO
        windows.append(
            {
                "start_sec": round(max(0.0, cue.start_sec - 0.2), 2),
                "end_sec": round(cue.start_sec, 2),
                "reason": "pre-speech pause",
            }
        )
        windows.append(
            {
                "start_sec": round(cue.end_sec, 2),
                "end_sec": round(min(total_runtime, cue.end_sec + 0.25), 2),
                "reason": "post-speech hold",
            }
        )

    if detection.category == "islamic":
        windows.append(
            {
                "start_sec": round(max(0.0, total_runtime * 0.45), 2),
                "end_sec": round(min(total_runtime, total_runtime * 0.45 + 0.6), 2),
                "reason": "respectful silence beat",
            }
        )
    return windows
