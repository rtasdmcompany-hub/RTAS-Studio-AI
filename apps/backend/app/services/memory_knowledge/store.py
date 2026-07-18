"""Thread-safe in-memory stores for memory, context, knowledge, timeline."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

from app.services.memory_knowledge.version import MAX_KNOWLEDGE_RECORDS, MAX_MEMORY_RECORDS

if TYPE_CHECKING:
    from app.services.memory_knowledge.models import (
        AuditLogEntry,
        ContextRecord,
        KnowledgeRecord,
        MemoryRecord,
        TimelineEntry,
    )

_lock = threading.Lock()
_memories: OrderedDict[str, "MemoryRecord"] = OrderedDict()
_contexts: OrderedDict[str, "ContextRecord"] = OrderedDict()
_knowledge: OrderedDict[str, "KnowledgeRecord"] = OrderedDict()
_timeline: list["TimelineEntry"] = []
_audits: list["AuditLogEntry"] = []
_project_members: dict[str, set[str]] = {}
_context_by_project: dict[str, str] = {}


def save_memory(rec: "MemoryRecord") -> "MemoryRecord":
    with _lock:
        _memories[rec.memory_id] = rec
        while len(_memories) > MAX_MEMORY_RECORDS:
            _memories.popitem(last=False)
        return rec


def get_memory(memory_id: str) -> "MemoryRecord | None":
    with _lock:
        return _memories.get(memory_id)


def all_memories() -> list["MemoryRecord"]:
    with _lock:
        return list(_memories.values())


def memories_for(
    *,
    user_id: str | None = None,
    project_id: str | None = None,
    memory_type: str | None = None,
) -> list["MemoryRecord"]:
    with _lock:
        out = []
        for m in _memories.values():
            if user_id and m.user_id != user_id:
                continue
            if project_id and m.project_id != project_id:
                continue
            if memory_type and m.memory_type != memory_type:
                continue
            out.append(m)
        return out


def save_context(rec: "ContextRecord") -> "ContextRecord":
    with _lock:
        _contexts[rec.context_id] = rec
        if rec.project_id:
            _context_by_project[f"{rec.user_id}:{rec.project_id}"] = rec.context_id
        return rec


def get_context(context_id: str) -> "ContextRecord | None":
    with _lock:
        return _contexts.get(context_id)


def context_for_project(user_id: str, project_id: str) -> "ContextRecord | None":
    with _lock:
        cid = _context_by_project.get(f"{user_id}:{project_id}")
        return _contexts.get(cid) if cid else None


def all_contexts() -> list["ContextRecord"]:
    with _lock:
        return list(_contexts.values())


def save_knowledge(rec: "KnowledgeRecord") -> "KnowledgeRecord":
    with _lock:
        _knowledge[rec.knowledge_id] = rec
        while len(_knowledge) > MAX_KNOWLEDGE_RECORDS:
            _knowledge.popitem(last=False)
        return rec


def get_knowledge(kid: str) -> "KnowledgeRecord | None":
    with _lock:
        return _knowledge.get(kid)


def all_knowledge() -> list["KnowledgeRecord"]:
    with _lock:
        return list(_knowledge.values())


def add_timeline(entry: "TimelineEntry") -> "TimelineEntry":
    with _lock:
        _timeline.append(entry)
        if len(_timeline) > 5000:
            del _timeline[:1000]
        return entry


def timeline(
    *,
    user_id: str | None = None,
    project_id: str | None = None,
    limit: int = 50,
) -> list["TimelineEntry"]:
    with _lock:
        items = [
            e
            for e in _timeline
            if (not user_id or e.user_id == user_id)
            and (not project_id or e.project_id == project_id)
        ]
        return list(reversed(items[-max(1, min(500, limit)) :]))


def save_audit(entry: "AuditLogEntry") -> "AuditLogEntry":
    with _lock:
        _audits.append(entry)
        if len(_audits) > 5000:
            del _audits[:1000]
        return entry


def audits(limit: int = 50) -> list["AuditLogEntry"]:
    with _lock:
        return list(reversed(_audits[-max(1, min(500, limit)) :]))


def register_project_member(project_id: str, user_id: str) -> None:
    with _lock:
        _project_members.setdefault(project_id, set()).add(user_id)


def project_members(project_id: str) -> set[str]:
    with _lock:
        return set(_project_members.get(project_id) or set())


def clear() -> None:
    with _lock:
        _memories.clear()
        _contexts.clear()
        _knowledge.clear()
        _timeline.clear()
        _audits.clear()
        _project_members.clear()
        _context_by_project.clear()
