"""Phase 5 Sprint 9 — AI Cinematic Director & Auto Filmmaker Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DI = ROOT / "app" / "services" / "director_intelligence"
CG = ROOT / "app" / "services" / "character_generation"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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
    if "app" in sys.modules:
        sys.modules["app"].__path__ = [str(ROOT / "app")]
    if "app.services" in sys.modules:
        sys.modules["app.services"].__path__ = [str(ROOT / "app" / "services")]


def _load_pkg(pkg_name: str, pkg_path: Path, modules: list[tuple[str, str]]):
    _ensure_parents(pkg_name)
    if pkg_name in sys.modules and all(
        f"{pkg_name}.{mod_name}" in sys.modules for mod_name, _ in modules
    ):
        return
    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(pkg_path)]
    sys.modules[pkg_name] = pkg
    for mod_name, file_name in modules:
        _load(f"{pkg_name}.{mod_name}", pkg_path / file_name)


_load_pkg(
    "app.services.character_generation",
    CG,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("templates", "templates.py"),
        ("validation", "validation.py"),
        ("paddle_status", "paddle_status.py"),
        ("registry", "registry.py"),
        ("store", "store.py"),
        ("engine", "engine.py"),
    ],
)

_load_pkg(
    "app.services.director_intelligence",
    DI,
    [
        ("version", "version.py"),
        ("models", "models.py"),
        ("library", "library.py"),
        ("analysis", "analysis.py"),
        ("planner", "planner.py"),
        ("memory", "memory.py"),
        ("bridge", "bridge.py"),
        ("store", "store.py"),
        ("queue", "queue.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.director_intelligence.version"]
library = sys.modules["app.services.director_intelligence.library"]
analysis = sys.modules["app.services.director_intelligence.analysis"]
planner = sys.modules["app.services.director_intelligence.planner"]
memory = sys.modules["app.services.director_intelligence.memory"]
store = sys.modules["app.services.director_intelligence.store"]
queue_mod = sys.modules["app.services.director_intelligence.queue"]
engine = sys.modules["app.services.director_intelligence.engine"]
cg_paddle = sys.modules["app.services.character_generation.paddle_status"]


def setup_function():
    store.clear()
    queue_mod.director_queue.clear()
    memory.clear()


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 5
    assert version.SPRINT == 9


def test_format_library_unit():
    lib = library.list_director_library()
    assert lib["format_count"] >= 12
    assert lib["extensible"] is True
    ids = {f["format_id"] for f in lib["formats"]}
    for required in (
        "short_film",
        "advertisement",
        "music_video",
        "podcast",
        "islamic_video",
        "educational",
        "documentary",
        "corporate",
        "youtube",
        "shorts",
        "reels",
        "tiktok",
    ):
        assert required in ids
    assert "intro" in lib["beats"] and "climax" in lib["beats"]
    library.register_format("brand_spot", {"runtime_sec": 15, "scenes": 3})
    assert library.resolve_format("brand_spot") == "brand_spot"


def test_story_analysis_unit():
    result = analysis.analyze_story(
        "Create an Islamic educational video about patience with cinematic music.",
        format_hint="islamic_video",
    )
    assert result.format_type == "islamic_video"
    assert result.genre in ("faith", "educational", "drama")
    assert result.estimated_runtime_sec > 0
    assert result.visual_complexity > 0
    assert len(result.emotional_journey) >= 3


def test_production_planner_unit():
    story = analysis.analyze_story("A dramatic short film about friendship and conflict.", format_hint="short_film")
    plan = planner.build_production_plan(
        project_id="p1",
        prompt="friendship conflict",
        analysis=story,
        characters=["protagonist", "supporting"],
    )
    assert len(plan.scenes) >= 6
    assert plan.shot_count >= len(plan.scenes)
    assert plan.total_runtime_sec > 0
    assert plan.camera_plan["angles"]
    assert plan.audio_plan["music_cues"]
    assert plan.render_plan["resolution"]
    assert plan.export_plan["platforms"]
    assert plan.accuracy_score >= version.PLANNING_ACCURACY_THRESHOLD
    assert "hook" in plan.story_structure or "climax" in plan.story_structure


def test_director_logic_beats_and_shots():
    story = analysis.analyze_story("TikTok comedy reel for mobile", format_hint="tiktok", genre_hint="comedy")
    plan = planner.build_production_plan(project_id="tik1", prompt="comedy reel", analysis=story)
    assert plan.format_type == "tiktok"
    assert plan.export_plan["aspect_ratio"] == "9:16"
    for scene in plan.scenes:
        assert scene.environment
        assert scene.emotion_flow
        assert scene.shots
        for shot in scene.shots:
            assert shot.camera_angle
            assert shot.transition


def test_generate_integration_and_bridges():
    result = engine.generate_director(
        prompt="Cinematic YouTube documentary about ocean explorers with epic score.",
        project_id="proj_doc_1",
        format_type="documentary",
        ai_brain={"intent": "direct"},
        story_plan={"title": "Ocean"},
        character_dna={"character_id": "char_exp"},
        motion_plan={"job_id": "mot1"},
        camera_plan={"job_id": "cam1"},
        emotion_plan={"job_id": "emo1"},
        world_plan={"job_id": "world1"},
        audio_summary={"score": "epic"},
        timeline_plan={"timeline_id": "tl1"},
        export_plan={"formats": ["mp4"]},
    )
    assert result["state"] == "completed"
    assert result["production_plan"]["scene_list"]
    assert result["production_plan"]["shot_list"]
    assert result["accuracy_score"] >= version.PLANNING_ACCURACY_THRESHOLD
    assert result["integrations"]["ai_brain"]["linked"] is True
    assert result["integrations"]["story_engine"]["linked"] is True
    assert result["integrations"]["character_dna"]["linked"] is True
    assert result["integrations"]["motion_engine"]["linked"] is True
    assert result["integrations"]["camera_engine"]["linked"] is True
    assert result["integrations"]["emotion_engine"]["linked"] is True
    assert result["integrations"]["world_engine"]["linked"] is True
    assert result["integrations"]["audio_engine"]["linked"] is True
    assert result["integrations"]["timeline_engine"]["linked"] is True
    assert result["integrations"]["export_engine"]["linked"] is True
    assert result["observability"]["scene_count"] >= 4
    assert result["observability"]["shot_count"] >= 4
    fetched = engine.get_director(result["job_id"])
    assert fetched is not None


def test_pipeline_plan_then_generate():
    planned = engine.plan_director(
        prompt="Corporate brand video for a startup launch.",
        format_type="corporate",
    )
    assert planned["state"] == "queued"
    generated = engine.generate_director(job_id=planned["job_id"])
    assert generated["state"] == "completed"
    assert generated["format_type"] == "corporate"
    hist = engine.director_history(limit=10)
    assert hist["count"] >= 1
    report = engine.director_report(limit=20)
    assert report["jobs_analyzed"] >= 1
    assert report["avg_accuracy"] >= version.PLANNING_ACCURACY_THRESHOLD


def test_director_memory():
    first = engine.generate_director(
        prompt="Music video with neon city nights.",
        project_id="mem_proj",
        format_type="music_video",
    )
    assert first["state"] == "completed"
    assert memory.last_plan("mem_proj") is not None
    second = engine.generate_director(
        prompt="Continue the neon music story.",
        project_id="mem_proj",
        format_type="music_video",
    )
    assert second["state"] == "completed"
    assert len(memory.history_for("mem_proj")) >= 2


def test_stress_and_performance_budget():
    t0 = time.perf_counter()
    formats = [
        "short_film",
        "advertisement",
        "youtube",
        "shorts",
        "reels",
        "tiktok",
        "educational",
        "islamic_video",
    ]
    scores = []
    for i, fmt in enumerate(formats * 2):
        result = engine.generate_director(
            prompt=f"Auto filmmaker test {fmt} number {i}",
            project_id=f"stress_{fmt}_{i % 3}",
            format_type=fmt,
        )
        assert result["state"] == "completed"
        scores.append(result["accuracy_score"])
    elapsed = time.perf_counter() - t0
    assert elapsed < 8.0
    assert min(scores) >= version.PLANNING_ACCURACY_THRESHOLD
    assert all(s >= 80 for s in scores)


def test_paddle_secrets_not_exposed():
    status = cg_paddle.paddle_status()
    assert isinstance(status, dict)
    assert "sk_" not in str(status)
