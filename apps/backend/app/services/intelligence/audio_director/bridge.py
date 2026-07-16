"""Bridge Audio Director → legacy MusicPlan / VoicePlan / SoundDesignPlan."""

from __future__ import annotations

from app.services.intelligence.audio_director.models import AudioDirectorPlan
from app.services.intelligence.cinematic_models import (
    MusicPlan,
    SoundDesignPlan,
    VoicePlan,
)


def to_voice_plan(plan: AudioDirectorPlan) -> VoicePlan:
    d = plan.detection
    age = "adult"
    tone = "warm authoritative"
    if d.emotion in ("somber", "calm"):
        tone = "soft emotional"
    elif d.emotion in ("dramatic",):
        tone = "intense measured"
    elif d.category == "advertisement":
        tone = "confident modern"
    elif d.category == "islamic":
        tone = "respectful serene"

    return VoicePlan(
        gender=d.gender,
        age=age,
        tone=tone,
        emotion=d.emotion,
        speed=d.speech_speed,
        pauses=list(d.pause_timing),
        emphasis=["hero line", "emotional turn", "closing line"],
        language=d.language,
        accent=d.accent,
    )


def to_music_plan(plan: AudioDirectorPlan) -> MusicPlan:
    d = plan.detection
    tempo = 92
    energy = "medium"
    if d.category == "shorts" or d.emotion in ("dramatic", "joyful"):
        tempo = 118
        energy = "high"
    elif d.emotion in ("somber", "calm"):
        tempo = 72
        energy = "low"
    elif d.category == "music_video":
        tempo = 110
        energy = "high"

    instrumentation = ["pads", "strings", "soft percussion"]
    if d.category == "music_video":
        instrumentation = ["drums", "bass", "synth", "vocals bed"]
    elif d.category == "islamic":
        instrumentation = ["soft choir pads", "strings", "gentle percussion"]
    elif d.category == "advertisement":
        instrumentation = ["plucks", "soft drums", "modern pads"]

    cues = [
        {
            "start_sec": c.start_sec,
            "end_sec": c.end_sec,
            "label": c.label,
            "kind": c.kind,
            "emotion": c.emotion,
        }
        for c in plan.music_timeline
    ]
    return MusicPlan(
        genre=d.music_style,
        tempo_bpm=tempo,
        energy=energy,
        emotion=d.emotion,
        instrumentation=instrumentation,
        beat_transitions=[
            c.label for c in plan.music_timeline if c.kind == "music_transition"
        ]
        or ["intro swell", "midrise hit", "outro resolve"],
        cue_timing=cues,
    )


def to_sound_plan(plan: AudioDirectorPlan, base: SoundDesignPlan | None = None) -> SoundDesignPlan:
    ambient = []
    foley = []
    transitions = []
    env_fx = []
    layers = ["music bed ducking under VO"]
    for cue in plan.sfx_timeline:
        if cue.kind == "ambient":
            ambient.extend((cue.metadata or {}).get("layers") or [cue.label])
        elif cue.kind == "foley":
            foley.extend((cue.metadata or {}).get("foley") or [cue.label])
        elif cue.kind == "sfx_transition":
            transitions.append(cue.label)
        elif cue.kind == "environmental_fx":
            env_fx.extend((cue.metadata or {}).get("fx") or [cue.label])

    if base:
        ambient = list(dict.fromkeys([*(base.ambient or []), *ambient]))
        foley = list(dict.fromkeys([*(base.foley or []), *foley]))
        transitions = list(dict.fromkeys([*(base.transitions or []), *transitions]))
        env_fx = list(dict.fromkeys([*(base.environmental_fx or []), *env_fx]))
        layers = list(dict.fromkeys([*(base.background_layers or []), *layers]))

    return SoundDesignPlan(
        ambient=ambient or ["room tone"],
        foley=foley or ["footsteps"],
        transitions=transitions or ["whoosh soft"],
        environmental_fx=env_fx or ["air movement"],
        background_layers=layers,
    )
