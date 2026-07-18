"""Unified Memory, Context & Knowledge Engine facade."""

from __future__ import annotations

from typing import Any

from app.services.memory_knowledge import (
    cache,
    context_engine,
    knowledge_engine,
    memory_engine,
    metrics,
    store,
)
from app.services.memory_knowledge.models import KnowledgeKind, MemoryType
from app.services.memory_knowledge.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


class MemoryKnowledgeEngine:
    def store(
        self,
        *,
        user_id: str,
        memory_type: MemoryType = "long_term",
        title: str,
        content: str,
        project_id: str | None = None,
        character_id: str | None = None,
        scene_id: str | None = None,
        asset_id: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        importance: float = 0.5,
        index_knowledge: bool = True,
        knowledge_kind: KnowledgeKind | None = None,
    ) -> dict[str, Any]:
        mem = memory_engine.store_memory(
            user_id=user_id,
            memory_type=memory_type,
            title=title,
            content=content,
            project_id=project_id,
            character_id=character_id,
            scene_id=scene_id,
            asset_id=asset_id,
            tags=tags,
            metadata=metadata,
            importance=importance,
        )
        know = None
        if index_knowledge:
            kind_map: dict[str, KnowledgeKind] = {
                "project": "project",
                "character": "character",
                "scene": "scene",
                "prompt": "prompt",
                "asset": "asset",
                "asset_references": "asset",
                "production_history": "production_report",
            }
            kind = knowledge_kind or kind_map.get(memory_type, "prompt")
            know = knowledge_engine.index_knowledge(
                user_id=user_id,
                kind=kind,
                title=title,
                body=content,
                project_id=project_id,
                tags=tags,
                metadata={"memory_id": mem["memory_id"], "memory_type": memory_type},
            )
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "memory": mem,
            "knowledge": know,
        }

    def retrieve(
        self,
        *,
        user_id: str,
        query: str | None = None,
        project_id: str | None = None,
        memory_type: MemoryType | None = None,
        character_id: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        result = memory_engine.retrieve_memory(
            user_id=user_id,
            query=query,
            project_id=project_id,
            memory_type=memory_type,
            character_id=character_id,
            limit=limit,
        )
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            **result,
            "performance": self.performance(),
        }

    def load_context(self, **kwargs: Any) -> dict[str, Any]:
        result = context_engine.load_context(**kwargs)
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            **result,
        }

    def project(self, user_id: str, project_id: str) -> dict[str, Any]:
        result = memory_engine.project_memory(user_id, project_id)
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            **result,
        }

    def history(
        self,
        *,
        user_id: str,
        project_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        result = memory_engine.memory_history(
            user_id=user_id, project_id=project_id, limit=limit
        )
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            **result,
        }

    def knowledge_search(
        self,
        *,
        user_id: str,
        query: str,
        kind: KnowledgeKind | None = None,
        project_id: str | None = None,
        top_k: int = 20,
    ) -> dict[str, Any]:
        result = knowledge_engine.search(
            user_id=user_id,
            query=query,
            kind=kind,
            project_id=project_id,
            top_k=top_k,
        )
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            **result,
            "performance": self.performance(),
        }

    def performance(self) -> dict[str, Any]:
        return metrics.summary(
            memory_count=len(store.all_memories()),
            knowledge_count=len(store.all_knowledge()),
            cache_stats=cache.stats(),
        )


_engine: MemoryKnowledgeEngine | None = None


def get_memory_engine() -> MemoryKnowledgeEngine:
    global _engine
    if _engine is None:
        _engine = MemoryKnowledgeEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    store.clear()
    cache.clear()
    metrics.clear()
    _engine = None
