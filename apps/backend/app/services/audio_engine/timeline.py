"""TimelineService — merge voice/music/ambient/sfx into tracks."""

from __future__ import annotations

from app.services.audio_engine.models import (
    AmbientClip,
    MusicClip,
    SfxClip,
    TimelineTrack,
    VoiceClip,
)


def build_timeline(
    voice: list[VoiceClip],
    music: list[MusicClip],
    ambient: list[AmbientClip],
    sfx: list[SfxClip],
) -> list[TimelineTrack]:
    tracks = [
        TimelineTrack(
            track_id="track_voice",
            kind="voice",
            clips=[c.to_dict() for c in voice],
            gain_db=0.0,
        ),
        TimelineTrack(
            track_id="track_music",
            kind="music",
            clips=[c.to_dict() for c in music],
            gain_db=-8.0,
        ),
        TimelineTrack(
            track_id="track_ambient",
            kind="ambient",
            clips=[c.to_dict() for c in ambient],
            gain_db=-12.0,
        ),
        TimelineTrack(
            track_id="track_sfx",
            kind="sfx",
            clips=[c.to_dict() for c in sfx],
            gain_db=-4.0,
        ),
    ]
    return tracks


def timeline_duration_sec(
    voice: list[VoiceClip],
    music: list[MusicClip],
    ambient: list[AmbientClip],
    sfx: list[SfxClip],
) -> float:
    ends: list[float] = [0.0]
    ends.extend(c.end_sec for c in voice)
    ends.extend(c.end_sec for c in music)
    ends.extend(c.end_sec for c in ambient)
    ends.extend(c.start_sec + c.duration_sec for c in sfx)
    return max(ends)
