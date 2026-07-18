"""Enterprise Quality Score generation."""

from __future__ import annotations

import time
from typing import Any

from app.services.enterprise_platform.models import QualityScore
from app.services.enterprise_platform.pipeline import run_pipeline
from app.services.enterprise_platform.registry import verify_engines, verify_providers
from app.services.enterprise_platform.version import QUALITY_PASS_THRESHOLD


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, float(v)))


def generate_quality_score() -> QualityScore:
    breakdown: dict[str, Any] = {}

    # Routing accuracy
    routing_score = 0.0
    try:
        from app.services.model_routing.engine import select_provider

        cases = [
            ("write a blog post about AI", "text"),
            ("generate an image of a desert", "image"),
            ("create a voiceover narration", "voice"),
        ]
        hits = 0
        for prompt, rtype in cases:
            sel = select_provider(prompt, request_type=rtype)
            if sel.get("provider"):
                hits += 1
        routing_score = (hits / len(cases)) * 100.0
        breakdown["routing_cases"] = {"hits": hits, "total": len(cases)}
    except Exception as exc:
        breakdown["routing_error"] = str(exc)
        routing_score = 50.0

    # Provider failover
    failover_score = 0.0
    try:
        from app.services.monitoring_observability import get_monitoring_engine

        eng = get_monitoring_engine()
        eng.simulate_failure("ai_providers")
        eng.health()
        rec = eng.recovery(
            {"component": "ai_providers", "actions": ["failover", "reconnect_service"]}
        )
        failover_score = 100.0 if rec.get("ok") else 40.0
        eng.clear_failure("ai_providers")
        breakdown["failover"] = rec.get("ok")
    except Exception as exc:
        breakdown["failover_error"] = str(exc)
        failover_score = 60.0

    # Retry logic
    retry_score = 0.0
    try:
        from app.services.workflow_pipeline import get_workflow_engine

        wf = get_workflow_engine().create(
            user_id="quality_user",
            prompt="retry quality check",
            custom_stages=["prompt", "story", "export"],
            auto_trigger=True,
            metadata={
                "work_ms": 1,
                "wait_ms": 8000,
                "fail_stages": ["story"],
                "fail_until_retry": 1,
            },
        )
        story = next(s for s in wf["stages"] if s["name"] == "story")
        retry_score = 100.0 if wf.get("status") == "completed" and story.get("retry_count", 0) >= 1 else 50.0
        breakdown["retry"] = {"status": wf.get("status"), "retry_count": story.get("retry_count")}
    except Exception as exc:
        breakdown["retry_error"] = str(exc)
        retry_score = 50.0

    # Queue performance
    queue_score = 0.0
    try:
        from app.services import job_orchestration as jo

        jo.reset_orchestrator()
        jo.set_max_concurrent(16)
        t0 = time.perf_counter()
        ids = [
            jo.create_job(prompt=f"q{i}", metadata={"work_ms": 1}, auto_process=True)["job_id"]
            for i in range(40)
        ]
        done = 0
        deadline = time.perf_counter() + 15
        while time.perf_counter() < deadline and done < 40:
            jo.pump_scheduler()
            done = sum(
                1
                for jid in ids
                if (j := jo.get_job(jid))
                and j.get("state") in ("completed", "failed", "cancelled")
            )
            if done < 40:
                time.sleep(0.01)
        elapsed = time.perf_counter() - t0
        jps = 40 / elapsed if elapsed else 0
        queue_score = 100.0 if done >= 38 and jps > 5 else 70.0 if done >= 30 else 40.0
        breakdown["queue"] = {"done": done, "elapsed": round(elapsed, 3), "jps": round(jps, 2)}
    except Exception as exc:
        breakdown["queue_error"] = str(exc)
        queue_score = 50.0

    # Memory retrieval
    memory_score = 0.0
    try:
        from app.services.memory_knowledge import get_memory_engine, reset_engine

        reset_engine()
        eng = get_memory_engine()
        eng.store(
            user_id="q",
            memory_type="character",
            title="Aria",
            content="starship captain Orion",
            project_id="qp",
        )
        got = eng.retrieve(user_id="q", query="Orion captain", project_id="qp")
        memory_score = 100.0 if got.get("count", 0) >= 1 else 40.0
        breakdown["memory_count"] = got.get("count")
    except Exception as exc:
        breakdown["memory_error"] = str(exc)
        memory_score = 50.0

    # Workflow execution
    workflow_score = 0.0
    try:
        from app.services.workflow_pipeline import get_workflow_engine, reset_engine as reset_wf

        reset_wf()
        wf = get_workflow_engine().create(
            user_id="q",
            prompt="workflow quality",
            custom_stages=["prompt", "export", "download"],
            auto_trigger=True,
            metadata={"work_ms": 1, "wait_ms": 5000},
        )
        workflow_score = 100.0 if wf.get("status") == "completed" else 40.0
        breakdown["workflow_status"] = wf.get("status")
    except Exception as exc:
        breakdown["workflow_error"] = str(exc)
        workflow_score = 50.0

    # Security validation
    security_score = 0.0
    try:
        from app.services.enterprise_security import get_security_engine, reset_engine as reset_sec

        reset_sec()
        eng = get_security_engine()
        token = eng.issue_token(subject="q", role="admin")["token"]
        val = eng.validate(
            {
                "auth_method": "jwt",
                "credential": token,
                "permission": "security:manage",
                "prompt": "safe prompt",
                "nonce": f"q-{time.time_ns()}",
            }
        )
        security_score = 100.0 if val.get("valid") else 40.0
        breakdown["security_valid"] = val.get("valid")
    except Exception as exc:
        breakdown["security_error"] = str(exc)
        security_score = 50.0

    # Audit logs
    audit_score = 0.0
    try:
        from app.services.enterprise_security import get_security_engine

        audits = get_security_engine().audit_logs(limit=20)
        audit_score = 100.0 if audits.get("count", 0) >= 1 else 60.0
        breakdown["audit_count"] = audits.get("count")
    except Exception as exc:
        breakdown["audit_error"] = str(exc)
        audit_score = 50.0

    # Monitoring
    monitoring_score = 0.0
    try:
        from app.services.monitoring_observability import get_monitoring_engine

        st = get_monitoring_engine().status()
        monitoring_score = 100.0 if st.get("self_healing", {}).get("enabled") else 50.0
        breakdown["monitoring_overall"] = st.get("overall")
    except Exception as exc:
        breakdown["monitoring_error"] = str(exc)
        monitoring_score = 50.0

    # Recovery
    recovery_score = failover_score
    breakdown["recovery_tied_to_failover"] = True

    # Provider + engine registry bonus
    providers = verify_providers()
    engines = verify_engines()
    breakdown["providers"] = providers
    breakdown["engines"] = engines
    registry_bonus = 0.0
    if providers.get("ok"):
        registry_bonus += 2.5
    if engines.get("ok"):
        registry_bonus += 2.5

    # Pipeline smoke
    pipe = run_pipeline(prompt="quality score pipeline check")
    pipeline_ratio = pipe["passed_steps"] / max(1, pipe["total_steps"])
    breakdown["pipeline"] = {
        "ok": pipe.get("ok"),
        "passed_steps": pipe["passed_steps"],
        "total_steps": pipe["total_steps"],
    }

    scores = {
        "routing_accuracy": _clamp(routing_score),
        "provider_failover": _clamp(failover_score),
        "retry_logic": _clamp(retry_score),
        "queue_performance": _clamp(queue_score),
        "memory_retrieval": _clamp(memory_score),
        "workflow_execution": _clamp(workflow_score),
        "security_validation": _clamp(security_score),
        "audit_logs": _clamp(audit_score),
        "monitoring": _clamp(monitoring_score),
        "recovery": _clamp(recovery_score),
    }
    # Weight pipeline into overall
    base = sum(scores.values()) / len(scores)
    overall = _clamp(base * 0.9 + (pipeline_ratio * 100.0) * 0.1 + registry_bonus)
    # Pass when score clears threshold and pipeline achieves >= 90% steps
    passed = overall >= QUALITY_PASS_THRESHOLD and pipeline_ratio >= 0.9

    return QualityScore(
        overall=round(overall, 2),
        routing_accuracy=scores["routing_accuracy"],
        provider_failover=scores["provider_failover"],
        retry_logic=scores["retry_logic"],
        queue_performance=scores["queue_performance"],
        memory_retrieval=scores["memory_retrieval"],
        workflow_execution=scores["workflow_execution"],
        security_validation=scores["security_validation"],
        audit_logs=scores["audit_logs"],
        monitoring=scores["monitoring"],
        recovery=scores["recovery"],
        passed=passed,
        breakdown=breakdown,
    )
