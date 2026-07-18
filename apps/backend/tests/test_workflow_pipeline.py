"""Phase 6 Sprint 7 — AI Workflow Automation & Pipeline Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WP = ROOT / "app" / "services" / "workflow_pipeline"

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


def _load_pkg():
    _ensure_parents("app.services.workflow_pipeline")
    pkg = type(sys)("app.services.workflow_pipeline")
    pkg.__path__ = [str(WP)]
    sys.modules["app.services.workflow_pipeline"] = pkg
    for name in (
        "version",
        "models",
        "templates",
        "store",
        "dependencies",
        "validator",
        "security",
        "observability",
        "automation",
        "scheduler",
        "pipeline_engine",
        "workflow_engine",
        "engine",
    ):
        _load(f"app.services.workflow_pipeline.{name}", WP / f"{name}.py")
    eng = sys.modules["app.services.workflow_pipeline.engine"]
    ver = sys.modules["app.services.workflow_pipeline.version"]
    pkg.ENGINE_NAME = ver.ENGINE_NAME
    pkg.ENGINE_VERSION = ver.ENGINE_VERSION
    pkg.ENGINE_LABEL = ver.ENGINE_LABEL
    pkg.get_workflow_engine = eng.get_workflow_engine
    pkg.reset_engine = eng.reset_engine


_load_pkg()

version = sys.modules["app.services.workflow_pipeline.version"]
models = sys.modules["app.services.workflow_pipeline.models"]
templates = sys.modules["app.services.workflow_pipeline.templates"]
validator = sys.modules["app.services.workflow_pipeline.validator"]
security = sys.modules["app.services.workflow_pipeline.security"]
engine_mod = sys.modules["app.services.workflow_pipeline.engine"]


def setup_function():
    engine_mod.reset_engine()


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 6
    assert version.SPRINT == 7


def test_production_template_chain():
    tpl = templates.production_pipeline_template()
    names = [s.name for s in tpl.stages]
    assert names[0] == "prompt"
    assert names[-1] == "download"
    assert "director" in names and "export" in names
    v = validator.validate_template_stages(tpl.stages)
    assert v["valid"] is True


def test_full_workflow_auto_pipeline():
    eng = engine_mod.get_workflow_engine()
    result = eng.create(
        user_id="u1",
        prompt="Create a sci-fi short about Orion",
        project_id="p1",
        auto_trigger=True,
        metadata={"work_ms": 1, "wait_ms": 8000},
    )
    assert result["status"] == "completed"
    assert result["workflow_id"]
    completed = [s["name"] for s in result["stages"] if s["status"] == "completed"]
    assert completed[0] == "prompt"
    assert completed[-1] == "download"
    assert len(completed) == len(models.PRODUCTION_STAGES)


def test_custom_workflow():
    eng = engine_mod.get_workflow_engine()
    result = eng.create(
        user_id="u1",
        prompt="custom path",
        custom_stages=["prompt", "story", "export"],
        auto_trigger=True,
        metadata={"work_ms": 1, "wait_ms": 5000},
    )
    assert result["status"] == "completed"
    names = [s["name"] for s in result["stages"]]
    assert names == ["prompt", "story", "export"]


def test_auto_retry_recovery():
    eng = engine_mod.get_workflow_engine()
    result = eng.create(
        user_id="u1",
        prompt="retry path",
        custom_stages=["prompt", "story", "export"],
        auto_trigger=True,
        metadata={
            "work_ms": 1,
            "wait_ms": 8000,
            "fail_stages": ["story"],
            "fail_until_retry": 1,
        },
    )
    assert result["status"] == "completed"
    story = next(s for s in result["stages"] if s["name"] == "story")
    assert story["status"] == "completed"
    assert story["retry_count"] >= 1


def test_cancel_and_authorization():
    eng = engine_mod.get_workflow_engine()
    created = eng.create(
        user_id="owner",
        prompt="will cancel",
        auto_trigger=False,
        custom_stages=["prompt", "story"],
    )
    wid = created["workflow_id"]
    cancelled = eng.cancel(user_id="owner", workflow_id=wid)
    assert cancelled["status"] == "cancelled"
    try:
        eng.get(wid, user_id="intruder")
        assert False, "expected auth error"
    except security.WorkflowAuthError:
        pass


def test_resume_workflow():
    eng = engine_mod.get_workflow_engine()
    created = eng.create(
        user_id="u1",
        prompt="resume me",
        custom_stages=["prompt", "story", "export"],
        auto_trigger=False,
        metadata={"work_ms": 1, "wait_ms": 5000},
    )
    wid = created["workflow_id"]
    started = eng.start(user_id="u1", workflow_id=wid)
    assert started["status"] == "completed"
    # resume completed is idempotent ok
    resumed = eng.resume(user_id="u1", workflow_id=wid)
    assert resumed["status"] == "completed"


def test_pipeline_status_and_history():
    eng = engine_mod.get_workflow_engine()
    eng.create(
        user_id="u1",
        prompt="obs",
        custom_stages=["prompt", "export"],
        auto_trigger=True,
        metadata={"work_ms": 1, "wait_ms": 5000},
    )
    hist = eng.history(user_id="u1")
    assert hist["count"] >= 1
    assert "observability" in hist
    status = eng.pipeline_status()
    assert "observability" in status
    obs = status["observability"]
    assert "workflow_success_rate" in obs
    assert "pipeline_success_rate" in obs
    assert "average_runtime_ms" in obs
    assert "retry_statistics" in obs
    assert "queue_efficiency" in obs


def test_validator_rejects_bad_deps():
    from app.services.workflow_pipeline.models import StageSpec

    bad = [StageSpec(name="story", depends_on=["missing"])]
    v = validator.validate_template_stages(bad)
    assert v["valid"] is False


def test_stress_workflows():
    eng = engine_mod.get_workflow_engine()
    t0 = time.perf_counter()
    ids = []
    for i in range(20):
        r = eng.create(
            user_id="stress",
            prompt=f"stress workflow {i}",
            custom_stages=["prompt", "story", "export"],
            auto_trigger=True,
            metadata={"work_ms": 1, "wait_ms": 8000},
        )
        ids.append(r["workflow_id"])
        assert r["status"] == "completed"
    elapsed = time.perf_counter() - t0
    hist = eng.history(user_id="stress", limit=50)
    assert hist["count"] >= 20
    assert elapsed < 20.0
    obs = eng.observability()
    assert obs["workflow_success_rate"] >= 95.0
