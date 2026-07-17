"""Scene analysis + cinematic rules + coverage + framing/composition/motion."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from app.services.camera_intelligence.library import get_shot_spec, resolve_shot, select_lens_for_shot
from app.services.camera_intelligence.models import SceneAnalysis, ShotPlan


def analyze_scene(
    prompt: str,
    *,
    character_ids: list[str] | None = None,
    emotion: str | None = None,
    environment: str | None = None,
) -> SceneAnalysis:
    text = (prompt or "").strip().lower()
    chars = list(character_ids or [])
    count = len(chars) if chars else (2 if re.search(r"\b(they|both|together|duo)\b", text) else 1)
    if re.search(r"\b(crowd|group|army|party)\b", text):
        count = max(count, 4)

    scene_type = "dialogue"
    if re.search(r"\b(action|chase|fight|battle)\b", text):
        scene_type = "action"
    elif re.search(r"\b(dialogue|conversation|talk|argue|argument)\b", text):
        scene_type = "dialogue"
    elif re.search(r"\b(intimate|romance|love|kiss)\b", text):
        scene_type = "intimate"
    elif re.search(r"\b(reveal|mystery|secret)\b", text):
        scene_type = "reveal"
    elif re.search(r"\b(establish|skyline|landscape|dawn|aerial overview)\b", text):
        scene_type = "establishing"
    elif re.search(r"\b(city|mountain|desert|ocean)\b", text) and not re.search(
        r"\b(people|leads|character|couple)\b", text
    ):
        scene_type = "establishing"

    emo = (emotion or "calm").lower()
    for key in ("happy", "sad", "angry", "fear", "suspense", "excited", "romantic", "serious", "motivational"):
        if key in text:
            emo = key
            break

    env = environment or ("urban" if "city" in text else "interior" if "room" in text or "office" in text else "general")
    lighting = "high_key" if emo in ("happy", "motivational") else "low_key" if emo in ("fear", "suspense", "sad") else "natural"

    movement = "static"
    if scene_type == "action":
        movement = "tracking"
    elif scene_type == "establishing":
        movement = "drone"
    elif scene_type == "reveal":
        movement = "dolly"
    elif scene_type == "intimate":
        movement = "slow_push"

    positions = [
        {"character_id": cid or f"char_{i}", "x": round(-0.3 + i * 0.3, 2), "y": 0.0, "z": 1.0}
        for i, cid in enumerate((chars or [f"anon_{i}" for i in range(count)])[:6])
    ]

    progression = "setup"
    if "climax" in text or "final" in text:
        progression = "climax"
    elif "resolve" in text or "ending" in text:
        progression = "resolution"
    elif "conflict" in text or "argument" in text:
        progression = "conflict"

    return SceneAnalysis(
        scene_type=scene_type,
        character_count=count,
        character_positions=positions,
        scene_emotion=emo,
        story_progression=progression,
        environment=env,
        lighting=lighting,
        camera_movement_recommendation=movement,
        notes=[f"auto_analyzed:{scene_type}", f"chars:{count}"],
    )


def cinematic_rules_for(analysis: SceneAnalysis) -> dict[str, Any]:
    rules = {
        "rule_of_thirds": True,
        "lead_room": True,
        "headroom": True,
        "avoid_jump_cuts": True,
        "axis_of_action": True if analysis.character_count >= 2 else False,
        "emotion_match": analysis.scene_emotion,
        "preferred_motion": analysis.camera_movement_recommendation,
    }
    if analysis.scene_type == "intimate":
        rules["prefer_shallow_dof"] = True
    if analysis.scene_type == "action":
        rules["prefer_wider_coverage"] = True
    return rules


def recommend_shot_sequence(analysis: SceneAnalysis, *, max_shots: int = 4) -> list[str]:
    by_type = {
        "establishing": ["extreme_wide_shot", "wide_shot", "cinematic_reveal", "drone_shot"],
        "action": ["tracking_shot", "low_angle", "handheld", "medium_shot"],
        "dialogue": ["wide_shot", "over_the_shoulder", "medium_close_up", "close_up"],
        "intimate": ["medium_shot", "medium_close_up", "close_up", "extreme_close_up"],
        "reveal": ["cinematic_reveal", "dolly_shot", "medium_shot", "close_up"],
    }
    seq = list(by_type.get(analysis.scene_type, by_type["dialogue"]))
    if analysis.camera_movement_recommendation == "orbit" and "orbit_shot" not in seq:
        seq.insert(1, "orbit_shot")
    return [resolve_shot(s) for s in seq[: max(1, min(8, max_shots))]]


def framing_engine(shot_type: str, analysis: SceneAnalysis) -> dict[str, Any]:
    size_map = {
        "extreme_wide_shot": "EWS",
        "wide_shot": "WS",
        "full_shot": "FS",
        "medium_shot": "MS",
        "medium_close_up": "MCU",
        "close_up": "CU",
        "extreme_close_up": "ECU",
    }
    return {
        "shot_size": size_map.get(shot_type, "MS"),
        "subject_count": analysis.character_count,
        "character_framing": "centered" if analysis.character_count == 1 else "balanced_group",
        "face_priority": shot_type in ("close_up", "extreme_close_up", "medium_close_up"),
        "headroom": "standard",
        "lead_room": True,
    }


def composition_engine(shot_type: str, analysis: SceneAnalysis) -> dict[str, Any]:
    return {
        "rule_of_thirds": True,
        "symmetry": analysis.scene_type == "establishing",
        "depth_layers": 3 if shot_type in ("wide_shot", "extreme_wide_shot", "drone_shot") else 2,
        "negative_space": analysis.scene_emotion in ("sad", "suspense", "fear"),
        "horizon_safe": shot_type != "dutch_angle",
        "dutch_roll_deg": 15.0 if shot_type == "dutch_angle" else 0.0,
    }


def camera_motion_engine(shot_type: str, analysis: SceneAnalysis) -> dict[str, Any]:
    spec = get_shot_spec(shot_type)
    motion = str(spec.get("motion") or analysis.camera_movement_recommendation)
    paths = {
        "static": {"path": "hold", "speed": 0.0},
        "dolly": {"path": "push_in", "speed": 0.35},
        "crane": {"path": "rise", "speed": 0.4},
        "orbit": {"path": "orbit_cw", "speed": 0.3, "radius": 2.5},
        "tracking": {"path": "lateral_follow", "speed": 0.55, "subject_tracking": True},
        "handheld": {"path": "organic", "speed": 0.25, "shake": "controlled"},
        "drone": {"path": "aerial_sweep", "speed": 0.5, "altitude": 40},
        "slow_push": {"path": "push_in", "speed": 0.15},
    }
    base = dict(paths.get(motion, paths["static"]))
    base["motion_type"] = motion
    base["face_tracking"] = True
    base["subject_tracking"] = True
    return base


def build_shot(
    shot_type: str,
    analysis: SceneAnalysis,
    *,
    job_id: str,
    index: int,
    start_sec: float,
    duration_sec: float | None = None,
) -> ShotPlan:
    st = resolve_shot(shot_type)
    spec = get_shot_spec(st)
    dur = float(duration_sec) if duration_sec else float(spec.get("default_duration") or 3.0)
    lens = select_lens_for_shot(st)
    digest = hashlib.sha1(f"{job_id}|{st}|{index}".encode()).hexdigest()
    rack = st in ("close_up", "extreme_close_up", "cinematic_reveal")
    shake = "handheld_controlled" if st == "handheld" else "stabilized"
    return ShotPlan(
        shot_id=f"shot_{digest[:10]}",
        shot_type=st,
        framing=framing_engine(st, analysis),
        composition=composition_engine(st, analysis),
        camera_motion=camera_motion_engine(st, analysis),
        lens=lens,
        duration_sec=round(dur, 3),
        subject_tracking=True,
        face_tracking=True,
        auto_focus=True,
        rack_focus=rack,
        zoom=1.15 if st in ("close_up", "extreme_close_up") else 1.0,
        shake_control=shake,
        start_sec=round(start_sec, 3),
        end_sec=round(start_sec + dur, 3),
        metadata={"cinematic_rules": cinematic_rules_for(analysis)},
    )


def scene_coverage(shots: list[ShotPlan], analysis: SceneAnalysis) -> dict[str, Any]:
    types = [s.shot_type for s in shots]
    has_master = any(t in ("wide_shot", "extreme_wide_shot", "full_shot") for t in types)
    has_coverage = any(t in ("medium_shot", "over_the_shoulder", "medium_close_up") for t in types)
    has_insert = any(t in ("close_up", "extreme_close_up") for t in types)
    score = 40.0 + (25.0 if has_master else 0) + (20.0 if has_coverage else 0) + (15.0 if has_insert else 0)
    return {
        "has_master": has_master,
        "has_coverage": has_coverage,
        "has_insert": has_insert,
        "shot_types": types,
        "coverage_score": round(min(100.0, score), 2),
        "scene_type": analysis.scene_type,
        "complete": score >= 70,
    }
