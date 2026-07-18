"""Phase 5 Sprint 10 — Final Production Release tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FR = ROOT / "app" / "services" / "final_release"
DI = ROOT / "app" / "services" / "director_intelligence"
VE = ROOT / "app" / "services" / "video_engine"
AE = ROOT / "app" / "services" / "audio_export"
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


# Minimal stubs / packages required by pipeline
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

# video_engine has many modules — load via package init carefully
def _load_video_engine():
    _ensure_parents("app.services.video_engine")
    if "app.services.video_engine.engine" in sys.modules:
        return
    pkg = type(sys)("app.services.video_engine")
    pkg.__path__ = [str(VE)]
    sys.modules["app.services.video_engine"] = pkg
    for name in (
        "version",
        "models",
        "store",
        "stages",
        "validation",
        "quality",
        "performance",
        "monitoring",
        "analytics",
        "recovery",
        "download",
        "stress",
        "engine",
    ):
        _load(f"app.services.video_engine.{name}", VE / f"{name}.py")
    # bind public API like __init__
    eng = sys.modules["app.services.video_engine.engine"]
    ver = sys.modules["app.services.video_engine.version"]
    sys.modules["app.services.video_engine"].build_video_engine_dict = eng.build_video_engine_dict
    sys.modules["app.services.video_engine"].ENGINE_NAME = ver.ENGINE_NAME
    sys.modules["app.services.video_engine"].ENGINE_VERSION = ver.ENGINE_VERSION
    sys.modules["app.services.video_engine"].ENGINE_LABEL = ver.ENGINE_LABEL


def _load_audio_export():
    _ensure_parents("app.services.audio_export")
    if "app.services.audio_export.engine" in sys.modules:
        return
    # discover modules
    files = sorted(p.name for p in AE.glob("*.py") if p.name != "__init__.py")
    pkg = type(sys)("app.services.audio_export")
    pkg.__path__ = [str(AE)]
    sys.modules["app.services.audio_export"] = pkg
    # load dependency order guess
    order = [
        "version",
        "models",
        "profiles",
        "store",
        "queue",
        "validators",
        "packager",
        "delivery",
        "engine",
    ]
    loaded = set()
    for name in order:
        path = AE / f"{name}.py"
        if path.exists():
            _load(f"app.services.audio_export.{name}", path)
            loaded.add(name)
    for name in files:
        mod = name[:-3]
        if mod not in loaded:
            try:
                _load(f"app.services.audio_export.{mod}", AE / name)
            except Exception:
                pass
    eng = sys.modules.get("app.services.audio_export.engine")
    if eng:
        sys.modules["app.services.audio_export"].create_export_dict = eng.create_export_dict
        sys.modules["app.services.audio_export"].download_export = eng.download_export
        if hasattr(eng, "ENGINE_LABEL"):
            sys.modules["app.services.audio_export"].ENGINE_LABEL = eng.ENGINE_LABEL


_load_video_engine()
_load_audio_export()

_load_pkg(
    "app.services.final_release",
    FR,
    [
        ("version", "version.py"),
        ("quality", "quality.py"),
        ("stress", "stress.py"),
        ("pipeline", "pipeline.py"),
        ("engine", "engine.py"),
    ],
)

version = sys.modules["app.services.final_release.version"]
quality = sys.modules["app.services.final_release.quality"]
stress = sys.modules["app.services.final_release.stress"]
pipeline = sys.modules["app.services.final_release.pipeline"]
engine = sys.modules["app.services.final_release.engine"]
di_store = sys.modules["app.services.director_intelligence.store"]
di_queue = sys.modules["app.services.director_intelligence.queue"]
di_memory = sys.modules["app.services.director_intelligence.memory"]
di_version = sys.modules["app.services.director_intelligence.version"]


def setup_function():
    di_store.clear()
    di_queue.director_queue.clear()
    di_memory.clear()


def test_final_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 5
    assert version.SPRINT == 10
    assert version.FINAL_RELEASE is True
    assert version.READY_FOR_PHASE_6 is True
    assert di_version.SPRINT == 10
    assert "Director Engine" in di_version.ENGINE_NAME


def test_release_pipeline_integration():
    result = engine.verify_release(
        "Cinematic short film — a teacher inspires students through conflict to triumph.",
        format_type="short_film",
        genre="inspirational",
    )
    assert result["ok"] is True
    assert result["pipeline_stages"]["director"] is True
    assert result["pipeline_stages"]["scene_planner"] is True
    assert result["pipeline_stages"]["shot_planner"] is True
    assert result["pipeline_stages"]["camera_planner"] is True
    assert result["pipeline_stages"]["audio_planner"] is True
    assert result["pipeline_stages"]["video_engine"] is True
    assert result["pipeline_stages"]["renderer"] is True
    assert result["pipeline_stages"]["exporter"] is True
    assert result["pipeline_stages"]["download"] is True
    v = result["verification"]
    for key in (
        "director_planning",
        "scene_ordering",
        "character_memory",
        "camera_logic",
        "motion_logic",
        "lighting_logic",
        "emotion_logic",
        "transition_logic",
        "audio_synchronization",
        "export_package",
        "download_package",
        "quality_score",
        "retry_system",
        "analytics",
        "production_monitoring",
    ):
        assert v[key] is True, key
    assert result["quality"]["overall_production_score"] >= version.QUALITY_THRESHOLD
    assert result["scene_count"] >= 4
    assert result["shot_count"] >= 4


def test_quality_multi_prompt():
    prompts = [
        ("Epic action short for YouTube about a chase through the city.", "youtube", "action"),
        ("Romantic music video at golden hour on the beach.", "music_video", "romance"),
        ("Islamic educational video about patience and hope.", "islamic_video", "faith"),
        ("Corporate brand film for a startup product launch.", "corporate", "corporate"),
        ("TikTok comedy reel with fast transitions.", "tiktok", "comedy"),
    ]
    scores = []
    for prompt, fmt, genre in prompts:
        result = engine.verify_release(prompt, format_type=fmt, genre=genre)
        assert result["ok"] is True
        q = result["quality"]
        assert q["passed"] is True
        assert q["scene_quality"] >= 60
        assert q["camera_quality"] >= 60
        assert q["continuity"] >= 60
        assert q["emotion"] >= 60
        assert q["identity_lock"] >= 80
        scores.append(q["overall_production_score"])
    assert min(scores) >= version.QUALITY_THRESHOLD
    assert sum(scores) / len(scores) >= 85.0


def test_stress_50_and_100():
    b50 = stress.run_stress_batch(50, format_type="shorts")
    assert b50["job_count"] == 50
    assert b50["passed"] is True
    assert b50["failures"] == 0
    assert b50["min_accuracy"] >= 80
    assert b50["avg_generation_ms"] > 0
    assert "queue" in b50
    assert "memory_peak_mb" in b50

    b100 = stress.run_stress_batch(100, format_type="reels")
    assert b100["job_count"] == 100
    assert b100["passed"] is True
    assert b100["failures"] == 0


def test_stress_250_and_500():
    b250 = stress.run_stress_batch(250, format_type="tiktok")
    assert b250["job_count"] == 250
    assert b250["passed"] is True
    assert b250["failures"] == 0
    assert b250["jobs_per_sec"] > 0

    b500 = stress.run_stress_batch(500, format_type="shorts")
    assert b500["job_count"] == 500
    assert b500["passed"] is True
    assert b500["failures"] == 0
    assert b500["min_accuracy"] >= 80
    assert b500["retry_count"] >= 0


def test_final_report_complete():
    report = engine.final_report(run_stress=True, stress_max_jobs=20)
    assert report["ok"] is True
    assert report["phase_status"] == "COMPLETE"
    assert report["ready_for_phase_6"] is True
    assert report["final_version"] == "RTAS Studio AI Director Engine v1.0.0"
    assert len(report["modules_completed"]) >= 15
    assert report["overall_production_score"] >= 80
    assert "PHASE 5 COMPLETE" in report["mark"]


def test_performance_budget_pipeline():
    t0 = time.perf_counter()
    result = engine.verify_release(
        "Performance budget cinematic documentary ocean explorers.",
        format_type="documentary",
    )
    elapsed = time.perf_counter() - t0
    assert result["ok"] is True
    assert elapsed < 15.0
    assert result["processing_time_ms"] < 15000
