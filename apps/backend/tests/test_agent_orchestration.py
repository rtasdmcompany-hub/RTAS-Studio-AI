"""Phase 9 Sprint 7 — AI Agents, Automation Workflows & Orchestration tests."""

from __future__ import annotations

import importlib.util
import sys
import time
import uuid
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVC = ROOT / "app" / "services"

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
        sys.modules["app.services"].__path__ = [str(SVC)]


def _load_folder(folder: str, modules: tuple[str, ...]):
    path = SVC / folder
    pkg = f"app.services.{folder}"
    _ensure_parents(pkg)
    mod = type(sys)(pkg)
    mod.__path__ = [str(path)]
    sys.modules[pkg] = mod
    for name in modules:
        _load(f"{pkg}.{name}", path / f"{name}.py")
    return mod


def _bootstrap():
    _load_folder(
        "multi_tenant",
        ("version", "roles", "models", "validation", "store", "repository", "service", "engine"),
    )
    mt = sys.modules["app.services.multi_tenant"]
    mt.get_multi_tenant_service = sys.modules[
        "app.services.multi_tenant.service"
    ].get_multi_tenant_service
    mt.reset_engine = sys.modules["app.services.multi_tenant.service"].reset_engine

    _load_folder(
        "enterprise_auth",
        (
            "version",
            "errors",
            "models",
            "store",
            "audit",
            "permission_engine",
            "sessions",
            "validators",
            "middleware",
            "sso",
            "service",
            "engine",
        ),
    )
    ea = sys.modules["app.services.enterprise_auth"]
    ea.get_enterprise_auth_service = sys.modules[
        "app.services.enterprise_auth.service"
    ].get_enterprise_auth_service
    ea.reset_engine = sys.modules["app.services.enterprise_auth.service"].reset_engine
    ea.require_access = sys.modules["app.services.enterprise_auth.middleware"].require_access

    _load_folder(
        "agent_orchestration",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    ao = sys.modules["app.services.agent_orchestration"]
    ao.get_agent_orchestration_service = sys.modules[
        "app.services.agent_orchestration.service"
    ].get_agent_orchestration_service
    ao.reset_engine = sys.modules["app.services.agent_orchestration.service"].reset_engine


_bootstrap()


def _ao():
    return sys.modules["app.services.agent_orchestration.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.agent_orchestration.version"]


def _catalog():
    return sys.modules["app.services.agent_orchestration.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    _bootstrap()
    mod = _ao()
    mod._service = None
    sys.modules["app.services.agent_orchestration.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"ao-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Agent Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _svc():
    return _ao().get_agent_orchestration_service()


def _create_agent(org_id: str, actor: str, **overrides):
    payload = {
        "organizationId": org_id,
        "name": "Director Agent",
        "agentType": "director",
        "description": "Lead orchestrator",
    }
    payload.update(overrides)
    return _svc().agents.create(payload, actor_id=actor)


# --- Unit ---


def test_version_unit():
    v = _version()
    assert v.PHASE == 9
    assert v.SPRINT == 7
    assert "AI Agents" in v.ENGINE_NAME


def test_catalog_unit():
    c = _catalog()
    assert "director" in c.AGENT_TYPES
    assert "qa" in c.AGENT_TYPES
    assert "custom" in c.AGENT_TYPES
    assert "sequential" in c.TASK_MODES
    assert "parallel" in c.TASK_MODES
    assert "daily" in c.SCHEDULE_KINDS
    assert c.slugify("Scene Planner!") == "scene-planner"
    caps = c.agent_capabilities("camera_director")
    assert "camera.plan" in caps
    templates = c.default_workflow_templates()
    assert len(templates) >= 3


def test_engine_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["phase"] == 9
    assert status["sprint"] == 7
    assert len(status["engines"]) == 6
    assert all(v == "ready" for v in status["engines"].values())


# --- AI Agent Engine ---


def test_agent_crud():
    org_id = _seed_org("owner_ag")
    created = _create_agent(org_id, "owner_ag")
    agent = created["agent"]
    assert agent["agentType"] == "director"
    assert "orchestrate" in agent["capabilities"]

    got = _svc().agents.get(agent["id"], actor_id="owner_ag")
    assert got["agent"]["id"] == agent["id"]

    updated = _svc().agents.update(
        agent["id"],
        {"description": "Updated", "status": "paused"},
        actor_id="owner_ag",
    )
    assert updated["agent"]["description"] == "Updated"
    assert updated["agent"]["status"] == "paused"

    deleted = _svc().agents.delete(agent["id"], actor_id="owner_ag")
    assert deleted["status"] == "archived"


def test_all_agent_types():
    org_id = _seed_org("owner_types")
    for atype in _catalog().AGENT_TYPES:
        created = _create_agent(
            org_id,
            "owner_types",
            name=f"{atype} Agent",
            agentType=atype,
        )
        assert created["agent"]["agentType"] == atype


def test_agents_status_endpoint_data():
    org_id = _seed_org("owner_st")
    _create_agent(org_id, "owner_st", agentType="director")
    _create_agent(org_id, "owner_st", name="QA", agentType="qa")
    status = _svc().agents.status_summary(
        actor_id="owner_st", organization_id=org_id
    )
    assert status["totalAgents"] == 2
    assert status["byType"]["director"] == 1
    assert status["byType"]["qa"] == 1


# --- Memory ---


def test_agent_memory():
    org_id = _seed_org("owner_mem")
    agent = _create_agent(org_id, "owner_mem")["agent"]
    store_mod = sys.modules["app.services.agent_orchestration.store"]
    ag = store_mod.get_agent(agent["id"])
    mem = _svc().memory.remember(ag, "last_brief", {"tone": "cinematic"})
    assert mem.key == "last_brief"
    recalled = _svc().memory.recall(agent["id"], "last_brief", actor_id="owner_mem")
    assert recalled["memory"]["value"]["tone"] == "cinematic"
    listed = _svc().memory.list(agent["id"], actor_id="owner_mem")
    assert listed["count"] == 1


# --- Workflow Automation ---


def test_workflow_templates_and_create():
    org_id = _seed_org("owner_wf")
    templates = _svc().workflows.list_templates()
    assert len(templates["templates"]) >= 3
    created = _svc().workflows.create(
        {
            "organizationId": org_id,
            "name": "Full Production",
            "templateSlug": "full-production",
        },
        actor_id="owner_wf",
    )
    assert created["workflow"]["mode"] == "sequential"
    assert len(created["workflow"]["steps"]) >= 5


def test_workflow_manual_run():
    org_id = _seed_org("owner_run")
    wf = _svc().workflows.create(
        {
            "organizationId": org_id,
            "name": "Audio Pass",
            "templateSlug": "audio-pass",
            "trigger": "manual",
        },
        actor_id="owner_run",
    )["workflow"]
    result = _svc().execution.run(
        {"workflowId": wf["id"], "context": {"brief": "epic score"}},
        actor_id="owner_run",
    )
    assert result["ok"] is True
    assert result["execution"]["status"] == "completed"
    assert len(result["execution"]["results"]) == 3


def test_parallel_workflow():
    org_id = _seed_org("owner_par")
    wf = _svc().workflows.create(
        {
            "organizationId": org_id,
            "name": "Parallel Story",
            "templateSlug": "script-to-storyboard",
        },
        actor_id="owner_par",
    )["workflow"]
    assert wf["mode"] == "parallel"
    result = _svc().execution.run({"workflowId": wf["id"]}, actor_id="owner_par")
    assert result["execution"]["status"] == "completed"
    assert len(result["execution"]["results"]) == 3


def test_conditional_workflow():
    org_id = _seed_org("owner_cond")
    wf = _svc().workflows.create(
        {
            "organizationId": org_id,
            "name": "Conditional QA",
            "mode": "conditional",
            "conditions": {"requireContextKey": "approved"},
            "steps": [{"agentType": "qa", "action": "check"}],
        },
        actor_id="owner_cond",
    )["workflow"]
    fail = _svc().execution.run(
        {"workflowId": wf["id"], "maxRetries": 0},
        actor_id="owner_cond",
    )
    assert fail["ok"] is False
    ok = _svc().execution.run(
        {"workflowId": wf["id"], "context": {"approved": True}},
        actor_id="owner_cond",
    )
    assert ok["ok"] is True


def test_workflow_history():
    org_id = _seed_org("owner_hist")
    wf = _svc().workflows.create(
        {
            "organizationId": org_id,
            "name": "History WF",
            "steps": [{"agentType": "prompt_engineer"}],
        },
        actor_id="owner_hist",
    )["workflow"]
    _svc().execution.run({"workflowId": wf["id"]}, actor_id="owner_hist")
    history = _svc().execution.history(
        actor_id="owner_hist", organization_id=org_id
    )
    assert history["count"] >= 1
    assert any(h["eventType"] == "completed" for h in history["history"])


# --- Recovery ---


def test_failure_recovery_retry():
    org_id = _seed_org("owner_rec")
    wf = _svc().workflows.create(
        {
            "organizationId": org_id,
            "name": "Retry WF",
            "steps": [
                {"agentType": "script_writer"},
                {"agentType": "qa"},
            ],
        },
        actor_id="owner_rec",
    )["workflow"]
    result = _svc().execution.run(
        {"workflowId": wf["id"], "forceFailStep": 0, "maxRetries": 2},
        actor_id="owner_rec",
    )
    assert result["ok"] is True
    assert result["execution"]["status"] == "completed"
    assert result["execution"]["retries"] >= 1


# --- Orchestrator ---


def test_multi_agent_collaboration():
    org_id = _seed_org("owner_col")
    a = _create_agent(org_id, "owner_col", name="Script", agentType="script_writer")["agent"]
    b = _create_agent(org_id, "owner_col", name="Board", agentType="storyboard")["agent"]
    result = _svc().orchestrator.collaborate(
        {
            "organizationId": org_id,
            "agentIds": [a["id"], b["id"]],
            "task": "Opening sequence",
        },
        actor_id="owner_col",
    )
    assert len(result["delegations"]) == 2
    assert len(result["sharedContextKeys"]) >= 0


# --- Scheduler ---


def test_scheduler_once_and_tick():
    org_id = _seed_org("owner_sch")
    wf = _svc().workflows.create(
        {
            "organizationId": org_id,
            "name": "Scheduled WF",
            "steps": [{"agentType": "director"}],
        },
        actor_id="owner_sch",
    )["workflow"]
    job = _svc().scheduler.schedule(
        {
            "organizationId": org_id,
            "workflowId": wf["id"],
            "kind": "once",
            "delayMinutes": 0,
            "priority": "high",
        },
        actor_id="owner_sch",
    )["job"]
    assert job["kind"] == "once"
    # Force due
    store = sys.modules["app.services.agent_orchestration.store"]
    stored = store.get_job(job["id"])
    stored.next_run_at = stored.next_run_at - timedelta(minutes=1)
    store.save_job(stored)
    tick = _svc().scheduler.tick(actor_id="owner_sch", organization_id=org_id)
    assert tick["processed"] == 1
    listed = _svc().scheduler.list(actor_id="owner_sch", organization_id=org_id)
    assert listed["jobs"][0]["status"] == "completed"


def test_scheduler_kinds():
    org_id = _seed_org("owner_kinds")
    wf = _svc().workflows.create(
        {
            "organizationId": org_id,
            "name": "Kinds WF",
            "steps": [{"agentType": "qa"}],
        },
        actor_id="owner_kinds",
    )["workflow"]
    for kind in ("daily", "weekly", "monthly", "recurring"):
        job = _svc().scheduler.schedule(
            {
                "organizationId": org_id,
                "workflowId": wf["id"],
                "kind": kind,
            },
            actor_id="owner_kinds",
        )["job"]
        assert job["kind"] == kind
        assert job["nextRunAt"] is not None


# --- Security ---


def test_security_agent_ownership():
    org_id = _seed_org("owner_sec")
    agent = _create_agent(org_id, "owner_sec")["agent"]
    try:
        _svc().agents.update(
            agent["id"], {"name": "Stolen"}, actor_id="editor_1"
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        _svc().agents.delete(agent["id"], actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


def test_security_organization_isolation():
    org_a = _seed_org("owner_oa")
    org_b = _seed_org("owner_ob")
    agent = _create_agent(org_a, "owner_oa")["agent"]
    try:
        _svc().agents.get(agent["id"], actor_id="owner_ob")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        _svc().agents.list(actor_id="owner_ob", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


def test_security_workspace_isolation():
    org_id = _seed_org("owner_ws")
    agent = _create_agent(
        org_id, "owner_ws", name="WS Agent", workspaceId="ws_a", agentType="qa"
    )["agent"]
    wf = _svc().workflows.create(
        {
            "organizationId": org_id,
            "name": "WS Workflow",
            "workspaceId": "ws_a",
            "steps": [{"agentId": agent["id"], "agentType": "qa"}],
        },
        actor_id="owner_ws",
    )["workflow"]
    try:
        _svc().execution.run(
            {"workflowId": wf["id"], "workspaceId": "ws_b"},
            actor_id="owner_ws",
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


def test_security_audit_logging():
    org_id = _seed_org("owner_aud")
    audit_store = sys.modules["app.services.enterprise_auth.store"]
    agent = _create_agent(org_id, "owner_aud")["agent"]
    wf = _svc().workflows.create(
        {
            "organizationId": org_id,
            "name": "Audit WF",
            "steps": [{"agentId": agent["id"], "agentType": "director"}],
        },
        actor_id="owner_aud",
    )["workflow"]
    _svc().execution.run({"workflowId": wf["id"]}, actor_id="owner_aud")
    events = audit_store.list_audits(limit=500)
    actions = {e.event_type for e in events}
    assert "agent_orchestration.agent_created" in actions
    assert "agent_orchestration.workflow_created" in actions
    assert "agent_orchestration.workflow_completed" in actions


# --- Integration ---


def test_full_orchestration_workflow():
    org_id = _seed_org("owner_full")
    svc = _svc()
    director = _create_agent(org_id, "owner_full", agentType="director")["agent"]
    qa = _create_agent(org_id, "owner_full", name="QA Bot", agentType="qa")["agent"]
    wf = svc.workflows.create(
        {
            "organizationId": org_id,
            "name": "Flagship Pipeline",
            "templateSlug": "full-production",
        },
        actor_id="owner_full",
    )["workflow"]
    run = svc.execution.run(
        {"workflowId": wf["id"], "context": {"title": "Neon Dawn"}, "priority": "high"},
        actor_id="owner_full",
    )
    assert run["execution"]["status"] == "completed"
    collab = svc.orchestrator.collaborate(
        {
            "organizationId": org_id,
            "agentIds": [director["id"], qa["id"]],
            "task": "Final review",
        },
        actor_id="owner_full",
    )
    assert len(collab["delegations"]) == 2
    job = svc.scheduler.schedule(
        {
            "organizationId": org_id,
            "workflowId": wf["id"],
            "kind": "daily",
            "priority": "normal",
        },
        actor_id="owner_full",
    )["job"]
    assert job["kind"] == "daily"
    history = svc.execution.history(actor_id="owner_full", organization_id=org_id)
    assert history["count"] >= 1
    status = svc.status()
    assert status["stats"]["workflows"] >= 1
    assert status["stats"]["executions"] >= 1


# --- Performance ---


def test_performance_bulk_runs():
    org_id = _seed_org("owner_perf")
    wf = _svc().workflows.create(
        {
            "organizationId": org_id,
            "name": "Perf WF",
            "steps": [
                {"agentType": "prompt_engineer"},
                {"agentType": "qa"},
            ],
        },
        actor_id="owner_perf",
    )["workflow"]
    start = time.perf_counter()
    for _ in range(50):
        result = _svc().execution.run({"workflowId": wf["id"]}, actor_id="owner_perf")
        assert result["execution"]["status"] == "completed"
    elapsed = time.perf_counter() - start
    assert elapsed < 10.0
    metrics = _svc().status()["stats"]
    assert metrics["executions"] >= 50
    assert metrics["avgLatencyMs"] >= 0
