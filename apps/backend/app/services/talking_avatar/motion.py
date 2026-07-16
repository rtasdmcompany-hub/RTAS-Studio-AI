"""Head motion, eye contact, blink, smile, idle, natural motion planners."""

from __future__ import annotations

from app.services.talking_avatar.emotion import emotion_params
from app.services.talking_avatar.models import (
    ExpressionCue,
    EyeContactCue,
    HeadMotionCue,
    IdleMotionCue,
    LipSyncFrame,
)


def build_head_motion(
    runtime: float,
    *,
    emotion: str,
    natural_motion: bool = True,
) -> list[HeadMotionCue]:
    intensity = 0.35 if natural_motion else 0.15
    if emotion in ("happy", "joy", "confident"):
        intensity += 0.1
    if emotion in ("sad", "somber", "lonely"):
        intensity *= 0.7

    cues: list[HeadMotionCue] = []
    t = 0.0
    step = 1.6 if natural_motion else 2.4
    kinds = ("idle", "nod", "turn", "emphasis", "idle")
    i = 0
    while t < runtime:
        end = min(runtime, t + step)
        kind = kinds[i % len(kinds)]
        yaw = 0.0
        pitch = 0.0
        roll = 0.0
        if kind == "nod":
            pitch = 0.18 * intensity
        elif kind == "turn":
            yaw = (0.22 if i % 2 == 0 else -0.22) * intensity
        elif kind == "emphasis":
            pitch = 0.12 * intensity
            yaw = 0.08 * intensity
        else:
            yaw = 0.05 * intensity * (1 if i % 2 == 0 else -1)
            pitch = 0.03 * intensity
        cues.append(
            HeadMotionCue(
                start_sec=round(t, 3),
                end_sec=round(end, 3),
                yaw=round(yaw, 3),
                pitch=round(pitch, 3),
                roll=round(roll, 3),
                intensity=round(intensity, 3),
                kind=kind,
            )
        )
        t = end
        i += 1
    return cues


def build_eye_contact_and_blinks(
    runtime: float,
    *,
    natural_motion: bool = True,
) -> tuple[list[EyeContactCue], list[EyeContactCue]]:
    contact: list[EyeContactCue] = []
    blinks: list[EyeContactCue] = []

    # Primary eye contact windows
    t = 0.0
    while t < runtime:
        hold = 2.2 if natural_motion else 3.0
        end = min(runtime, t + hold)
        contact.append(
            EyeContactCue(
                start_sec=round(t, 3),
                end_sec=round(end, 3),
                gaze_x=0.0,
                gaze_y=0.02,
                blink=False,
                eyelid_close=0.0,
                kind="contact",
            )
        )
        # Soft glance away
        if end < runtime and natural_motion:
            g_end = min(runtime, end + 0.45)
            contact.append(
                EyeContactCue(
                    start_sec=round(end, 3),
                    end_sec=round(g_end, 3),
                    gaze_x=0.15 if int(t) % 2 == 0 else -0.12,
                    gaze_y=-0.05,
                    blink=False,
                    eyelid_close=0.0,
                    kind="glance",
                )
            )
            t = g_end
        else:
            t = end

    # Blinks ~ every 3.2s
    bt = 1.1
    while bt < runtime:
        blinks.append(
            EyeContactCue(
                start_sec=round(bt, 3),
                end_sec=round(min(runtime, bt + 0.12), 3),
                gaze_x=0.0,
                gaze_y=0.0,
                blink=True,
                eyelid_close=1.0,
                kind="blink",
            )
        )
        bt += 3.2 if natural_motion else 4.5
    return contact, blinks


def build_expressions_and_smiles(
    runtime: float,
    *,
    emotion: str,
    lip_sync: list[LipSyncFrame],
) -> tuple[list[ExpressionCue], list[ExpressionCue]]:
    smile, brow, intensity = emotion_params(emotion)
    expressions: list[ExpressionCue] = []
    smiles: list[ExpressionCue] = []

    # Base emotional hold
    expressions.append(
        ExpressionCue(
            start_sec=0.0,
            end_sec=round(runtime, 3),
            emotion=emotion,
            smile=smile,
            brow_raise=brow,
            intensity=intensity,
            kind="speak" if lip_sync else "idle",
        )
    )

    # Smile pulses for positive emotions / natural warmth
    if smile >= 0.35:
        st = 0.8
        while st < runtime:
            end = min(runtime, st + 1.4)
            cue = ExpressionCue(
                start_sec=round(st, 3),
                end_sec=round(end, 3),
                emotion=emotion,
                smile=min(1.0, smile + 0.1),
                brow_raise=brow,
                intensity=min(1.0, intensity + 0.1),
                kind="smile",
            )
            smiles.append(cue)
            expressions.append(cue)
            st += 4.5
    elif emotion in ("sad", "somber", "lonely"):
        # Subtle soft expression beats
        expressions.append(
            ExpressionCue(
                start_sec=round(runtime * 0.35, 3),
                end_sec=round(min(runtime, runtime * 0.55), 3),
                emotion=emotion,
                smile=0.02,
                brow_raise=0.2,
                intensity=0.5,
                kind="react",
            )
        )
    return expressions, smiles


def build_idle_motion(
    runtime: float,
    *,
    natural_motion: bool = True,
) -> list[IdleMotionCue]:
    if not natural_motion:
        return [
            IdleMotionCue(
                start_sec=0.0,
                end_sec=round(runtime, 3),
                sway=0.02,
                micro_nod=0.01,
                breath=0.08,
            )
        ]
    cues: list[IdleMotionCue] = []
    t = 0.0
    while t < runtime:
        end = min(runtime, t + 2.0)
        cues.append(
            IdleMotionCue(
                start_sec=round(t, 3),
                end_sec=round(end, 3),
                sway=0.06,
                micro_nod=0.04,
                breath=0.12,
                kind="idle",
            )
        )
        t = end
    return cues
