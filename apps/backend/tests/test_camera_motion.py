"""Phase 3 Sprint 6 — Camera Motion Engine tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CM = ROOT / "app" / "services" / "camera_motion"


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
    "app.services.camera_motion",
    CM,
    [
        ("models", "models.py"),
        ("catalog", "catalog.py"),
        ("detector", "detector.py"),
        ("adaptive", "adaptive.py"),
        ("path", "path.py"),
        ("bridge", "bridge.py"),
        ("store", "store.py"),
        ("engine", "engine.py"),
    ],
)

engine = sys.modules["app.services.camera_motion.engine"]
catalog = sys.modules["app.services.camera_motion.catalog"]
adaptive = sys.modules["app.services.camera_motion.adaptive"]
detector = sys.modules["app.services.camera_motion.detector"]


def test_catalog_covers_mission_motions():
    required = {
        "dolly",
        "crane",
        "drone",
        "orbit",
        "slider",
        "tracking",
        "push_in",
        "pull_out",
        "pov",
        "steadicam",
        "handheld",
    }
    assert required.issubset(set(catalog.MOTION_KINDS))
    assert catalog.normalize_motion("Push In") == "push_in"
    assert catalog.normalize_motion("Steadicam") == "steadicam"
    assert catalog.normalize_motion("slow dolly") == "dolly"


def test_detector_keywords():
    scores = detector.score_motions("Aerial drone flyover of the city")
    assert scores.get("drone", 0) > 0.5
    scores2 = detector.score_motions("Handheld documentary energy in the crowd")
    assert scores2.get("handheld", 0) > 0.5
    assert detector.detect_from_camera_plan({"movement": "Tracking"}) == "tracking"


def test_adaptive_with_locomotion_and_director():
    decision = adaptive.choose_camera_motion(
        "A woman walks through the market",
        locomotion="walking",
        emotion="confident",
        director_pacing="medium",
        cinematic_rhythm="rising intensity",
        camera={"movement": "Steadicam", "cinematic_motion": "Steadicam"},
    )
    assert decision.chosen in ("steadicam", "tracking", "dolly")
    assert decision.alternatives
    assert "locomotion" in decision.factors or "walking" in decision.reason


def test_full_plan_all_motion_kinds_paths():
    kinds = [
        "dolly",
        "crane",
        "drone",
        "orbit",
        "slider",
        "tracking",
        "push_in",
        "pull_out",
        "pov",
        "steadicam",
        "handheld",
    ]
    for kind in kinds:
        label = catalog.DISPLAY_NAME[kind]
        plan = engine.build_camera_motion_plan(
            f"Professional {label} camera move on the subject",
            cameras=[{"scene_index": 0, "movement": label, "framing": "medium"}],
            duration_seconds=5,
        )
        assert plan.scenes[0].primary_motion == kind
        assert plan.scenes[0].cues
        assert plan.scenes[0].cues[0].keyframes or kind == "static"
        assert plan.timeline


def test_integrated_plan():
    plan = engine.build_camera_motion_plan(
        "Epic crane rise then tracking follow as she runs; later intimate push in.",
        scenes=[
            {
                "index": 0,
                "title": "Rise",
                "description": "crane rising over the plaza",
                "duration_seconds": 5,
                "actions": ["stand"],
            },
            {
                "index": 1,
                "title": "Chase",
                "description": "tracking follow as she runs",
                "duration_seconds": 6,
                "actions": ["run"],
            },
            {
                "index": 2,
                "title": "Eyes",
                "description": "emotional push in on face",
                "duration_seconds": 4,
                "actions": ["look"],
            },
        ],
        cameras=[
            {"scene_index": 0, "movement": "Crane", "framing": "wide", "angle": "High Angle"},
            {"scene_index": 1, "movement": "Tracking", "framing": "medium"},
            {"scene_index": 2, "movement": "Push In", "framing": "close-up"},
        ],
        director_plan={
            "cinematic_rhythm": "rising intensity",
            "emotional_pacing": ["epic", "tense", "intimate"],
            "decisions": [
                {"pacing": "slow"},
                {"pacing": "fast"},
                {"pacing": "slow"},
            ],
        },
        motion_intelligence={
            "job_id": "motion_test",
            "primary_locomotion": ["standing", "running", "looking"],
            "scenes": [
                {"scene_index": 0, "primary_locomotion": "standing"},
                {"scene_index": 1, "primary_locomotion": "running"},
                {"scene_index": 2, "primary_locomotion": "looking"},
            ],
        },
        prompt_understanding={"emotion": "intense"},
        parent_generation_id="gen_cam_1",
    )

    assert plan.job_id.startswith("cammotion_")
    assert len(plan.scenes) == 3
    assert plan.scenes[0].primary_motion == "crane"
    assert plan.scenes[1].primary_motion == "tracking"
    assert plan.scenes[2].primary_motion == "push_in"
    assert plan.adaptive_logic["mode"] == "context_weighted"
    assert plan.director_integration.get("cinematic_rhythm") == "rising intensity"
    assert plan.motion_integration.get("motion_job_id") == "motion_test"
    assert plan.provider_directives
    assert sum(len(s.cues) for s in plan.scenes) >= 3

    summary = plan.summary()
    assert summary["scenes"] == 3
    assert summary["cue_count"] >= 3
    assert engine.get_plan(plan.job_id) is not None


def test_dict_export():
    result = engine.build_camera_motion_dict(
        "Orbit around the product on a turntable",
        duration_seconds=4,
    )
    assert "plan" in result and "summary" in result
    assert result["plan"]["scenes"][0]["primary_motion"] == "orbit"


if __name__ == "__main__":
    test_catalog_covers_mission_motions()
    test_detector_keywords()
    test_adaptive_with_locomotion_and_director()
    test_full_plan_all_motion_kinds_paths()
    test_integrated_plan()
    test_dict_export()
    print("OK camera_motion")
