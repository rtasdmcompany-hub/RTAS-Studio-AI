"""Cinematic synchronization — scene/shot/frame/beat/emotion."""

from __future__ import annotations

from typing import Any

from app.services.audio_timeline.models import BeatMarker, SyncMetadata, TimelineEvent, TimelineTrack


def _snap(value: float, grid_sec: float) -> float:
    if grid_sec <= 0:
        return value
    return round(value / grid_sec) * grid_sec


def generate_beat_markers(
    duration_sec: float,
    *,
    bpm: float = 96.0,
    intensity_curve: list[float] | None = None,
) -> list[BeatMarker]:
    duration = max(0.5, float(duration_sec))
    bpm = max(40.0, min(220.0, float(bpm)))
    interval = 60.0 / bpm
    markers: list[BeatMarker] = []
    t = 0.0
    idx = 0
    while t <= duration + 1e-6:
        intensity = 0.5
        if intensity_curve:
            pos = min(len(intensity_curve) - 1, int((t / duration) * len(intensity_curve)))
            intensity = float(intensity_curve[pos])
        markers.append(
            BeatMarker(
                marker_id=f"beat_{idx}",
                time_sec=round(t, 4),
                beat_index=idx,
                intensity=intensity,
                bar=(idx // 4) + 1,
            )
        )
        idx += 1
        t += interval
    return markers


def align_events_to_grid(
    tracks: list[TimelineTrack],
    *,
    fps: float,
    snap_enabled: bool,
) -> None:
    grid = 1.0 / max(1.0, float(fps))
    for track in tracks:
        if track.locked:
            continue
        for event in track.events:
            if event.locked:
                continue
            if snap_enabled and track.snap_enabled:
                event.start_sec = _snap(event.start_sec, grid)
                event.end_sec = max(event.start_sec + grid, _snap(event.end_sec, grid))
            event.frame = int(round(event.start_sec * fps))


def sync_dialogue_lip_sync(
    tracks: list[TimelineTrack],
    lip_sync: dict[str, Any] | None,
    *,
    fps: float,
) -> bool:
    if not lip_sync:
        return False
    cues = lip_sync.get("viseme_timeline") or lip_sync.get("cues") or lip_sync.get("lip_sync_timeline") or []
    if not isinstance(cues, list) or not cues:
        return False
    voice = next((t for t in tracks if t.kind == "voice"), None)
    if voice is None or not voice.events:
        return False
    # Shift voice events to first cue start when available
    first = cues[0] if isinstance(cues[0], dict) else {}
    cue_start = float(first.get("start") or first.get("start_sec") or 0.0)
    delta = cue_start - voice.events[0].start_sec
    if abs(delta) < 1e-6:
        return True
    for e in voice.events:
        if e.locked or voice.locked:
            continue
        e.start_sec = max(0.0, e.start_sec + delta)
        e.end_sec = max(e.start_sec, e.end_sec + delta)
        e.frame = int(round(e.start_sec * fps))
        e.metadata["lip_sync_aligned"] = True
    return True


def sync_music_emotion(
    tracks: list[TimelineTrack],
    scenes: list[dict[str, Any]] | None,
) -> bool:
    music = next((t for t in tracks if t.kind == "music"), None)
    if music is None or not music.events or not scenes:
        return False
    emotions = []
    for sc in scenes:
        if isinstance(sc, dict):
            emotions.append(str(sc.get("emotion") or sc.get("mood") or "neutral"))
    if not emotions:
        return False
    # Tag music segments with dominant scene emotion
    dominant = max(set(emotions), key=emotions.count)
    for e in music.events:
        e.emotion = dominant
        e.metadata["emotion_synced"] = True
    return True


def sync_sfx_with_actions(
    tracks: list[TimelineTrack],
    shots: list[dict[str, Any]] | None,
    *,
    fps: float,
) -> bool:
    sfx = next((t for t in tracks if t.kind == "sfx"), None)
    if sfx is None or not shots:
        return False
    aligned = 0
    for i, shot in enumerate(shots[: len(sfx.events) or 1]):
        if not isinstance(shot, dict):
            continue
        start = float(shot.get("start") or shot.get("start_sec") or i * 0.5)
        if i < len(sfx.events):
            ev = sfx.events[i]
            if not ev.locked and not sfx.locked:
                length = max(0.05, ev.end_sec - ev.start_sec)
                ev.start_sec = start
                ev.end_sec = start + length
                ev.shot_id = str(shot.get("shot_id") or shot.get("id") or "") or None
                ev.frame = int(round(ev.start_sec * fps))
                ev.metadata["action_synced"] = True
                aligned += 1
    return aligned > 0


def sync_ambient_environment(
    tracks: list[TimelineTrack],
    scenes: list[dict[str, Any]] | None,
) -> bool:
    ambient = next((t for t in tracks if t.kind == "ambient"), None)
    if ambient is None or not ambient.events or not scenes:
        return False
    env = None
    for sc in scenes:
        if isinstance(sc, dict) and (sc.get("environment") or sc.get("location")):
            env = str(sc.get("environment") or sc.get("location"))
            break
    if not env:
        return False
    for e in ambient.events:
        e.label = env
        e.metadata["environment_synced"] = True
    return True


def sync_camera_with_music_intensity(
    tracks: list[TimelineTrack],
    beat_markers: list[BeatMarker],
    camera_plan: dict[str, Any] | None,
) -> bool:
    if not beat_markers:
        return False
    music = next((t for t in tracks if t.kind == "music"), None)
    if music is None:
        return False
    peak = max(beat_markers, key=lambda b: b.intensity)
    for e in music.events:
        e.metadata["peak_intensity_sec"] = peak.time_sec
        e.metadata["camera_music_aligned"] = True
        if camera_plan:
            e.metadata["camera_motion"] = camera_plan.get("primary_motion") or camera_plan.get(
                "style"
            )
    return True


def apply_dynamic_balance(tracks: list[TimelineTrack]) -> None:
    """Duck music/ambient when dialogue is active."""
    voice_windows: list[tuple[float, float]] = []
    for t in tracks:
        if t.kind in ("voice", "narration"):
            for e in t.events:
                voice_windows.append((e.start_sec, e.end_sec))

    def overlaps(a0: float, a1: float) -> bool:
        for b0, b1 in voice_windows:
            if a0 < b1 and a1 > b0:
                return True
        return False

    for t in tracks:
        if t.kind not in ("music", "ambient"):
            continue
        for e in t.events:
            if overlaps(e.start_sec, e.end_sec):
                e.gain_db = min(e.gain_db, t.gain_db - 6.0)
                e.metadata["ducked"] = True
            else:
                e.gain_db = t.gain_db


def compute_sync_accuracy(
    tracks: list[TimelineTrack],
    *,
    fps: float,
    lip_ok: bool,
    emotion_ok: bool,
    sfx_ok: bool,
    ambient_ok: bool,
    camera_ok: bool,
) -> float:
    scores = [
        0.95 if lip_ok else 0.7,
        0.95 if emotion_ok else 0.75,
        0.95 if sfx_ok else 0.72,
        0.9 if ambient_ok else 0.75,
        0.9 if camera_ok else 0.7,
    ]
    # Frame snap conformance
    grid = 1.0 / max(1.0, fps)
    total = 0
    ok = 0
    for t in tracks:
        for e in t.events:
            total += 1
            if abs(e.start_sec - _snap(e.start_sec, grid)) < 1e-6:
                ok += 1
    frame_score = (ok / total) if total else 0.9
    scores.append(frame_score)
    return round(sum(scores) / len(scores), 4)


def run_synchronization(
    tracks: list[TimelineTrack],
    *,
    fps: float = 24.0,
    duration_sec: float = 8.0,
    scenes: list[dict[str, Any]] | None = None,
    shots: list[dict[str, Any]] | None = None,
    lip_sync: dict[str, Any] | None = None,
    camera_plan: dict[str, Any] | None = None,
    bpm: float = 96.0,
    snap_enabled: bool = True,
    auto_align: bool = True,
) -> tuple[list[BeatMarker], SyncMetadata]:
    scenes = scenes or []
    shots = shots or []
    beat_markers = generate_beat_markers(duration_sec, bpm=bpm)

    lip_ok = emotion_ok = sfx_ok = ambient_ok = camera_ok = False
    if auto_align:
        lip_ok = sync_dialogue_lip_sync(tracks, lip_sync, fps=fps)
        emotion_ok = sync_music_emotion(tracks, scenes)
        sfx_ok = sync_sfx_with_actions(tracks, shots, fps=fps)
        ambient_ok = sync_ambient_environment(tracks, scenes)
        camera_ok = sync_camera_with_music_intensity(tracks, beat_markers, camera_plan)
        apply_dynamic_balance(tracks)

    align_events_to_grid(tracks, fps=fps, snap_enabled=snap_enabled)

    accuracy = compute_sync_accuracy(
        tracks,
        fps=fps,
        lip_ok=lip_ok,
        emotion_ok=emotion_ok,
        sfx_ok=sfx_ok,
        ambient_ok=ambient_ok,
        camera_ok=camera_ok,
    )
    sync = SyncMetadata(
        mode="auto",
        fps=fps,
        frame_accuracy_ms=round(1000.0 / max(1.0, fps), 3),
        sync_accuracy=accuracy,
        scene_count=len(scenes),
        shot_count=len(shots),
        beat_count=len(beat_markers),
        lip_sync_aligned=lip_ok,
        emotion_aligned=emotion_ok,
        camera_music_aligned=camera_ok,
        dynamic_balance=True,
        snap_grid_ms=round((1000.0 / max(1.0, fps)), 3),
        details={
            "sfx_action_aligned": sfx_ok,
            "ambient_environment_aligned": ambient_ok,
            "snap_enabled": snap_enabled,
            "auto_align": auto_align,
        },
    )
    return beat_markers, sync
