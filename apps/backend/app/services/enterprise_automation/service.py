"""Enterprise Automation, Integrations & Event-Driven Platform — Phase 9 Sprint 8."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.enterprise_automation import store
from app.services.enterprise_automation.catalog import (
    AUTOMATION_MODES,
    AUTOMATION_STATUSES,
    EVENT_TYPES,
    INTEGRATION_PROVIDERS,
    SCHEDULE_KINDS,
    category_for_event,
    generate_credentials_ref,
    sign_webhook_payload,
    slugify,
    verify_webhook_signature,
)
from app.services.enterprise_automation.models import (
    AutomationExecutionRecord,
    AutomationHistoryRecord,
    AutomationRuleRecord,
    EventBusRecord,
    EventLogRecord,
    EventSubscriptionRecord,
    IntegrationConnectionRecord,
    ScheduledAutomationRecord,
    new_id,
)
from app.services.enterprise_automation.version import (
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


def _history(
    *,
    organization_id: str,
    rule_id: str,
    event_type: str,
    message: str = "",
    execution_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    store.save_history(
        AutomationHistoryRecord(
            id=new_id("auh_"),
            organization_id=organization_id,
            rule_id=rule_id,
            execution_id=execution_id,
            event_type=event_type,
            message=message,
            metadata=dict(metadata or {}),
        )
    )


class EventBusEngine:
    """Publish/subscribe event bus with auth signatures and logging."""

    def publish(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            event_type = str(require_non_empty(payload.get("eventType"), "eventType"))
            if event_type not in EVENT_TYPES and not event_type.startswith("custom."):
                raise ValidationError(f"unknown event type: {event_type}")
            ws_id = payload.get("workspaceId")
            workspace_id = str(ws_id) if ws_id else None
            body = dict(payload.get("payload") or {})
            canonical = json.dumps(
                {"eventType": event_type, "organizationId": org_id, "payload": body},
                sort_keys=True,
                separators=(",", ":"),
            )
            provided_sig = str(payload.get("signature") or "")
            secret = str(payload.get("signingSecret") or "")
            if provided_sig and not verify_webhook_signature(
                canonical, provided_sig, secret
            ):
                raise ValidationError("event signature validation failed")
            signature = provided_sig or sign_webhook_payload(canonical, secret)
            event = EventBusRecord(
                id=new_id("evt_"),
                organization_id=org_id,
                workspace_id=workspace_id,
                event_type=event_type,
                category=category_for_event(event_type),
                payload=body,
                actor_user_id=actor_id,
                signature=signature,
            )
            store.save_event(event)
            store.save_event_log(
                EventLogRecord(
                    id=new_id("elog_"),
                    event_id=event.id,
                    organization_id=org_id,
                    action="published",
                    message=f"Published {event_type}",
                    success=True,
                )
            )
            _audit("enterprise_automation.event_published", actor_id, event_type)
            return {"ok": True, "event": event.to_dict()}

    def history(
        self,
        *,
        actor_id: str,
        organization_id: str,
        event_type: str | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            events = store.list_events(
                organization_id=organization_id,
                event_type=event_type,
                category=category,
                limit=limit,
            )
            logs = store.list_event_logs(
                organization_id=organization_id, limit=limit
            )
            return {
                "ok": True,
                "count": len(events),
                "events": [e.to_dict() for e in events],
                "logs": [l.to_dict() for l in logs],
            }

    def authorize_event(
        self, event: EventBusRecord, *, actor_id: str, organization_id: str
    ) -> None:
        ForbiddenError, _ = _auth_errors()
        if event.organization_id != organization_id:
            raise ForbiddenError("event organization isolation violation")
        _require_member(actor_id=actor_id, organization_id=organization_id)


class IntegrationHub:
    """Third-party integration connections for automation delivery."""

    def connect(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            provider = str(require_non_empty(payload.get("provider"), "provider"))
            if provider not in INTEGRATION_PROVIDERS:
                raise ValidationError(f"unknown integration provider: {provider}")
            credentials_ref = str(
                payload.get("credentialsRef")
                or payload.get("accessTokenRef")
                or generate_credentials_ref(provider)
            )
            if not credentials_ref:
                raise ValidationError("credentialsRef is required")
            ws_id = payload.get("workspaceId")
            workspace_id = str(ws_id) if ws_id else None
            webhook_secret = str(payload.get("webhookSecret") or secrets_token())
            conn = IntegrationConnectionRecord(
                id=new_id("ain_"),
                organization_id=org_id,
                workspace_id=workspace_id,
                provider=provider,
                status="connected",
                display_name=str(
                    payload.get("displayName")
                    or provider.replace("_", " ").title()
                ),
                credentials_ref=credentials_ref,
                webhook_secret=webhook_secret,
                metadata=dict(payload.get("metadata") or {}),
                connected_by=actor_id,
            )
            store.save_integration(conn)
            _audit("enterprise_automation.integration_connected", actor_id, provider)
            return {
                "ok": True,
                "connection": conn.to_dict(),
                "webhookSecret": webhook_secret if provider == "webhook" else None,
            }

    def status(
        self, *, actor_id: str, organization_id: str, workspace_id: str | None = None
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            items = store.list_integrations(
                organization_id=organization_id, workspace_id=workspace_id
            )
            by_provider: dict[str, int] = {}
            for c in items:
                by_provider[c.provider] = by_provider.get(c.provider, 0) + 1
            return {
                "ok": True,
                "organizationId": organization_id,
                "connected": len(items),
                "byProvider": by_provider,
                "providers": list(INTEGRATION_PROVIDERS),
                "integrations": [c.to_dict() for c in items],
            }

    def deliver(
        self, connection: IntegrationConnectionRecord, event: EventBusRecord
    ) -> dict[str, Any]:
        payload = json.dumps(event.to_dict(), sort_keys=True)
        sig = sign_webhook_payload(payload, connection.webhook_secret)
        return {
            "provider": connection.provider,
            "connectionId": connection.id,
            "delivered": True,
            "signature": sig,
            "eventId": event.id,
        }


def secrets_token() -> str:
    import secrets

    return secrets.token_urlsafe(24)


class WorkflowTriggerEngine:
    """Match published events to automation rules via subscriptions."""

    def subscribe(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            event_type = str(require_non_empty(payload.get("eventType"), "eventType"))
            rule_id = payload.get("ruleId")
            if rule_id:
                rule = store.get_rule(str(rule_id))
                if rule is None or rule.organization_id != org_id:
                    _, NotFoundError = _auth_errors()
                    raise NotFoundError("automation rule not found")
            ws_id = payload.get("workspaceId")
            sub = EventSubscriptionRecord(
                id=new_id("esub_"),
                organization_id=org_id,
                workspace_id=str(ws_id) if ws_id else None,
                event_type=event_type,
                rule_id=str(rule_id) if rule_id else None,
                target=str(payload.get("target") or "automation"),
            )
            store.save_subscription(sub)
            return {"ok": True, "subscription": sub.to_dict()}

    def matching_rules(self, event: EventBusRecord) -> list[AutomationRuleRecord]:
        rules = store.list_rules(
            organization_id=event.organization_id,
            status="active",
            trigger_event=event.event_type,
        )
        # Also include rules subscribed via EventSubscriptions
        subs = store.list_subscriptions(
            organization_id=event.organization_id, event_type=event.event_type
        )
        rule_ids = {r.id for r in rules}
        for sub in subs:
            if sub.rule_id and sub.rule_id not in rule_ids:
                rule = store.get_rule(sub.rule_id)
                if rule and rule.status == "active":
                    rules.append(rule)
                    rule_ids.add(rule.id)
        if event.workspace_id:
            rules = [
                r
                for r in rules
                if not r.workspace_id or r.workspace_id == event.workspace_id
            ]
        rules.sort(key=lambda r: r.priority)
        return rules


class EventProcessingEngine:
    """Process events: authorize, match triggers, enqueue automations."""

    def __init__(
        self,
        bus: EventBusEngine,
        triggers: WorkflowTriggerEngine,
        automation: "AutomationEngine",
    ) -> None:
        self.bus = bus
        self.triggers = triggers
        self.automation = automation

    def process(self, event_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            _, NotFoundError = _auth_errors()
            event = store.get_event(event_id)
            if event is None:
                raise NotFoundError("event not found")
            self.bus.authorize_event(
                event, actor_id=actor_id, organization_id=event.organization_id
            )
            rules = self.triggers.matching_rules(event)
            executions = []
            for rule in rules:
                result = self.automation.execute_rule(
                    rule, event=event, actor_id=actor_id, trigger="event"
                )
                executions.append(result.get("execution"))
            store.save_event_log(
                EventLogRecord(
                    id=new_id("elog_"),
                    event_id=event.id,
                    organization_id=event.organization_id,
                    action="processed",
                    message=f"Matched {len(rules)} rules",
                    success=True,
                    metadata={"ruleCount": len(rules)},
                )
            )
            return {
                "ok": True,
                "eventId": event_id,
                "matchedRules": len(rules),
                "executions": executions,
            }


class ScheduledAutomationEngine:
    """Schedule automations for future/recurring runs."""

    def __init__(self, automation: "AutomationEngine") -> None:
        self.automation = automation

    def schedule(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            rule_id = str(require_non_empty(payload.get("ruleId"), "ruleId"))
            rule = store.get_rule(rule_id)
            if rule is None or rule.organization_id != org_id:
                _, NotFoundError = _auth_errors()
                raise NotFoundError("automation rule not found")
            kind = str(payload.get("kind") or "once")
            if kind not in SCHEDULE_KINDS:
                raise ValidationError(f"unknown schedule kind: {kind}")
            next_run = _now() + timedelta(minutes=int(payload.get("delayMinutes") or 0))
            if kind == "daily":
                next_run = _now() + timedelta(days=1)
            elif kind == "weekly":
                next_run = _now() + timedelta(weeks=1)
            elif kind == "monthly":
                next_run = _now() + timedelta(days=30)
            elif kind == "recurring":
                next_run = _now() + timedelta(hours=int(payload.get("intervalHours") or 1))
            job = ScheduledAutomationRecord(
                id=new_id("asch_"),
                organization_id=org_id,
                workspace_id=rule.workspace_id,
                rule_id=rule_id,
                kind=kind,
                cron=str(payload.get("cron") or ""),
                next_run_at=next_run,
                created_by=actor_id,
            )
            store.save_schedule(job)
            # Ensure rule mode reflects scheduled automation
            if rule.mode == "event":
                rule.mode = "scheduled"
                rule.updated_at = _now()
                store.save_rule(rule)
            _audit("enterprise_automation.scheduled", actor_id, job.id)
            return {"ok": True, "schedule": job.to_dict()}

    def tick(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            due = [
                j
                for j in store.list_schedules(
                    organization_id=organization_id, status="scheduled"
                )
                if j.next_run_at and j.next_run_at <= _now()
            ]
            results = []
            for job in due:
                rule = store.get_rule(job.rule_id)
                if rule is None:
                    continue
                result = self.automation.execute_rule(
                    rule, event=None, actor_id=actor_id, trigger="schedule"
                )
                job.last_run_at = _now()
                if job.kind == "once":
                    job.status = "completed"
                elif job.kind == "daily":
                    job.next_run_at = _now() + timedelta(days=1)
                elif job.kind == "weekly":
                    job.next_run_at = _now() + timedelta(weeks=1)
                elif job.kind == "monthly":
                    job.next_run_at = _now() + timedelta(days=30)
                else:
                    job.next_run_at = _now() + timedelta(hours=1)
                job.updated_at = _now()
                store.save_schedule(job)
                results.append(result.get("execution"))
            return {"ok": True, "processed": len(results), "executions": results}


class AutomationEngine:
    """Automation rules CRUD and multi-step / queue / conditional execution."""

    def __init__(self, hub: IntegrationHub) -> None:
        self.hub = hub

    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            name = str(require_non_empty(payload.get("name"), "name"))
            mode = str(payload.get("mode") or "event")
            if mode not in AUTOMATION_MODES:
                raise ValidationError(f"unknown automation mode: {mode}")
            actions = list(payload.get("actions") or [])
            if not actions:
                raise ValidationError("actions are required")
            trigger_event = str(payload.get("triggerEvent") or "")
            if mode == "event" and not trigger_event:
                raise ValidationError("triggerEvent is required for event automation")
            if trigger_event and trigger_event not in EVENT_TYPES and not trigger_event.startswith(
                "custom."
            ):
                raise ValidationError(f"unknown trigger event: {trigger_event}")
            ws_id = payload.get("workspaceId")
            workspace_id = str(ws_id) if ws_id else None
            integration_id = payload.get("integrationId")
            if integration_id:
                conn = store.get_integration(str(integration_id))
                if conn is None or conn.organization_id != org_id:
                    raise ValidationError("integration not found in organization")
                if workspace_id and conn.workspace_id and conn.workspace_id != workspace_id:
                    raise ValidationError("workspace isolation violation for integration")
            rule = AutomationRuleRecord(
                id=new_id("arule_"),
                organization_id=org_id,
                workspace_id=workspace_id,
                owner_user_id=actor_id,
                name=name,
                slug=slugify(name),
                mode=mode,
                description=str(payload.get("description") or ""),
                trigger_event=trigger_event,
                conditions=dict(payload.get("conditions") or {}),
                actions=actions,
                integration_id=str(integration_id) if integration_id else None,
                priority=int(payload.get("priority") or 100),
            )
            store.save_rule(rule)
            if trigger_event:
                store.save_subscription(
                    EventSubscriptionRecord(
                        id=new_id("esub_"),
                        organization_id=org_id,
                        workspace_id=workspace_id,
                        event_type=trigger_event,
                        rule_id=rule.id,
                    )
                )
            _history(
                organization_id=org_id,
                rule_id=rule.id,
                event_type="created",
                message=f"Automation {name} created",
            )
            _audit("enterprise_automation.rule_created", actor_id, name)
            return {"ok": True, "automation": rule.to_dict()}

    def list(
        self,
        *,
        actor_id: str,
        organization_id: str,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            items = store.list_rules(
                organization_id=organization_id, workspace_id=workspace_id
            )
            items.sort(key=lambda r: r.created_at, reverse=True)
            return {
                "ok": True,
                "count": len(items),
                "automations": [r.to_dict() for r in items],
            }

    def update(
        self, rule_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            rule = self._get_for_write(rule_id, actor_id=actor_id)
            if "name" in payload and payload["name"] is not None:
                rule.name = str(payload["name"])
                rule.slug = slugify(rule.name)
            if "description" in payload and payload["description"] is not None:
                rule.description = str(payload["description"])
            if "status" in payload and payload["status"] is not None:
                status = str(payload["status"])
                if status not in AUTOMATION_STATUSES:
                    raise ValidationError(f"unknown status: {status}")
                rule.status = status
            if "actions" in payload and payload["actions"] is not None:
                actions = list(payload["actions"])
                if not actions:
                    raise ValidationError("actions cannot be empty")
                rule.actions = actions
            if "conditions" in payload and payload["conditions"] is not None:
                rule.conditions = dict(payload["conditions"])
            if "priority" in payload and payload["priority"] is not None:
                rule.priority = int(payload["priority"])
            rule.updated_at = _now()
            store.save_rule(rule)
            _audit("enterprise_automation.rule_updated", actor_id, rule.name)
            return {"ok": True, "automation": rule.to_dict()}

    def delete(self, rule_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            rule = self._get_for_write(rule_id, actor_id=actor_id)
            rule.status = "archived"
            rule.updated_at = _now()
            store.save_rule(rule)
            _audit("enterprise_automation.rule_deleted", actor_id, rule.name)
            return {"ok": True, "automationId": rule_id, "status": "archived"}

    def execute_rule(
        self,
        rule: AutomationRuleRecord,
        *,
        event: EventBusRecord | None,
        actor_id: str,
        trigger: str = "manual",
    ) -> dict[str, Any]:
        ValidationError, _ = _validation()
        if rule.status != "active":
            raise ValidationError("automation is not active")

        # Conditional gate
        if rule.mode == "conditional" or rule.conditions:
            required = rule.conditions.get("requirePayloadKey")
            payload = (event.payload if event else {}) or {}
            if required and required not in payload:
                execution = AutomationExecutionRecord(
                    id=new_id("aex_"),
                    organization_id=rule.organization_id,
                    workspace_id=rule.workspace_id,
                    rule_id=rule.id,
                    event_id=event.id if event else None,
                    status="skipped",
                    trigger=trigger,
                    error=f"missing required payload key: {required}",
                    completed_at=_now(),
                )
                store.save_execution(execution)
                return {"ok": True, "execution": execution.to_dict(), "skipped": True}

        execution = AutomationExecutionRecord(
            id=new_id("aex_"),
            organization_id=rule.organization_id,
            workspace_id=rule.workspace_id,
            rule_id=rule.id,
            event_id=event.id if event else None,
            status="queued",
            trigger=trigger,
        )
        store.save_execution(execution)
        if rule.mode in ("queue", "background"):
            store.enqueue(execution.id)
            dequeued = store.dequeue()
            if dequeued != execution.id and dequeued:
                store.enqueue(dequeued)

        execution.status = "running"
        execution.started_at = _now()
        store.save_execution(execution)
        results: list[dict[str, Any]] = []
        try:
            steps = rule.actions
            if rule.mode == "multi_step" or len(steps) > 1:
                for idx, action in enumerate(steps):
                    results.append(
                        self._run_action(rule, action, idx, event, execution)
                    )
            else:
                results.append(
                    self._run_action(rule, steps[0], 0, event, execution)
                )
            execution.results = results
            execution.status = "completed"
            execution.completed_at = _now()
            store.save_execution(execution)
            _history(
                organization_id=rule.organization_id,
                rule_id=rule.id,
                execution_id=execution.id,
                event_type="completed",
                message="Automation completed",
            )
            return {"ok": True, "execution": execution.to_dict()}
        except Exception as exc:
            execution.status = "failed"
            execution.error = str(exc)
            execution.completed_at = _now()
            store.save_execution(execution)
            _history(
                organization_id=rule.organization_id,
                rule_id=rule.id,
                execution_id=execution.id,
                event_type="failed",
                message=str(exc),
            )
            return {"ok": False, "execution": execution.to_dict()}

    def run_manual(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            rule_id = str(require_non_empty(payload.get("ruleId"), "ruleId"))
            rule = store.get_rule(rule_id)
            _, NotFoundError = _auth_errors()
            if rule is None or rule.status == "archived":
                raise NotFoundError("automation not found")
            _require_member(
                actor_id=actor_id, organization_id=rule.organization_id
            )
            return self.execute_rule(
                rule, event=None, actor_id=actor_id, trigger="manual"
            )

    def _run_action(
        self,
        rule: AutomationRuleRecord,
        action: dict[str, Any],
        index: int,
        event: EventBusRecord | None,
        execution: AutomationExecutionRecord,
    ) -> dict[str, Any]:
        action_type = str(action.get("type") or action.get("action") or "notify")
        result: dict[str, Any] = {
            "step": index,
            "type": action_type,
            "status": "completed",
        }
        if action_type in ("notify", "ai_workflow", "transform", "log"):
            result["output"] = {
                "message": f"{action_type} executed",
                "eventType": event.event_type if event else None,
                "ruleId": rule.id,
            }
        elif action_type == "integration_deliver":
            if not rule.integration_id:
                ValidationError, _ = _validation()
                raise ValidationError("integrationId required for integration_deliver")
            conn = store.get_integration(rule.integration_id)
            if conn is None:
                ValidationError, _ = _validation()
                raise ValidationError("integration connection not found")
            if event is None:
                # synthesize event for scheduled/manual
                event = EventBusRecord(
                    id=new_id("evt_"),
                    organization_id=rule.organization_id,
                    workspace_id=rule.workspace_id,
                    event_type="custom.event",
                    category="webhook",
                    payload={"executionId": execution.id},
                    actor_user_id=execution.id,
                )
            result["output"] = self.hub.deliver(conn, event)
        else:
            result["output"] = {"message": f"custom action {action_type}"}
        return result

    def _get_for_write(self, rule_id: str, *, actor_id: str) -> AutomationRuleRecord:
        ForbiddenError, NotFoundError = _auth_errors()
        rule = store.get_rule(rule_id)
        if rule is None or rule.status == "archived":
            raise NotFoundError("automation not found")
        if rule.owner_user_id != actor_id:
            try:
                _require_access(
                    user_id=actor_id,
                    organization_id=rule.organization_id,
                    permission="org.update",
                )
            except Exception:
                raise ForbiddenError("only the automation owner can perform this action")
        return rule


class EnterpriseAutomationFacade:
    """Facade combining all enterprise automation engines."""

    def __init__(self) -> None:
        self.hub = IntegrationHub()
        self.bus = EventBusEngine()
        self.triggers = WorkflowTriggerEngine()
        self.automation = AutomationEngine(self.hub)
        self.processing = EventProcessingEngine(
            self.bus, self.triggers, self.automation
        )
        self.scheduler = ScheduledAutomationEngine(self.automation)

    def publish_and_process(
        self, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        published = self.bus.publish(payload, actor_id=actor_id)
        processed = self.processing.process(
            published["event"]["id"], actor_id=actor_id
        )
        return {
            "ok": True,
            "event": published["event"],
            "processing": processed,
        }

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "automation": "ready",
                "eventBus": "ready",
                "integrationHub": "ready",
                "workflowTrigger": "ready",
                "scheduledAutomation": "ready",
                "eventProcessing": "ready",
            },
            "eventTypes": list(EVENT_TYPES),
            "integrationProviders": list(INTEGRATION_PROVIDERS),
            "automationModes": list(AUTOMATION_MODES),
            "stats": store.metrics(),
        }


_service: EnterpriseAutomationFacade | None = None


def get_enterprise_automation_service() -> EnterpriseAutomationFacade:
    global _service
    if _service is None:
        _service = EnterpriseAutomationFacade()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    _service = None


get_engine = get_enterprise_automation_service
