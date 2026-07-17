"""Phase 3 Sprint 9 — Multi GPU Engine tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MG = ROOT / "app" / "services" / "multi_gpu"


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
    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(pkg_path)]
    sys.modules[pkg_name] = pkg
    # Ensure backend root is importable as `app`
    backend = ROOT
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))
    for mod_name, file_name in modules:
        _load(f"{pkg_name}.{mod_name}", pkg_path / file_name)


_load_pkg(
    "app.services.multi_gpu",
    MG,
    [
        ("models", "models.py"),
        ("catalog", "catalog.py"),
        ("workers", "workers.py"),
        ("balancer", "balancer.py"),
        ("retry", "retry.py"),
        ("monitor", "monitor.py"),
        ("queue", "queue.py"),
        ("distributor", "distributor.py"),
        ("bridge", "bridge.py"),
        ("store", "store.py"),
        ("engine", "engine.py"),
    ],
)

engine = sys.modules["app.services.multi_gpu.engine"]
catalog = sys.modules["app.services.multi_gpu.catalog"]
workers = sys.modules["app.services.multi_gpu.workers"]
retry = sys.modules["app.services.multi_gpu.retry"]
distributor = sys.modules["app.services.multi_gpu.distributor"]
queue = sys.modules["app.services.multi_gpu.queue"]
balancer = sys.modules["app.services.multi_gpu.balancer"]


def setup():
    workers.clear_workers()
    queue.clear_queue()


def test_catalog_skus():
    required = {"H100", "A100", "L40S", "RTX", "CLOUD"}
    assert required.issubset(set(catalog.GPU_SKUS))
    assert catalog.normalize_sku("h100") == "H100"
    assert catalog.normalize_sku("L40") == "L40S"
    prefs = catalog.preferred_skus(quality="cinema", require_rt=False)
    assert prefs[0] == "H100"
    rt_prefs = catalog.preferred_skus(quality="production", require_rt=True)
    assert "L40S" in rt_prefs or "RTX" in rt_prefs
    assert "H100" not in rt_prefs  # no RT


def test_fleet_and_balance():
    setup()
    fleet = workers.ensure_default_fleet()
    assert len(fleet) >= 8
    skus = {w.sku for w in fleet}
    assert {"H100", "A100", "L40S", "RTX", "CLOUD"}.issubset(skus)
    qbal = balancer.queue_balance_report(fleet)
    lbal = balancer.load_balance_report(fleet)
    assert "by_sku" in qbal
    assert "avg_load" in lbal


def test_retry_escalation():
    setup()
    job = queue.make_job(
        kind="scene_render",
        preferred_skus=["RTX", "CLOUD"],
        required_vram_mb=8192,
        max_attempts=3,
    )
    policy = retry.default_retry_policy()
    out = retry.apply_retry(job, policy, "CUDA OOM on worker")
    assert out.state == "retrying"
    assert out.attempts == 1
    assert "H100" in out.preferred_skus or "A100" in out.preferred_skus
    out2 = retry.apply_retry(out, policy, "fatal corrupt payload")
    # fatal should fail if not in retry_on
    assert out2.state in ("failed", "retrying")


def test_full_plan_distribution():
    setup()
    plan = engine.build_multi_gpu_plan(
        scene_render={
            "job_id": "scenerender_test",
            "quality": "production",
            "ray_tracing_ready": True,
            "gpu_queue": [
                {
                    "job_id": "gpu_a",
                    "scene_index": 0,
                    "priority": 10,
                    "estimated_vram_mb": 4096,
                    "estimated_ms": 8000,
                    "quality": "production",
                },
                {
                    "job_id": "gpu_b",
                    "scene_index": 1,
                    "priority": 20,
                    "estimated_vram_mb": 6144,
                    "estimated_ms": 12000,
                    "quality": "production",
                },
            ],
        },
        strategy="capability_match",
        quality="production",
        seed_fleet=True,
        distribute=True,
        parent_generation_id="gen_mg_1",
    )
    assert plan.job_id.startswith("multigpu_")
    assert plan.strategy == "capability_match"
    assert len(plan.workers) >= 8
    assert len(plan.jobs) == 2
    assert plan.distribution.get("assigned_count", 0) >= 1
    assert any(j.assigned_worker_id for j in plan.jobs)
    # RT jobs should prefer RT-capable SKUs when possible
    assigned_skus = {j.assigned_sku for j in plan.jobs if j.assigned_sku}
    assert assigned_skus.issubset({"H100", "A100", "L40S", "RTX", "CLOUD"})
    assert plan.monitoring.workers_online + plan.monitoring.workers_busy >= 1
    assert plan.queue_balance.get("by_sku")
    assert plan.load_balance.get("avg_load") is not None
    assert "H100" in plan.summary()["skus"]
    assert engine.get_plan(plan.job_id) is not None

    # complete + retry path
    jid = next(j.job_id for j in plan.jobs if j.assigned_worker_id)
    done = distributor.complete_job(jid, success=False, error="timeout waiting for kernel")
    assert done is not None
    assert done.state in ("retrying", "failed")


def test_round_robin_and_least_load():
    setup()
    for strategy in ("round_robin", "least_load", "least_queue"):
        workers.clear_workers()
        queue.clear_queue()
        plan = engine.build_multi_gpu_plan(
            jobs=[
                {"kind": "generic", "priority": 10, "required_vram_mb": 2048},
                {"kind": "generic", "priority": 20, "required_vram_mb": 2048},
                {"kind": "generic", "priority": 30, "required_vram_mb": 2048},
            ],
            strategy=strategy,
            seed_fleet=True,
            distribute=True,
        )
        assert plan.strategy == strategy
        assert plan.distribution["assigned_count"] >= 1


def test_dict_export():
    setup()
    result = engine.build_multi_gpu_dict(
        quality="cinema",
        seed_fleet=True,
        distribute=True,
    )
    assert "plan" in result and "summary" in result
    assert result["summary"]["job_id"].startswith("multigpu_")


if __name__ == "__main__":
    test_catalog_skus()
    test_fleet_and_balance()
    test_retry_escalation()
    test_full_plan_distribution()
    test_round_robin_and_least_load()
    test_dict_export()
    print("OK multi_gpu")
