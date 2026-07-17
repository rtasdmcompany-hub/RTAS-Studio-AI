"""Phase 3 Sprint 10 — Production Ready Video Engine v1.0 tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VE = ROOT / "app" / "services" / "video_engine"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_parents(pkg_name: str):
    parts = pkg_name.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            mod = type(sys)(parent)
            mod.__path__ = []
            sys.modules[parent] = mod


def _load_pkg(pkg_name: str, pkg_path: Path, modules: list[tuple[str, str]]):
    _ensure_parents(pkg_name)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(pkg_path)]
    sys.modules[pkg_name] = pkg
    for mod_name, file_name in modules:
        _load(f"{pkg_name}.{mod_name}", pkg_path / file_name)


_load_pkg(
    "app.services.video_engine",
    VE,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("stages", "stages.py"),
        ("quality", "quality.py"),
        ("validation", "validation.py"),
        ("performance", "performance.py"),
        ("monitoring", "monitoring.py"),
        ("analytics", "analytics.py"),
        ("recovery", "recovery.py"),
        ("stress", "stress.py"),
        ("download", "download.py"),
        ("store", "store.py"),
        ("engine", "engine.py"),
    ],
)

engine = sys.modules["app.services.video_engine.engine"]
version = sys.modules["app.services.video_engine.version"]
stages = sys.modules["app.services.video_engine.stages"]
recovery = sys.modules["app.services.video_engine.recovery"]


def _full_fixture():
    return dict(
        prompt="A woman walks through neon rain; cinematic tracking shot.",
        director_plan={
            "cinematic_rhythm": "rising intensity",
            "transition_style": "motivated cut",
        },
        scenes=[
            {
                "index": 0,
                "title": "Rain Walk",
                "description": "walking in rain",
                "duration_seconds": 5,
            }
        ],
        shots=[{"scene_index": 0, "shot_index": 0, "title": "Track", "duration_seconds": 5}],
        cameras=[{"scene_index": 0, "movement": "Tracking", "framing": "medium"}],
        character_memory=[{"character_id": "Hero_A"}],
        cinematic_quality={"overall": 0.88},
        character_consistency={"consistency_score": {"overall": 0.9}},
        production_render={
            "validation": {"passed": True},
            "export_specs": [
                {"format": "mp4"},
                {"format": "mov"},
                {"format": "webm"},
            ],
            "video_manifest": {"runtime_seconds": 5},
        },
        scene_render={
            "job_id": "scenerender_x",
            "ray_tracing_ready": True,
            "cache_entries": 1,
            "vram_target_mb": 8192,
        },
        camera_motion={"job_id": "cam_x", "primary_motions": ["tracking"]},
        physics={"job_id": "phys_x", "effects": ["rain", "wind", "gravity"]},
        multi_gpu={
            "job_id": "multigpu_x",
            "assigned": 1,
            "workers": 10,
            "skus": ["H100", "A100", "L40S", "RTX", "CLOUD"],
        },
        text_to_video={"job_id": "t2v_x", "requests": 1},
        auto_retry=True,
        run_stress=True,
        stress_iterations=2,
        parent_generation_id="gen_ve_1",
    )


def test_version_stamp():
    assert version.ENGINE_VERSION == "1.0"
    assert "Video Engine" in version.ENGINE_NAME
    assert "v1.0" in version.ENGINE_LABEL


def test_pipeline_order():
    assert list(stages.PIPELINE_ORDER) == [
        "prompt",
        "director",
        "scene",
        "shot",
        "camera",
        "generation",
        "rendering",
        "export",
        "download",
    ]


def test_full_production_ready_plan():
    plan = engine.build_video_engine_plan(**_full_fixture())
    assert plan.job_id.startswith("videoeng_")
    assert plan.engine == version.ENGINE_NAME
    assert plan.version == "1.0"
    assert len(plan.stages) == 9
    assert plan.quality.overall >= 0.75
    assert plan.quality.grade in ("A", "B", "C")
    assert plan.validation.passed is True
    assert plan.download.ready is True
    assert plan.production_ready is True
    assert plan.performance.total_ms >= 0
    assert plan.monitoring.healthy is True
    assert plan.analytics.scenes == 1
    assert plan.analytics.shots == 1
    assert "rain" in plan.analytics.effects
    assert plan.recovery.auto_retry is True
    assert plan.stress.ran is True
    assert plan.stress.success_rate >= 0.9
    assert plan.timeline
    assert any("v1.0" in d or "1.0" in d for d in plan.provider_directives)
    summary = plan.summary()
    assert summary["production_ready"] is True
    assert summary["version"] == "1.0"
    assert engine.get_plan(plan.job_id) is not None


def test_recovery_auto_retry():
    incomplete = engine.build_video_engine_plan(
        "Short prompt only",
        auto_retry=True,
        run_stress=False,
    )
    # Incomplete pipeline should not be fully production ready
    assert incomplete.production_ready is False
    assert incomplete.recovery.enabled is True
    # Some stages may be recovered/pending after auto-retry
    statuses = {s.name: s.status for s in incomplete.stages}
    assert statuses["prompt"] == "passed"


def test_stress_and_dict():
    result = engine.build_video_engine_dict(
        "Stress path",
        scenes=[{"index": 0, "title": "A", "duration_seconds": 3}],
        shots=[{"scene_index": 0, "shot_index": 0}],
        cameras=[{"scene_index": 0, "movement": "Push In"}],
        director_plan={"cinematic_rhythm": "calm"},
        production_render={
            "validation": {"passed": True},
            "export_specs": [{"format": "mp4"}],
            "video_manifest": {"runtime_seconds": 3},
        },
        scene_render={"job_id": "sr1"},
        multi_gpu={"job_id": "mg1", "assigned": 1, "workers": 2, "skus": ["A100"]},
        text_to_video={"job_id": "t1"},
        cinematic_quality={"overall": 0.82},
        character_consistency={"consistency_score": {"overall": 0.8}},
        run_stress=True,
        stress_iterations=2,
    )
    assert result["version"] == "1.0"
    assert result["label"] == version.ENGINE_LABEL
    assert "plan" in result and "summary" in result


if __name__ == "__main__":
    test_version_stamp()
    test_pipeline_order()
    test_full_production_ready_plan()
    test_recovery_auto_retry()
    test_stress_and_dict()
    print("OK video_engine")
