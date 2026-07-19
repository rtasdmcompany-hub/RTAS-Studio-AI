"""Phase 6 Sprint 10 — Enterprise AI Orchestration Platform final integration tests."""

from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVC = ROOT / "app" / "services"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("RTAS_JWT_SECRET", "platform-test-jwt-secret-key-32b")
os.environ.setdefault("AI_BACKEND_SECRET", "platform-test-backend-secret-32b")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_pkg(pkg_name: str, path: Path | None = None):
    parts = pkg_name.split(".")
    for i in range(1, len(parts) + 1):
        name = ".".join(parts[:i])
        if name not in sys.modules:
            mod = types.ModuleType(name)
            mod.__path__ = []
            sys.modules[name] = mod
    if "app" in sys.modules:
        sys.modules["app"].__path__ = [str(ROOT / "app")]
    if "app.services" in sys.modules:
        # Prevent importing heavy app.services.__init__
        sys.modules["app.services"].__path__ = [str(SVC)]
        sys.modules["app.services"].__file__ = str(SVC / "__init__.py")
    if path is not None:
        sys.modules[pkg_name].__path__ = [str(path)]


def _load_package(pkg: str, folder: str, modules: tuple[str, ...]):
    path = SVC / folder
    _ensure_pkg(pkg, path)
    for name in modules:
        fp = path / f"{name}.py"
        if fp.exists():
            _load(f"{pkg}.{name}", fp)
    # Wire common exports on package module
    pkg_mod = sys.modules[pkg]
    if "version" in modules and f"{pkg}.version" in sys.modules:
        ver = sys.modules[f"{pkg}.version"]
        for attr in (
            "ENGINE_NAME",
            "ENGINE_VERSION",
            "ENGINE_LABEL",
            "PLATFORM_NAME",
            "PLATFORM_VERSION",
            "PLATFORM_LABEL",
        ):
            if hasattr(ver, attr):
                setattr(pkg_mod, attr, getattr(ver, attr))
    return pkg_mod


def _bootstrap():
    # Only skip when every module setup_function depends on is already loaded.
    # A prior test in the same session may have loaded enterprise_platform.engine
    # without these dependencies, which previously caused a KeyError at setup.
    _required = (
        "app.services.enterprise_platform.engine",
        "app.services.memory_knowledge",
        "app.services.workflow_pipeline",
        "app.services.enterprise_security",
        "app.services.monitoring_observability",
        "app.services.cost_intelligence",
        "app.services.job_orchestration",
    )
    if all(name in sys.modules for name in _required):
        return

    # Minimal config stub for connectors that may read settings
    _ensure_pkg("app.core")
    if "app.core.config" not in sys.modules:
        cfg = types.ModuleType("app.core.config")

        class _S:
            ai_backend_secret = os.environ.get("AI_BACKEND_SECRET")
            fal_configured = False
            replicate_configured = False

        cfg.settings = _S()
        cfg.reload_settings = lambda: None
        cfg.get_settings = lambda: _S()
        sys.modules["app.core.config"] = cfg
        sys.modules["app.core"].config = cfg

    _load_package(
        "app.services.provider_orchestration",
        "provider_orchestration",
        (
            "version",
            "models",
            "base",
            "registry",
            "priority",
            "health",
            "builtins",
            "discovery",
            "manager",
        ),
    )
    po = sys.modules["app.services.provider_orchestration"]
    mgr = sys.modules["app.services.provider_orchestration.manager"]
    po.get_provider_manager = mgr.get_provider_manager
    po.reset_provider_manager = getattr(mgr, "reset_provider_manager", lambda: None)

    # Connectors — load lightly if present
    conn_path = SVC / "provider_connectors"
    if conn_path.exists():
        _ensure_pkg("app.services.provider_connectors", conn_path)
        for name in ("version", "models", "config", "auth", "retry", "base", "registry", "health", "engine"):
            fp = conn_path / f"{name}.py"
            if fp.exists():
                try:
                    _load(f"app.services.provider_connectors.{name}", fp)
                except Exception:
                    pass
        if "app.services.provider_connectors.engine" in sys.modules:
            pc = sys.modules["app.services.provider_connectors"]
            eng = sys.modules["app.services.provider_connectors.engine"]
            if hasattr(eng, "get_connector_engine"):
                pc.get_connector_engine = eng.get_connector_engine

    _load_package(
        "app.services.model_routing",
        "model_routing",
        (
            "version",
            "models",
            "detection",
            "rules",
            "model_registry",
            "scoring",
            "analytics",
            "engine",
        ),
    )

    _load_package(
        "app.services.cost_intelligence",
        "cost_intelligence",
        (
            "version",
            "models",
            "pricing",
            "store",
            "token_tracker",
            "credit_tracker",
            "budget",
            "analytics",
            "ranking",
            "reports",
            "optimizer",
            "monitoring",
            "engine",
        ),
    )
    ci = sys.modules["app.services.cost_intelligence"]
    ci.get_cost_engine = sys.modules["app.services.cost_intelligence.engine"].get_cost_engine
    ci.reset_engine = sys.modules["app.services.cost_intelligence.engine"].reset_engine

    _load_package(
        "app.services.job_orchestration",
        "job_orchestration",
        ("version", "models", "store", "retry", "queue_manager", "metrics", "orchestrator"),
    )
    jo = sys.modules["app.services.job_orchestration"]
    orch = sys.modules["app.services.job_orchestration.orchestrator"]
    for name in (
        "create_job",
        "get_job",
        "jobs_status",
        "wait_for_job",
        "pump_scheduler",
        "reset_orchestrator",
        "set_max_concurrent",
        "create_dict",
    ):
        if hasattr(orch, name):
            setattr(jo, name, getattr(orch, name))

    _load_package(
        "app.services.memory_knowledge",
        "memory_knowledge",
        (
            "version",
            "models",
            "crypto",
            "store",
            "security",
            "cache",
            "metrics",
            "retrieval",
            "memory_engine",
            "context_engine",
            "knowledge_engine",
            "engine",
        ),
    )
    mk = sys.modules["app.services.memory_knowledge"]
    mk.get_memory_engine = sys.modules["app.services.memory_knowledge.engine"].get_memory_engine
    mk.reset_engine = sys.modules["app.services.memory_knowledge.engine"].reset_engine

    _load_package(
        "app.services.workflow_pipeline",
        "workflow_pipeline",
        (
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
        ),
    )
    wp = sys.modules["app.services.workflow_pipeline"]
    wp.get_workflow_engine = sys.modules["app.services.workflow_pipeline.engine"].get_workflow_engine
    wp.reset_engine = sys.modules["app.services.workflow_pipeline.engine"].reset_engine

    _load_package(
        "app.services.enterprise_security",
        "enterprise_security",
        (
            "version",
            "models",
            "store",
            "secrets",
            "auth",
            "rbac",
            "api_security",
            "policies",
            "audit",
            "compliance",
            "observability",
            "engine",
        ),
    )
    es = sys.modules["app.services.enterprise_security"]
    es.get_security_engine = sys.modules["app.services.enterprise_security.engine"].get_security_engine
    es.reset_engine = sys.modules["app.services.enterprise_security.engine"].reset_engine

    _load_package(
        "app.services.monitoring_observability",
        "monitoring_observability",
        (
            "version",
            "models",
            "store",
            "health_monitor",
            "alerts",
            "incidents",
            "self_healing",
            "diagnostics",
            "predictive",
            "metrics",
            "engine",
        ),
    )
    mo = sys.modules["app.services.monitoring_observability"]
    mo.get_monitoring_engine = sys.modules[
        "app.services.monitoring_observability.engine"
    ].get_monitoring_engine
    mo.reset_engine = sys.modules["app.services.monitoring_observability.engine"].reset_engine

    _load_package(
        "app.services.enterprise_platform",
        "enterprise_platform",
        ("version", "models", "registry", "pipeline", "quality", "stress", "engine"),
    )
    ep = sys.modules["app.services.enterprise_platform"]
    eng = sys.modules["app.services.enterprise_platform.engine"]
    ep.get_platform_engine = eng.get_platform_engine
    ep.reset_engine = eng.reset_engine
    ep.PLATFORM_VERSION = sys.modules["app.services.enterprise_platform.version"].PLATFORM_VERSION


_bootstrap()

version = sys.modules["app.services.enterprise_platform.version"]
registry = sys.modules["app.services.enterprise_platform.registry"]
pipeline = sys.modules["app.services.enterprise_platform.pipeline"]
quality = sys.modules["app.services.enterprise_platform.quality"]
stress = sys.modules["app.services.enterprise_platform.stress"]
engine_mod = sys.modules["app.services.enterprise_platform.engine"]
jo = sys.modules["app.services.job_orchestration"]

# Capture dependency module references at import time. Other test modules
# collected later can remove these entries from sys.modules, so we hold direct
# references to keep setup_function robust regardless of collection order.
_memory_knowledge = sys.modules["app.services.memory_knowledge"]
_workflow_pipeline = sys.modules["app.services.workflow_pipeline"]
_enterprise_security = sys.modules["app.services.enterprise_security"]
_monitoring_observability = sys.modules["app.services.monitoring_observability"]
_cost_intelligence = sys.modules["app.services.cost_intelligence"]


def setup_function():
    engine_mod.reset_engine()
    jo.reset_orchestrator()
    _memory_knowledge.reset_engine()
    _workflow_pipeline.reset_engine()
    _enterprise_security.reset_engine()
    _monitoring_observability.reset_engine()
    _cost_intelligence.reset_engine()


def test_version_unit():
    assert version.PLATFORM_VERSION == "1.0.0"
    assert version.PHASE == 6
    assert version.SPRINT == 10


def test_providers_verified():
    providers = registry.verify_providers()
    assert providers["ok"] is True
    for req in ("openai", "gemini", "claude", "runpod", "stability", "elevenlabs"):
        assert req in providers["found"]
    assert providers["unlimited_extension"] is True


def test_engines_integrated():
    engines = registry.verify_engines()
    assert engines["ok"] is True, engines.get("missing")
    for name in version.INTEGRATED_ENGINES:
        assert engines["checks"].get(name) is True, name


def test_end_to_end_pipeline():
    result = pipeline.run_pipeline(prompt="E2E Orion captain sunrise platform test")
    assert result["total_steps"] == 12
    assert result["passed_steps"] == 12, result
    assert result["ok"] is True


def test_enterprise_quality_score():
    score = quality.generate_quality_score()
    assert score.overall >= 90.0, score.to_dict()
    assert score.passed is True


def test_stress_batches_to_1000():
    quick = stress.run_stress([50, 100])
    assert quick["ok"] is True
    full = stress.run_stress([50, 100, 250, 500, 1000])
    assert full["ok"] is True
    assert len(full["batches"]) == 5
    assert full["summary"]["total_jobs"] == 1900
    assert full["summary"]["passed"] is True


def test_platform_facade_release():
    eng = engine_mod.get_platform_engine()
    status = eng.status()
    assert status["ok"] is True
    assert status["phase"] == 6 and status["sprint"] == 10
    validation = eng.validate(prompt="platform facade validation")
    assert validation["ok"] is True
    q = eng.quality_report()
    assert q["enterprise_quality_score"] >= 90
    release = eng.release()
    assert release["ok"] is True
    assert release["release"]["status"] == "RELEASED"
