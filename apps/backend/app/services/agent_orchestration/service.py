"""Enterprise AI Agents, Automation Workflows & Orchestration Engine — Phase 9 Sprint 7."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.agent_orchestration import store
from app.services.agent_orchestration.catalog import (
    AGENT_STATUSES,
    AGENT_TYPES,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MEMORY_LIMIT,
    JOB_PRIORITIES,
    SCHEDULE_KINDS,
    TASK_MODES,
    WORKFLOW_TRIGGERS,
    agent_capabilities,
    default_workflow_templates,
    slugify,
)
from app.services.agent_orchestration.models import (
    AgentEventRecord,
    AgentMemoryRecord,
    AgentWorkflowRecord,
    AIAgentRecord,
    ExecutionHistoryRecord,
    ScheduledJobRecord,
    WorkflowExecutionRecord,
    WorkflowTemplateRecord,
    new_id,
)
from app.services.agent_orchestration.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validation():
    from app.services.multi_tenant.validation import ValidationError, require_non_empty

    return ValidationError, require_non_empty


def _auth_errors():
    from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError

    return ForbiddenError, NotFoundError


def _require_access(**kwargs: Any) -> None:
    from app.services.enterprise_auth.middleware import require_access

    require_access(**kwargs)


def _audit(action: str, actor_id: str, detail: str | None = None, **meta: Any) -> None:
    from app.services.enterprise_auth.audit import log_auth_event

    log_auth_event(
        action, actor_id=actor_id, success=True, detail=detail or action, metadata=meta
    )


def _require_member(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id, organization_id=organization_id, permission="org.read"
    )


def _emit_agent_event(
    *,
    organization_id: str,
    agent_id: str,
    event_type: str,
    actor: str = "",
    payload: dict[str, Any] | None = None,
) -> None:
    store.save_event(
        AgentEventRecord(
            id=new_id("aev_"),
            organization_id=organization_id,
            agent_id=agent_id,
            event_type=event_type,
            payload=dict(payload or {}),
            actor_user_id=actor,
        )
    )


def _history(
    *,
    organization_id: str,
    execution_id: str,
    workflow_id: str,
    event_type: str,
    message: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    store.save_history(
        ExecutionHistoryRecord(
            id=new_id("exh_"),
            organization_id=organization_id,
            execution_id=execution_id,
            workflow_id=workflow_id,
            event_type=event_type,
            message=message,
            metadata=dict(metadata or {}),
        )
    )


class AgentMemoryEngine:
    """Per-agent memory with organization/workspace isolation."""

    def remember(
        self,
        agent: AIAgentRecord,
        key: str,
        value: dict[str, Any],
        *,
        execution_id: str | None = None,
    ) -> AgentMemoryRecord:
        ValidationError, require_non_empty = _validation()
        key = str(require_non_empty(key, "key"))
        existing = store.get_memory(agent.id, key)
        if existing is None and store.count_memory(agent.id) >= DEFAULT_MEMORY_LIMIT:
            items = store.list_memory(agent.id, limit=DEFAULT_MEMORY_LIMIT)
            if items:
                store.delete_memory(items[-1].id)
        if existing:
            existing.value = dict(value)
            existing.execution_id = execution_id
            existing.updated_at = _now()
            store.save_memory(existing)
            return existing
        record = AgentMemoryRecord(
            id=new_id("mem_"),
            organization_id=agent.organization_id,
            agent_id=agent.id,
            workspace_id=agent.workspace_id,
            key=key,
            value=dict(value),
            execution_id=execution_id,
        )
        store.save_memory(record)
        return record

    def recall(self, agent_id: str, key: str, *, actor_id: str) -> dict[str, Any]:
        _, NotFoundError = _auth_errors()
        agent = store.get_agent(agent_id)
        if agent is None:
            raise NotFoundError("agent not found")
        _require_member(actor_id=actor_id, organization_id=agent.organization_id)
        mem = store.get_memory(agent_id, key)
        if mem is None:
            raise NotFoundError("memory key not found")
        return {"ok": True, "memory": mem.to_dict()}

    def list(self, agent_id: str, *, actor_id: str) -> dict[str, Any]:
        _, NotFoundError = _auth_errors()
        agent = store.get_agent(agent_id)
        if agent is None:
            raise NotFoundError("agent not found")
        _require_member(actor_id=actor_id, organization_id=agent.organization_id)
        items = store.list_memory(agent_id)
        return {"ok": True, "count": len(items), "memory": [m.to_dict() for m in items]}

    def shared_context(self, agent_ids: list[str]) -> dict[str, Any]:
        context: dict[str, Any] = {}
        for aid in agent_ids:
            for mem in store.list_memory(aid, limit=20):
                context[f"{aid}:{mem.key}"] = mem.value
        return context


class AIAgentEngine:
    """AI agent CRUD, isolation, and capability management."""

    def __init__(self, memory: AgentMemoryEngine) -> None:
        self.memory = memory

    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            name = str(require_non_empty(payload.get("name"), "name"))
            agent_type = str(payload.get("agentType") or payload.get("type") or "custom")
            if agent_type not in AGENT_TYPES:
                raise ValidationError(f"unknown agent type: {agent_type}")
            ws_id = payload.get("workspaceId")
            workspace_id = str(ws_id) if ws_id else None
            caps = payload.get("capabilities") or agent_capabilities(agent_type)
            agent = AIAgentRecord(
                id=new_id("agt_"),
                organization_id=org_id,
                workspace_id=workspace_id,
                owner_user_id=actor_id,
                name=name,
                slug=slugify(name),
                agent_type=agent_type,
                description=str(payload.get("description") or ""),
                capabilities=[str(c) for c in caps],
                config=dict(payload.get("config") or {}),
            )
            store.save_agent(agent)
            _emit_agent_event(
                organization_id=org_id,
                agent_id=agent.id,
                event_type="created",
                actor=actor_id,
            )
            _audit("agent_orchestration.agent_created", actor_id, agent.name)
            return {"ok": True, "agent": agent.to_dict()}

    def get(self, agent_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            agent = self._get_for_read(agent_id, actor_id=actor_id)
            return {"ok": True, "agent": agent.to_dict()}

    def list(
        self,
        *,
        actor_id: str,
        organization_id: str,
        workspace_id: str | None = None,
        agent_type: str | None = None,
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            items = store.list_agents(
                organization_id=organization_id,
                workspace_id=workspace_id,
                agent_type=agent_type,
            )
            items.sort(key=lambda a: a.created_at, reverse=True)
            return {
                "ok": True,
                "count": len(items),
                "agents": [a.to_dict() for a in items],
            }

    def update(
        self, agent_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            agent = self._get_for_write(agent_id, actor_id=actor_id)
            if "name" in payload and payload["name"] is not None:
                agent.name = str(payload["name"])
                agent.slug = slugify(agent.name)
            if "description" in payload and payload["description"] is not None:
                agent.description = str(payload["description"])
            if "status" in payload and payload["status"] is not None:
                status = str(payload["status"])
                if status not in AGENT_STATUSES:
                    raise ValidationError(f"unknown status: {status}")
                agent.status = status
            if "config" in payload and payload["config"] is not None:
                agent.config = dict(payload["config"])
            agent.updated_at = _now()
            store.save_agent(agent)
            _audit("agent_orchestration.agent_updated", actor_id, agent.name)
            return {"ok": True, "agent": agent.to_dict()}

    def delete(self, agent_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            agent = self._get_for_write(agent_id, actor_id=actor_id)
            agent.status = "archived"
            agent.updated_at = _now()
            store.save_agent(agent)
            _emit_agent_event(
                organization_id=agent.organization_id,
                agent_id=agent.id,
                event_type="archived",
                actor=actor_id,
            )
            _audit("agent_orchestration.agent_deleted", actor_id, agent.name)
            return {"ok": True, "agentId": agent_id, "status": "archived"}

    def status_summary(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            agents = store.list_agents(organization_id=organization_id)
            by_type: dict[str, int] = {}
            by_status: dict[str, int] = {}
            for a in agents:
                by_type[a.agent_type] = by_type.get(a.agent_type, 0) + 1
                by_status[a.status] = by_status.get(a.status, 0) + 1
            return {
                "ok": True,
                "organizationId": organization_id,
                "totalAgents": len(agents),
                "byType": by_type,
                "byStatus": by_status,
                "queueDepth": store.queue_depth(),
                "engines": {
                    "aiAgent": "ready",
                    "workflowAutomation": "ready",
                    "multiAgentOrchestrator": "ready",
                    "agentMemory": "ready",
                    "agentScheduler": "ready",
                    "workflowExecution": "ready",
                },
            }

    def _get_for_read(self, agent_id: str, *, actor_id: str) -> AIAgentRecord:
        _, NotFoundError = _auth_errors()
        agent = store.get_agent(agent_id)
        if agent is None or agent.status == "archived":
            raise NotFoundError("agent not found")
        _require_member(actor_id=actor_id, organization_id=agent.organization_id)
        return agent

    def _get_for_write(self, agent_id: str, *, actor_id: str) -> AIAgentRecord:
        ForbiddenError, NotFoundError = _auth_errors()
        agent = store.get_agent(agent_id)
        if agent is None or agent.status == "archived":
            raise NotFoundError("agent not found")
        if agent.owner_user_id != actor_id:
            try:
                _require_access(
                    user_id=actor_id,
                    organization_id=agent.organization_id,
                    permission="org.update",
                )
            except Exception:
                raise ForbiddenError("only the agent owner can perform this action")
        return agent


class WorkflowAutomationEngine:
    """Workflow builder, templates, and trigger configuration."""

    def ensure_templates(self) -> None:
        if store.list_templates():
            return
        for tpl in default_workflow_templates():
            steps = [
                {
                    "order": i,
                    "agentType": at,
                    "action": "execute",
                    "mode": tpl["mode"],
                }
                for i, at in enumerate(tpl["agentTypes"])
            ]
            store.save_template(
                WorkflowTemplateRecord(
                    id=new_id("wft_"),
                    slug=tpl["slug"],
                    name=tpl["name"],
                    description=tpl["description"],
                    mode=tpl["mode"],
                    agent_types=list(tpl["agentTypes"]),
                    steps=steps,
                )
            )

    def list_templates(self) -> dict[str, Any]:
        self.ensure_templates()
        return {
            "ok": True,
            "templates": [t.to_dict() for t in store.list_templates()],
        }

    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            self.ensure_templates()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            name = str(require_non_empty(payload.get("name"), "name"))
            trigger = str(payload.get("trigger") or "manual")
            if trigger not in WORKFLOW_TRIGGERS:
                raise ValidationError(f"unknown trigger: {trigger}")
            mode = str(payload.get("mode") or "sequential")
            if mode not in TASK_MODES:
                raise ValidationError(f"unknown mode: {mode}")
            ws_id = payload.get("workspaceId")
            workspace_id = str(ws_id) if ws_id else None
            template_id = None
            steps = list(payload.get("steps") or [])
            template_slug = payload.get("templateSlug") or payload.get("template")
            if template_slug:
                tpl = store.get_template_by_slug(str(template_slug))
                if tpl is None:
                    raise ValidationError(f"unknown template: {template_slug}")
                template_id = tpl.id
                if not steps:
                    steps = list(tpl.steps)
                mode = tpl.mode
            if not steps:
                raise ValidationError("workflow steps are required")
            for step in steps:
                agent_type = step.get("agentType") or step.get("agent_type")
                if agent_type and agent_type not in AGENT_TYPES:
                    raise ValidationError(f"unknown agent type in step: {agent_type}")
                agent_id = step.get("agentId")
                if agent_id:
                    agent = store.get_agent(str(agent_id))
                    if agent is None or agent.organization_id != org_id:
                        raise ValidationError("step agent not found in organization")
                    if workspace_id and agent.workspace_id and agent.workspace_id != workspace_id:
                        raise ValidationError("workspace isolation violation for step agent")
            workflow = AgentWorkflowRecord(
                id=new_id("wf_"),
                organization_id=org_id,
                workspace_id=workspace_id,
                owner_user_id=actor_id,
                name=name,
                slug=slugify(name),
                description=str(payload.get("description") or ""),
                trigger=trigger,
                mode=mode,
                steps=steps,
                conditions=dict(payload.get("conditions") or {}),
                template_id=template_id,
            )
            store.save_workflow(workflow)
            _audit("agent_orchestration.workflow_created", actor_id, workflow.name)
            return {"ok": True, "workflow": workflow.to_dict()}

    def get(self, workflow_id: str, *, actor_id: str) -> AgentWorkflowRecord:
        _, NotFoundError = _auth_errors()
        workflow = store.get_workflow(workflow_id)
        if workflow is None or workflow.status == "archived":
            raise NotFoundError("workflow not found")
        _require_member(
            actor_id=actor_id, organization_id=workflow.organization_id
        )
        return workflow


class WorkflowExecutionEngine:
    """Execute workflows with retry, failure recovery, and history."""

    def __init__(
        self,
        memory: AgentMemoryEngine,
        agents: AIAgentEngine,
    ) -> None:
        self.memory = memory
        self.agents = agents

    def run(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            workflow_id = str(require_non_empty(payload.get("workflowId"), "workflowId"))
            workflow = store.get_workflow(workflow_id)
            _, NotFoundError = _auth_errors()
            if workflow is None or workflow.status != "active":
                raise NotFoundError("workflow not found")
            _require_member(
                actor_id=actor_id, organization_id=workflow.organization_id
            )
            if workflow.workspace_id and payload.get("workspaceId"):
                if str(payload["workspaceId"]) != workflow.workspace_id:
                    ForbiddenError, _ = _auth_errors()
                    raise ForbiddenError("workspace isolation violation")
            priority = str(payload.get("priority") or "normal")
            if priority not in JOB_PRIORITIES:
                raise ValidationError(f"unknown priority: {priority}")
            max_retries = int(payload.get("maxRetries") or DEFAULT_MAX_RETRIES)
            force_fail_step = payload.get("forceFailStep")
            execution = WorkflowExecutionRecord(
                id=new_id("wex_"),
                organization_id=workflow.organization_id,
                workspace_id=workflow.workspace_id,
                workflow_id=workflow.id,
                status="queued",
                trigger=str(payload.get("trigger") or workflow.trigger or "manual"),
                started_by=actor_id,
                context=dict(payload.get("context") or {}),
                max_retries=max_retries,
                priority=priority,
            )
            store.save_execution(execution)
            store.enqueue(execution.id, priority=priority)
            _history(
                organization_id=workflow.organization_id,
                execution_id=execution.id,
                workflow_id=workflow.id,
                event_type="queued",
                message="Execution queued",
            )
            return self._process(
                execution,
                workflow,
                force_fail_step=force_fail_step,
            )

    def _process(
        self,
        execution: WorkflowExecutionRecord,
        workflow: AgentWorkflowRecord,
        *,
        force_fail_step: Any = None,
    ) -> dict[str, Any]:
        dequeued = store.dequeue()
        if dequeued != execution.id and dequeued is not None:
            store.enqueue(dequeued, priority="normal")

        attempt = 0
        while attempt <= execution.max_retries:
            execution.status = "retrying" if attempt > 0 else "running"
            execution.started_at = execution.started_at or _now()
            execution.retries = attempt
            store.save_execution(execution)
            _history(
                organization_id=execution.organization_id,
                execution_id=execution.id,
                workflow_id=workflow.id,
                event_type="started" if attempt == 0 else "retry",
                message=f"Attempt {attempt + 1}",
                metadata={"attempt": attempt + 1},
            )
            try:
                results = self._execute_steps(
                    workflow,
                    execution,
                    force_fail_step=force_fail_step if attempt == 0 else None,
                )
                execution.results = results
                execution.status = "completed"
                execution.completed_at = _now()
                execution.error = ""
                store.save_execution(execution)
                _history(
                    organization_id=execution.organization_id,
                    execution_id=execution.id,
                    workflow_id=workflow.id,
                    event_type="completed",
                    message="Execution completed",
                )
                _audit(
                    "agent_orchestration.workflow_completed",
                    execution.started_by,
                    workflow.name,
                )
                return {"ok": True, "execution": execution.to_dict()}
            except Exception as exc:
                execution.error = str(exc)
                execution.status = "failed"
                store.save_execution(execution)
                _history(
                    organization_id=execution.organization_id,
                    execution_id=execution.id,
                    workflow_id=workflow.id,
                    event_type="failed",
                    message=str(exc),
                    metadata={"attempt": attempt + 1},
                )
                if attempt >= execution.max_retries:
                    break
                attempt += 1
                # Failure recovery: clear force fail and retry
                force_fail_step = None

        _audit(
            "agent_orchestration.workflow_failed",
            execution.started_by,
            workflow.name,
        )
        return {"ok": False, "execution": execution.to_dict()}

    def _execute_steps(
        self,
        workflow: AgentWorkflowRecord,
        execution: WorkflowExecutionRecord,
        *,
        force_fail_step: Any = None,
    ) -> list[dict[str, Any]]:
        ValidationError, _ = _validation()
        results: list[dict[str, Any]] = []
        shared: dict[str, Any] = dict(execution.context)

        # Conditional gate
        if workflow.mode == "conditional" and workflow.conditions:
            required = workflow.conditions.get("requireContextKey")
            if required and required not in shared:
                raise ValidationError(f"missing required context key: {required}")

        steps = list(workflow.steps)
        if workflow.mode == "parallel":
            # Simulate parallel by executing all then aggregating
            for idx, step in enumerate(steps):
                results.append(
                    self._run_step(
                        step,
                        idx,
                        workflow,
                        execution,
                        shared,
                        force_fail=(force_fail_step == idx),
                    )
                )
        else:
            for idx, step in enumerate(steps):
                result = self._run_step(
                    step,
                    idx,
                    workflow,
                    execution,
                    shared,
                    force_fail=(force_fail_step == idx),
                )
                results.append(result)
                shared[f"step_{idx}"] = result.get("output")

        execution.context = shared
        return results

    def _run_step(
        self,
        step: dict[str, Any],
        index: int,
        workflow: AgentWorkflowRecord,
        execution: WorkflowExecutionRecord,
        shared: dict[str, Any],
        *,
        force_fail: bool = False,
    ) -> dict[str, Any]:
        ValidationError, _ = _validation()
        if force_fail:
            raise ValidationError(f"forced failure at step {index}")

        agent_type = str(step.get("agentType") or step.get("agent_type") or "custom")
        agent_id = step.get("agentId")
        agent: AIAgentRecord | None = None
        if agent_id:
            agent = store.get_agent(str(agent_id))
            if agent is None or agent.organization_id != workflow.organization_id:
                raise ValidationError("agent isolation violation")
            if agent.status != "active":
                raise ValidationError(f"agent {agent.id} is not active")
        else:
            # Resolve or auto-provision ephemeral agent of required type in org
            matches = [
                a
                for a in store.list_agents(
                    organization_id=workflow.organization_id,
                    agent_type=agent_type,
                    status="active",
                )
                if not workflow.workspace_id
                or not a.workspace_id
                or a.workspace_id == workflow.workspace_id
            ]
            if matches:
                agent = matches[0]
            else:
                created = self.agents.create(
                    {
                        "organizationId": workflow.organization_id,
                        "workspaceId": workflow.workspace_id,
                        "name": f"{agent_type.replace('_', ' ').title()} Auto",
                        "agentType": agent_type,
                    },
                    actor_id=execution.started_by or workflow.owner_user_id,
                )
                agent = store.get_agent(created["agent"]["id"])

        assert agent is not None
        output = {
            "agentId": agent.id,
            "agentType": agent.agent_type,
            "action": step.get("action") or "execute",
            "summary": f"{agent.agent_type} completed step {index}",
            "sharedKeys": list(shared.keys())[:10],
        }
        self.memory.remember(
            agent,
            key=f"exec:{execution.id}:step:{index}",
            value={"output": output, "shared": shared},
            execution_id=execution.id,
        )
        _emit_agent_event(
            organization_id=agent.organization_id,
            agent_id=agent.id,
            event_type="task_completed",
            actor=execution.started_by,
            payload={"executionId": execution.id, "step": index},
        )
        return {
            "step": index,
            "agentId": agent.id,
            "agentType": agent.agent_type,
            "status": "completed",
            "output": output,
        }

    def history(
        self,
        *,
        actor_id: str,
        organization_id: str,
        workflow_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            executions = store.list_executions(
                organization_id=organization_id,
                workflow_id=workflow_id,
                limit=limit,
            )
            history = store.list_history(
                organization_id=organization_id, limit=limit
            )
            return {
                "ok": True,
                "count": len(executions),
                "executions": [e.to_dict() for e in executions],
                "history": [h.to_dict() for h in history],
            }


class MultiAgentOrchestrator:
    """Multi-agent collaboration, delegation, and context sharing."""

    def __init__(self, memory: AgentMemoryEngine, execution: WorkflowExecutionEngine) -> None:
        self.memory = memory
        self.execution = execution

    def collaborate(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            agent_ids = [str(a) for a in (payload.get("agentIds") or [])]
            if len(agent_ids) < 2:
                raise ValidationError("at least two agents required for collaboration")
            agents: list[AIAgentRecord] = []
            for aid in agent_ids:
                agent = store.get_agent(aid)
                if agent is None or agent.organization_id != org_id:
                    ForbiddenError, _ = _auth_errors()
                    raise ForbiddenError("agent isolation violation")
                if agent.status != "active":
                    raise ValidationError(f"agent {aid} is not active")
                agents.append(agent)
            task = str(require_non_empty(payload.get("task"), "task"))
            shared = self.memory.shared_context(agent_ids)
            delegations = []
            for agent in agents:
                result = {
                    "agentId": agent.id,
                    "agentType": agent.agent_type,
                    "task": task,
                    "contribution": f"{agent.agent_type} contributed to: {task}",
                }
                self.memory.remember(
                    agent,
                    key=f"collab:{slugify(task)}",
                    value=result,
                )
                delegations.append(result)
            return {
                "ok": True,
                "task": task,
                "agents": [a.id for a in agents],
                "delegations": delegations,
                "sharedContextKeys": list(shared.keys()),
            }


class AgentScheduler:
    """One-time and recurring job scheduling with priorities and retries."""

    def __init__(self, execution: WorkflowExecutionEngine) -> None:
        self.execution = execution

    def schedule(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            workflow_id = str(require_non_empty(payload.get("workflowId"), "workflowId"))
            workflow = store.get_workflow(workflow_id)
            if workflow is None or workflow.organization_id != org_id:
                _, NotFoundError = _auth_errors()
                raise NotFoundError("workflow not found")
            kind = str(payload.get("kind") or "once")
            if kind not in SCHEDULE_KINDS:
                raise ValidationError(f"unknown schedule kind: {kind}")
            priority = str(payload.get("priority") or "normal")
            if priority not in JOB_PRIORITIES:
                raise ValidationError(f"unknown priority: {priority}")
            next_run = _now() + timedelta(minutes=int(payload.get("delayMinutes") or 0))
            if kind == "daily":
                next_run = _now() + timedelta(days=1)
            elif kind == "weekly":
                next_run = _now() + timedelta(weeks=1)
            elif kind == "monthly":
                next_run = _now() + timedelta(days=30)
            elif kind == "recurring":
                next_run = _now() + timedelta(hours=int(payload.get("intervalHours") or 1))
            job = ScheduledJobRecord(
                id=new_id("job_"),
                organization_id=org_id,
                workspace_id=workflow.workspace_id,
                workflow_id=workflow_id,
                kind=kind,
                cron=str(payload.get("cron") or ""),
                priority=priority,
                next_run_at=next_run,
                max_retries=int(payload.get("maxRetries") or DEFAULT_MAX_RETRIES),
                created_by=actor_id,
            )
            store.save_job(job)
            _audit("agent_orchestration.job_scheduled", actor_id, job.id)
            return {"ok": True, "job": job.to_dict()}

    def list(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            jobs = store.list_jobs(organization_id=organization_id)
            return {"ok": True, "count": len(jobs), "jobs": [j.to_dict() for j in jobs]}

    def tick(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        """Process due jobs (simulation clock tick)."""
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            due = [
                j
                for j in store.list_jobs(organization_id=organization_id, status="scheduled")
                if j.next_run_at and j.next_run_at <= _now()
            ]
            # Priority ordering
            order = {p: i for i, p in enumerate(JOB_PRIORITIES)}
            due.sort(key=lambda j: order.get(j.priority, 1))
            ran = []
            for job in due:
                result = self.execution.run(
                    {
                        "workflowId": job.workflow_id,
                        "trigger": "schedule",
                        "priority": job.priority,
                        "maxRetries": job.max_retries,
                    },
                    actor_id=actor_id,
                )
                job.last_run_at = _now()
                if job.kind == "once":
                    job.status = "completed"
                else:
                    # Advance next run
                    if job.kind == "daily":
                        job.next_run_at = _now() + timedelta(days=1)
                    elif job.kind == "weekly":
                        job.next_run_at = _now() + timedelta(weeks=1)
                    elif job.kind == "monthly":
                        job.next_run_at = _now() + timedelta(days=30)
                    else:
                        job.next_run_at = _now() + timedelta(hours=1)
                job.updated_at = _now()
                store.save_job(job)
                ran.append({"jobId": job.id, "execution": result.get("execution")})
            return {"ok": True, "processed": len(ran), "results": ran}


class AgentOrchestrationFacade:
    """Facade combining all agent orchestration engines."""

    def __init__(self) -> None:
        self.memory = AgentMemoryEngine()
        self.agents = AIAgentEngine(self.memory)
        self.workflows = WorkflowAutomationEngine()
        self.execution = WorkflowExecutionEngine(self.memory, self.agents)
        self.orchestrator = MultiAgentOrchestrator(self.memory, self.execution)
        self.scheduler = AgentScheduler(self.execution)
        self.workflows.ensure_templates()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "aiAgent": "ready",
                "workflowAutomation": "ready",
                "multiAgentOrchestrator": "ready",
                "agentMemory": "ready",
                "agentScheduler": "ready",
                "workflowExecution": "ready",
            },
            "agentTypes": list(AGENT_TYPES),
            "scheduleKinds": list(SCHEDULE_KINDS),
            "stats": store.metrics(),
        }


_service: AgentOrchestrationFacade | None = None


def get_agent_orchestration_service() -> AgentOrchestrationFacade:
    global _service
    if _service is None:
        _service = AgentOrchestrationFacade()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    _service = None


get_engine = get_agent_orchestration_service
