"""Thread-safe in-memory store for enterprise automation & event bus."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.enterprise_automation.models import (
        AutomationExecutionRecord,
        AutomationHistoryRecord,
        AutomationRuleRecord,
        EventBusRecord,
        EventLogRecord,
        EventSubscriptionRecord,
        IntegrationConnectionRecord,
        ScheduledAutomationRecord,
    )

_lock = threading.RLock()

_rules: OrderedDict[str, "AutomationRuleRecord"] = OrderedDict()
_executions: OrderedDict[str, "AutomationExecutionRecord"] = OrderedDict()
_events: OrderedDict[str, "EventBusRecord"] = OrderedDict()
_event_logs: OrderedDict[str, "EventLogRecord"] = OrderedDict()
_subscriptions: OrderedDict[str, "EventSubscriptionRecord"] = OrderedDict()
_integrations: OrderedDict[str, "IntegrationConnectionRecord"] = OrderedDict()
_schedules: OrderedDict[str, "ScheduledAutomationRecord"] = OrderedDict()
_history: OrderedDict[str, "AutomationHistoryRecord"] = OrderedDict()
_queue: list[str] = []

_op_timings: list[float] = []
_op_count = 0
_error_count = 0


def reset_store() -> None:
    global _op_count, _error_count
    with _lock:
        for coll in (
            _rules, _executions, _events, _event_logs, _subscriptions,
            _integrations, _schedules, _history, _queue,
        ):
            coll.clear()
        _op_timings.clear()
        _op_count = 0
        _error_count = 0


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


@contextmanager
def timed_op() -> Iterator[None]:
    global _op_count
    start = time.perf_counter()
    try:
        yield
    except Exception:
        record_error()
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        with _lock:
            _op_timings.append(ms)
            if len(_op_timings) > 500:
                del _op_timings[: len(_op_timings) - 500]
            _op_count += 1


def metrics() -> dict[str, Any]:
    with _lock:
        timings = list(_op_timings)
        avg = sum(timings) / len(timings) if timings else 0.0
        return {
            "opCount": _op_count,
            "errorCount": _error_count,
            "avgLatencyMs": round(avg, 3),
            "automationRules": len(_rules),
            "executions": len(_executions),
            "events": len(_events),
            "eventLogs": len(_event_logs),
            "subscriptions": len(_subscriptions),
            "integrations": len(_integrations),
            "scheduledAutomations": len(_schedules),
            "history": len(_history),
            "queueDepth": len(_queue),
        }


def save_rule(rule: "AutomationRuleRecord") -> None:
    with _lock:
        _rules[rule.id] = rule


def get_rule(rule_id: str) -> "AutomationRuleRecord | None":
    with _lock:
        return _rules.get(rule_id)


def list_rules(
    *,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    status: str | None = None,
    trigger_event: str | None = None,
) -> list["AutomationRuleRecord"]:
    with _lock:
        return [
            r
            for r in _rules.values()
            if (organization_id is None or r.organization_id == organization_id)
            and (workspace_id is None or r.workspace_id == workspace_id)
            and (status is None or r.status == status)
            and (trigger_event is None or r.trigger_event == trigger_event)
            and r.status != "archived"
        ]


def save_execution(execution: "AutomationExecutionRecord") -> None:
    with _lock:
        _executions[execution.id] = execution


def get_execution(execution_id: str) -> "AutomationExecutionRecord | None":
    with _lock:
        return _executions.get(execution_id)


def list_executions(
    *, organization_id: str | None = None, rule_id: str | None = None, limit: int = 100
) -> list["AutomationExecutionRecord"]:
    with _lock:
        items = [
            e
            for e in _executions.values()
            if (organization_id is None or e.organization_id == organization_id)
            and (rule_id is None or e.rule_id == rule_id)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def enqueue(execution_id: str) -> None:
    with _lock:
        _queue.append(execution_id)


def dequeue() -> str | None:
    with _lock:
        if not _queue:
            return None
        return _queue.pop(0)


def save_event(event: "EventBusRecord") -> None:
    with _lock:
        _events[event.id] = event
        if len(_events) > 100_000:
            _events.popitem(last=False)


def get_event(event_id: str) -> "EventBusRecord | None":
    with _lock:
        return _events.get(event_id)


def list_events(
    *,
    organization_id: str | None = None,
    event_type: str | None = None,
    category: str | None = None,
    limit: int = 100,
) -> list["EventBusRecord"]:
    with _lock:
        items = [
            e
            for e in _events.values()
            if (organization_id is None or e.organization_id == organization_id)
            and (event_type is None or e.event_type == event_type)
            and (category is None or e.category == category)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def save_event_log(log: "EventLogRecord") -> None:
    with _lock:
        _event_logs[log.id] = log
        if len(_event_logs) > 100_000:
            _event_logs.popitem(last=False)


def list_event_logs(
    *, organization_id: str | None = None, event_id: str | None = None, limit: int = 100
) -> list["EventLogRecord"]:
    with _lock:
        items = [
            l
            for l in _event_logs.values()
            if (organization_id is None or l.organization_id == organization_id)
            and (event_id is None or l.event_id == event_id)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def save_subscription(sub: "EventSubscriptionRecord") -> None:
    with _lock:
        _subscriptions[sub.id] = sub


def list_subscriptions(
    *,
    organization_id: str | None = None,
    event_type: str | None = None,
) -> list["EventSubscriptionRecord"]:
    with _lock:
        return [
            s
            for s in _subscriptions.values()
            if (organization_id is None or s.organization_id == organization_id)
            and (event_type is None or s.event_type == event_type)
            and s.status == "active"
        ]


def save_integration(conn: "IntegrationConnectionRecord") -> None:
    with _lock:
        _integrations[conn.id] = conn


def get_integration(connection_id: str) -> "IntegrationConnectionRecord | None":
    with _lock:
        return _integrations.get(connection_id)


def list_integrations(
    *,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    provider: str | None = None,
) -> list["IntegrationConnectionRecord"]:
    with _lock:
        return [
            c
            for c in _integrations.values()
            if (organization_id is None or c.organization_id == organization_id)
            and (workspace_id is None or c.workspace_id == workspace_id)
            and (provider is None or c.provider == provider)
            and c.status != "disconnected"
        ]


def save_schedule(job: "ScheduledAutomationRecord") -> None:
    with _lock:
        _schedules[job.id] = job


def get_schedule(schedule_id: str) -> "ScheduledAutomationRecord | None":
    with _lock:
        return _schedules.get(schedule_id)


def list_schedules(
    *, organization_id: str | None = None, status: str | None = None
) -> list["ScheduledAutomationRecord"]:
    with _lock:
        return [
            s
            for s in _schedules.values()
            if (organization_id is None or s.organization_id == organization_id)
            and (status is None or s.status == status)
        ]


def save_history(record: "AutomationHistoryRecord") -> None:
    with _lock:
        _history[record.id] = record
        if len(_history) > 100_000:
            _history.popitem(last=False)


def list_history(
    *, organization_id: str | None = None, rule_id: str | None = None, limit: int = 100
) -> list["AutomationHistoryRecord"]:
    with _lock:
        items = [
            h
            for h in _history.values()
            if (organization_id is None or h.organization_id == organization_id)
            and (rule_id is None or h.rule_id == rule_id)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]
