"""Thread-safe in-memory store for project collaboration."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import TYPE_CHECKING, Any

from app.services.project_collaboration.version import (
    MAX_ACTIVITY,
    MAX_NOTES,
    MAX_TASKS,
)

if TYPE_CHECKING:
    from app.services.project_collaboration.models import (
        CollabProject,
        CollaborationNote,
        ProjectActivity,
        ProjectMember,
        ProjectSettings,
        ProjectTask,
        ProjectTemplate,
        ProjectTimelineEvent,
    )

_lock = threading.RLock()
_projects: OrderedDict[str, "CollabProject"] = OrderedDict()
_members: OrderedDict[str, "ProjectMember"] = OrderedDict()
_activity: OrderedDict[str, "ProjectActivity"] = OrderedDict()
_timeline: OrderedDict[str, "ProjectTimelineEvent"] = OrderedDict()
_templates: OrderedDict[str, "ProjectTemplate"] = OrderedDict()
_settings: dict[str, "ProjectSettings"] = {}
_notes: OrderedDict[str, "CollaborationNote"] = OrderedDict()
_tasks: OrderedDict[str, "ProjectTask"] = OrderedDict()

_slug_index: dict[tuple[str, str], str] = {}
_member_key: dict[tuple[str, str], str] = {}
_template_key: dict[tuple[str | None, str], str] = {}

_api_timings: list[float] = []
_api_count = 0
_error_count = 0
_seeded = False


def reset_store() -> None:
    global _seeded, _api_count, _error_count
    with _lock:
        _projects.clear()
        _members.clear()
        _activity.clear()
        _timeline.clear()
        _templates.clear()
        _settings.clear()
        _notes.clear()
        _tasks.clear()
        _slug_index.clear()
        _member_key.clear()
        _template_key.clear()
        _api_timings.clear()
        _api_count = 0
        _error_count = 0
        _seeded = False


def is_seeded() -> bool:
    with _lock:
        return _seeded


def mark_seeded() -> None:
    global _seeded
    with _lock:
        _seeded = True


def save_project(p: "CollabProject") -> "CollabProject":
    with _lock:
        _projects[p.id] = p
        _slug_index[(p.organization_id, p.slug)] = p.id
        return p


def get_project(project_id: str) -> "CollabProject | None":
    with _lock:
        return _projects.get(project_id)


def get_project_by_slug(org_id: str, slug: str) -> "CollabProject | None":
    with _lock:
        pid = _slug_index.get((org_id, slug))
        return _projects.get(pid) if pid else None


def list_projects(
    *,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    owner_id: str | None = None,
    status: str | None = None,
    include_deleted: bool = False,
) -> list["CollabProject"]:
    with _lock:
        items = list(_projects.values())
    if not include_deleted:
        items = [p for p in items if p.status != "deleted" and p.deleted_at is None]
    if organization_id:
        items = [p for p in items if p.organization_id == organization_id]
    if workspace_id:
        items = [p for p in items if p.workspace_id == workspace_id]
    if owner_id:
        items = [p for p in items if p.owner_id == owner_id]
    if status:
        items = [p for p in items if p.status == status]
    return items


def delete_slug(org_id: str, slug: str) -> None:
    with _lock:
        _slug_index.pop((org_id, slug), None)


def save_member(m: "ProjectMember") -> "ProjectMember":
    with _lock:
        _members[m.id] = m
        _member_key[(m.project_id, m.user_id)] = m.id
        return m


def get_member(project_id: str, user_id: str) -> "ProjectMember | None":
    with _lock:
        mid = _member_key.get((project_id, user_id))
        return _members.get(mid) if mid else None


def list_members(project_id: str) -> list["ProjectMember"]:
    with _lock:
        return [m for m in _members.values() if m.project_id == project_id]


def delete_member(project_id: str, user_id: str) -> bool:
    with _lock:
        mid = _member_key.pop((project_id, user_id), None)
        if mid is None:
            return False
        _members.pop(mid, None)
        return True


def add_activity(a: "ProjectActivity") -> "ProjectActivity":
    with _lock:
        _activity[a.id] = a
        while len(_activity) > MAX_ACTIVITY:
            _activity.popitem(last=False)
        return a


def list_activity(project_id: str, *, limit: int = 50) -> list["ProjectActivity"]:
    with _lock:
        items = [a for a in _activity.values() if a.project_id == project_id]
    items.reverse()
    return items[: max(1, min(limit, 500))]


def add_timeline(e: "ProjectTimelineEvent") -> "ProjectTimelineEvent":
    with _lock:
        _timeline[e.id] = e
        while len(_timeline) > MAX_ACTIVITY:
            _timeline.popitem(last=False)
        return e


def list_timeline(project_id: str, *, limit: int = 50) -> list["ProjectTimelineEvent"]:
    with _lock:
        items = [e for e in _timeline.values() if e.project_id == project_id]
    items.reverse()
    return items[: max(1, min(limit, 500))]


def save_template(t: "ProjectTemplate") -> "ProjectTemplate":
    with _lock:
        _templates[t.id] = t
        _template_key[(t.organization_id, t.key)] = t.id
        return t


def get_template_by_key(key: str, organization_id: str | None = None) -> "ProjectTemplate | None":
    with _lock:
        tid = _template_key.get((organization_id, key))
        if tid:
            return _templates.get(tid)
        tid = _template_key.get((None, key))
        return _templates.get(tid) if tid else None


def list_templates(*, organization_id: str | None = None) -> list["ProjectTemplate"]:
    with _lock:
        items = list(_templates.values())
    return [
        t
        for t in items
        if t.organization_id is None
        or (organization_id is not None and t.organization_id == organization_id)
    ]


def save_settings(s: "ProjectSettings") -> "ProjectSettings":
    with _lock:
        _settings[s.project_id] = s
        return s


def get_settings(project_id: str) -> "ProjectSettings | None":
    with _lock:
        return _settings.get(project_id)


def save_note(n: "CollaborationNote") -> "CollaborationNote":
    with _lock:
        _notes[n.id] = n
        while len(_notes) > MAX_NOTES:
            _notes.popitem(last=False)
        return n


def list_notes(project_id: str, *, limit: int = 50) -> list["CollaborationNote"]:
    with _lock:
        items = [n for n in _notes.values() if n.project_id == project_id]
    items.reverse()
    return items[: max(1, min(limit, 500))]


def save_task(t: "ProjectTask") -> "ProjectTask":
    with _lock:
        _tasks[t.id] = t
        while len(_tasks) > MAX_TASKS:
            _tasks.popitem(last=False)
        return t


def get_task(task_id: str) -> "ProjectTask | None":
    with _lock:
        return _tasks.get(task_id)


def list_tasks(project_id: str) -> list["ProjectTask"]:
    with _lock:
        return [t for t in _tasks.values() if t.project_id == project_id]


def record_api(ms: float, *, error: bool = False) -> None:
    global _api_count, _error_count
    with _lock:
        _api_count += 1
        _api_timings.append(ms)
        if len(_api_timings) > 1000:
            del _api_timings[:200]
        if error:
            _error_count += 1


def metrics() -> dict[str, Any]:
    with _lock:
        projects = list(_projects.values())
        timings = list(_api_timings)
        avg = sum(timings) / len(timings) if timings else 0.0
        p95 = sorted(timings)[int(len(timings) * 0.95)] if timings else 0.0
        return {
            "totalProjects": len(projects),
            "activeProjects": sum(
                1 for p in projects if p.status in {"active", "in_progress", "review"}
            ),
            "archivedProjects": sum(1 for p in projects if p.status == "archived"),
            "deletedProjects": sum(1 for p in projects if p.status == "deleted"),
            "members": len(_members),
            "activityEvents": len(_activity),
            "timelineEvents": len(_timeline),
            "notes": len(_notes),
            "tasks": len(_tasks),
            "collaborationEvents": len(_activity) + len(_notes),
            "apiCalls": _api_count,
            "errors": _error_count,
            "avgLatencyMs": round(avg, 2),
            "p95LatencyMs": round(p95, 2),
        }


class timed_op:
    def __init__(self) -> None:
        self._start = 0.0

    def __enter__(self) -> "timed_op":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        record_api((time.perf_counter() - self._start) * 1000, error=bool(exc_type))
        return False
