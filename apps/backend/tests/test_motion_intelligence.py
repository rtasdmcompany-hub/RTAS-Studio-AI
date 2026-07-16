"""Phase 3 Sprint 5 — Motion Intelligence Engine tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MI = ROOT / "app" / "services" / "motion_intelligence"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_pkg(pkg_name: str, pkg_path: Path, modules: list[tuple[str, str]]):
    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(pkg_path)]
    sys.modules[pkg_name] = pkg
    for mod_name, file_name in modules:
        _load(f"{pkg_name}.{mod_name}", pkg_path / file_name)
    _load(pkg_name, pkg_path / "__init__.py")


_load_pkg(
    "app.services.motion_intelligence",
    MI,
    [
        ("models", "models.py"),
        ("locomotion", "locomotion.py"),
        ("gaze", "gaze.py"),
        ("hand_motion", "hand_motion.py"),
        ("body_motion", "body_motion.py"),
        ("naturalness", "naturalness.py"),
        ("director_bridge", "director_bridge.py"),
        ("store", "store.py"),
        ("engine", "engine.py"),
    ],
)

engine = sys.modules["app.services.motion_intelligence.engine"]
locomotion = sys.modules["app.services.motion_intelligence.locomotion"]


def test_locomotion_detection_matrix():
    assert locomotion.detect_primary_locomotion("A man walking in rain") == "walking"
    assert locomotion.detect_primary_locomotion("She is running through streets") == "running"
    assert locomotion.detect_primary_locomotion("He sits on a chair") == "sitting"
    assert locomotion.detect_primary_locomotion("Standing by the window") == "standing"
    assert locomotion.detect_primary_locomotion("She turns slowly left") == "turning"
    assert locomotion.detect_primary_locomotion("Looking at the camera") == "looking"
    assert locomotion.detect_primary_locomotion(
        "calm scene", actions=["walk across room"]
    ) == "walking"


def test_full_plan_with_integrations():
    plan = engine.build_motion_intelligence_plan(
        "A confident woman walks toward camera then looks at the lens.",
        scenes=[
            {
                "index": 0,
                "title": "Approach",
                "description": "walking toward camera",
                "duration_seconds": 5,
                "actions": ["walk", "look at camera"],
                "characters": ["Hero_A"],
            },
            {
                "index": 1,
                "title": "Hold",
                "description": "standing and looking",
                "duration_seconds": 4,
                "actions": ["stand", "look"],
                "characters": ["Hero_A"],
            },
        ],
        cameras=[
            {
                "scene_index": 0,
                "movement": "Tracking",
                "framing": "medium",
                "lens": "35mm",
                "cinematic_motion": "Tracking",
            },
            {
                "scene_index": 1,
                "movement": "Push In",
                "framing": "close-up",
                "lens": "50mm",
            },
        ],
        character_memory=[
            {
                "character_id": "Hero_A",
                "walking_style": "confident measured stride",
                "pose": "upright",
                "expression": "calm",
                "body": "athletic",
            }
        ],
        director_plan={
            "cinematic_rhythm": "rising intensity",
            "transition_style": "motivated cut",
            "emotional_pacing": ["confident", "intimate"],
            "scene_emphasis": ["walk in", "eye contact"],
            "decisions": [
                {"pacing": "medium", "emotional_beat": "arrival"},
                {"pacing": "slow", "emotional_beat": "connection"},
            ],
        },
        scene_breakdown={"Production": {"EstimatedRuntime": "9s"}},
        prompt_understanding={"emotion": "confident"},
        duration_seconds=9.0,
        parent_generation_id="gen_test_1",
    )

    assert plan.job_id.startswith("motion_")
    assert len(plan.scenes) == 2
    assert plan.scenes[0].primary_locomotion == "walking"
    assert plan.scenes[0].locomotion
    assert plan.scenes[0].gaze
    assert plan.scenes[0].hand_motion
    assert plan.scenes[0].body_motion
    assert plan.scenes[0].camera_sync
    assert plan.scenes[0].director_notes
    assert plan.character_ids == ["Hero_A"]
    assert plan.walking_styles["Hero_A"] == "confident measured stride"
    assert plan.natural.avoid_robotic is True
    assert plan.natural.foot_contact_lock is True
    assert plan.timeline
    assert plan.animation_directives
    assert plan.director_integration.get("cinematic_rhythm") == "rising intensity"
    assert plan.camera_integration.get("count") == 2
    assert plan.scene_planner_integration.get("scene_count") == 2
    assert "parent_generation_id" in plan.director_integration

    summary = plan.summary()
    assert summary["scenes"] == 2
    assert summary["locomotion_cues"] >= 2
    assert summary["gaze_cues"] >= 1
    assert summary["hand_cues"] >= 1
    assert summary["body_cues"] >= 1

    stored = engine.get_plan(plan.job_id)
    assert stored is not None
    assert stored.job_id == plan.job_id


def test_running_and_sitting_and_turning():
    run = engine.build_motion_intelligence_plan(
        "Athlete sprinting down the alley",
        duration_seconds=6,
    )
    assert run.scenes[0].primary_locomotion == "running"
    assert any(c.kind == "running" for c in run.scenes[0].locomotion)

    sit = engine.build_motion_intelligence_plan(
        "He sits on a wooden chair by the window",
        duration_seconds=5,
    )
    assert sit.scenes[0].primary_locomotion == "sitting"

    turn = engine.build_motion_intelligence_plan(
        "She turns slowly to face the door",
        duration_seconds=4,
    )
    assert turn.scenes[0].primary_locomotion == "turning"


def test_dict_export():
    result = engine.build_motion_intelligence_dict(
        "Standing still, waving hello",
        duration_seconds=4,
    )
    assert "plan" in result and "summary" in result
    assert result["plan"]["natural"]["micro_movements"] is True
    assert result["summary"]["job_id"]


if __name__ == "__main__":
    test_locomotion_detection_matrix()
    test_full_plan_with_integrations()
    test_running_and_sitting_and_turning()
    test_dict_export()
    print("OK motion_intelligence")
