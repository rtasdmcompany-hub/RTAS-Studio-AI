"""Multi-track builder and audio layer manager."""

from __future__ import annotations

from typing import Any

from app.services.audio_timeline.models import AudioLayer, TimelineEvent, TimelineTrack

DEFAULT_TRACK_SPECS: list[tuple[str, str, str, float, int]] = [
    ("track_voice", "voice", "Voice", 0.0, 0),
    ("track_music", "music", "Music", -8.0, 1),
    ("track_ambient", "ambient", "Ambient", -12.0, 2),
    ("track_sfx", "sfx", "SFX", -4.0, 3),
    ("track_foley", "foley", "Foley", -6.0, 4),
    ("track_narration", "narration", "Narration", -2.0, 5),
    ("track_transition", "transition", "Transition Audio", -3.0, 6),
]


def _clip_event(
    *,
    event_id: str,
    track_id: str,
    kind: str,
    start: float,
    end: float,
    label: str | None = None,
    scene_id: str | None = None,
    shot_id: str | None = None,
    frame: int | None = None,
    emotion: str | None = None,
    asset_url: str | None = None,
    gain_db: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> TimelineEvent:
    return TimelineEvent(
        event_id=event_id,
        track_id=track_id,
        kind=kind,
        start_sec=max(0.0, float(start)),
        end_sec=max(float(start), float(end)),
        label=label,
        scene_id=scene_id,
        shot_id=shot_id,
        frame=frame,
        emotion=emotion,
        asset_url=asset_url,
        gain_db=gain_db,
        metadata=metadata or {},
    )


def build_default_tracks() -> list[TimelineTrack]:
    return [
        TimelineTrack(
            track_id=tid,
            kind=kind,  # type: ignore[arg-type]
            name=name,
            gain_db=gain,
            order=order,
            snap_enabled=True,
        )
        for tid, kind, name, gain, order in DEFAULT_TRACK_SPECS
    ]


def populate_tracks_from_sources(
    tracks: list[TimelineTrack],
    *,
    scenes: list[dict[str, Any]] | None = None,
    shots: list[dict[str, Any]] | None = None,
    voice_summary: dict[str, Any] | None = None,
    music_summary: dict[str, Any] | None = None,
    sfx_summary: dict[str, Any] | None = None,
    ambient_summary: dict[str, Any] | None = None,
    mix_summary: dict[str, Any] | None = None,
    localization_summary: dict[str, Any] | None = None,
    audio_director: dict[str, Any] | None = None,
    duration_sec: float = 8.0,
) -> list[TimelineTrack]:
    by_kind = {t.kind: t for t in tracks}
    scenes = scenes or []
    shots = shots or []
    audio_director = audio_director or {}
    dur = max(1.0, float(duration_sec))

    # Voice / dialogue
    voice_track = by_kind.get("voice")
    if voice_track is not None:
        vt = audio_director.get("voice_timeline") or []
        if isinstance(vt, list) and vt:
            for i, item in enumerate(vt[:64]):
                if not isinstance(item, dict):
                    continue
                start = float(item.get("start") or item.get("start_sec") or i * 1.5)
                end = float(item.get("end") or item.get("end_sec") or start + 1.2)
                voice_track.events.append(
                    _clip_event(
                        event_id=f"voice_{i}",
                        track_id=voice_track.track_id,
                        kind="dialogue",
                        start=start,
                        end=end,
                        label=str(item.get("text") or item.get("dialogue") or "dialogue")[
                            :120
                        ],
                        scene_id=str(item.get("scene_id") or "") or None,
                        emotion=str(item.get("emotion") or "") or None,
                        asset_url=(voice_summary or {}).get("audio_url"),
                    )
                )
        elif voice_summary:
            voice_track.events.append(
                _clip_event(
                    event_id="voice_0",
                    track_id=voice_track.track_id,
                    kind="dialogue",
                    start=0.0,
                    end=min(dur, float(voice_summary.get("duration_sec") or dur)),
                    label="voice",
                    asset_url=voice_summary.get("audio_url"),
                )
            )

    # Music
    music_track = by_kind.get("music")
    if music_track is not None:
        music_track.events.append(
            _clip_event(
                event_id="music_0",
                track_id=music_track.track_id,
                kind="score",
                start=0.0,
                end=dur,
                label=str((music_summary or {}).get("mood") or "score"),
                emotion=str((music_summary or {}).get("emotion") or "neutral"),
                asset_url=(music_summary or {}).get("audio_url"),
                gain_db=-8.0,
            )
        )

    # Ambient
    ambient_track = by_kind.get("ambient")
    if ambient_track is not None:
        at = audio_director.get("ambient_timeline") or []
        if isinstance(at, list) and at:
            for i, item in enumerate(at[:24]):
                if not isinstance(item, dict):
                    continue
                start = float(item.get("start") or item.get("start_sec") or 0.0)
                end = float(item.get("end") or item.get("end_sec") or dur)
                ambient_track.events.append(
                    _clip_event(
                        event_id=f"ambient_{i}",
                        track_id=ambient_track.track_id,
                        kind="ambient",
                        start=start,
                        end=end,
                        label=str(item.get("label") or item.get("environment") or "ambient"),
                        asset_url=(ambient_summary or {}).get("audio_url"),
                        gain_db=-12.0,
                    )
                )
        else:
            ambient_track.events.append(
                _clip_event(
                    event_id="ambient_0",
                    track_id=ambient_track.track_id,
                    kind="ambient",
                    start=0.0,
                    end=dur,
                    label=str((ambient_summary or {}).get("environment") or "ambient"),
                    asset_url=(ambient_summary or {}).get("audio_url"),
                    gain_db=-12.0,
                )
            )

    # SFX
    sfx_track = by_kind.get("sfx")
    if sfx_track is not None:
        st = audio_director.get("sfx_timeline") or []
        events_src = st if isinstance(st, list) and st else (sfx_summary or {}).get("events") or []
        if isinstance(events_src, list) and events_src:
            for i, item in enumerate(events_src[:48]):
                if not isinstance(item, dict):
                    continue
                start = float(item.get("start") or item.get("start_sec") or i * 0.8)
                length = float(item.get("duration_sec") or item.get("duration") or 0.4)
                sfx_track.events.append(
                    _clip_event(
                        event_id=f"sfx_{i}",
                        track_id=sfx_track.track_id,
                        kind="action",
                        start=start,
                        end=start + length,
                        label=str(item.get("label") or item.get("name") or "sfx"),
                        scene_id=str(item.get("scene_id") or "") or None,
                        shot_id=str(item.get("shot_id") or "") or None,
                        asset_url=item.get("asset_url") or (sfx_summary or {}).get("audio_url"),
                        gain_db=-4.0,
                    )
                )

    # Foley from shots / actions
    foley_track = by_kind.get("foley")
    if foley_track is not None and shots:
        for i, shot in enumerate(shots[:32]):
            if not isinstance(shot, dict):
                continue
            start = float(shot.get("start") or shot.get("start_sec") or i * (dur / max(1, len(shots))))
            end = float(shot.get("end") or shot.get("end_sec") or start + 0.5)
            foley_track.events.append(
                _clip_event(
                    event_id=f"foley_{i}",
                    track_id=foley_track.track_id,
                    kind="foley",
                    start=start,
                    end=end,
                    label=str(shot.get("action") or shot.get("camera") or "foley"),
                    scene_id=str(shot.get("scene_id") or "") or None,
                    shot_id=str(shot.get("shot_id") or shot.get("id") or "") or None,
                    gain_db=-6.0,
                )
            )

    # Narration
    narration_track = by_kind.get("narration")
    if narration_track is not None and localization_summary:
        narration_track.events.append(
            _clip_event(
                event_id="narration_0",
                track_id=narration_track.track_id,
                kind="narration",
                start=0.0,
                end=min(dur, float(localization_summary.get("duration_sec") or dur)),
                label="dubbed_narration",
                asset_url=localization_summary.get("dubbed_audio_url"),
                gain_db=-2.0,
            )
        )

    # Transition audio between scenes
    transition_track = by_kind.get("transition")
    if transition_track is not None and len(scenes) > 1:
        for i in range(len(scenes) - 1):
            sc = scenes[i] if isinstance(scenes[i], dict) else {}
            nxt = scenes[i + 1] if isinstance(scenes[i + 1], dict) else {}
            boundary = float(
                sc.get("end")
                or sc.get("end_sec")
                or ((i + 1) * dur / max(1, len(scenes)))
            )
            transition_track.events.append(
                _clip_event(
                    event_id=f"transition_{i}",
                    track_id=transition_track.track_id,
                    kind="transition",
                    start=max(0.0, boundary - 0.15),
                    end=boundary + 0.15,
                    label=f"transition_{sc.get('id', i)}_{nxt.get('id', i + 1)}",
                    scene_id=str(sc.get("id") or sc.get("scene_id") or "") or None,
                    gain_db=-3.0,
                )
            )

    # Mix metadata can mute / gain adjust
    if mix_summary and isinstance(mix_summary, dict):
        gains = mix_summary.get("track_gains") or {}
        if isinstance(gains, dict):
            for t in tracks:
                if t.kind in gains:
                    try:
                        t.gain_db = float(gains[t.kind])
                    except (TypeError, ValueError):
                        pass

    return tracks


def build_layers(tracks: list[TimelineTrack]) -> list[AudioLayer]:
    dialogue_ids = [t.track_id for t in tracks if t.kind in ("voice", "narration")]
    score_ids = [t.track_id for t in tracks if t.kind in ("music", "ambient")]
    fx_ids = [t.track_id for t in tracks if t.kind in ("sfx", "foley", "transition")]
    layers = [
        AudioLayer(
            layer_id="layer_dialogue",
            name="Dialogue Layer",
            track_ids=dialogue_ids,
            blend_mode="priority",
            gain_db=0.0,
        ),
        AudioLayer(
            layer_id="layer_score",
            name="Score & Atmosphere",
            track_ids=score_ids,
            blend_mode="mix",
            gain_db=-6.0,
        ),
        AudioLayer(
            layer_id="layer_fx",
            name="Effects & Transitions",
            track_ids=fx_ids,
            blend_mode="additive",
            gain_db=-2.0,
        ),
        AudioLayer(
            layer_id="layer_master",
            name="Master Bus",
            track_ids=[t.track_id for t in tracks],
            blend_mode="bus",
            gain_db=0.0,
        ),
    ]
    return layers


def timeline_duration(tracks: list[TimelineTrack], fallback: float = 0.0) -> float:
    ends = [fallback]
    for t in tracks:
        for e in t.events:
            ends.append(e.end_sec)
    return max(ends)
