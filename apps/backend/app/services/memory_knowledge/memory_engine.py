"""Memory Engine — project/user/character/prompt/conversation/asset/production."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.memory_knowledge import cache, crypto, metrics, security, store
from app.services.memory_knowledge.models import MemoryRecord, MemoryType, TimelineEntry, new_id
from app.services.memory_knowledge.version import SHORT_TERM_TTL_SEC


def _expire_for(memory_type: MemoryType) -> str | None:
    if memory_type == "short_term":
        return (
            datetime.now(timezone.utc) + timedelta(seconds=SHORT_TERM_TTL_SEC)
        ).isoformat()
    return None


def store_memory(
    *,
    user_id: str,
    memory_type: MemoryType,
    title: str,
    content: str,
    project_id: str | None = None,
    character_id: str | None = None,
    scene_id: str | None = None,
    asset_id: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    importance: float = 0.5,
    encrypt: bool = True,
) -> dict[str, Any]:
    uid = security.assert_user(user_id)
    if project_id:
        store.register_project_member(project_id, uid)
    plain = content or ""
    enc = crypto.encrypt_text(plain) if encrypt else plain
    mid = new_id("mem")
    rec = MemoryRecord(
        memory_id=mid,
        memory_type=memory_type,
        user_id=uid,
        project_id=project_id,
        title=title or memory_type,
        content=plain if not encrypt else "",
        content_encrypted=enc,
        tags=list(tags or []),
        character_id=character_id,
        scene_id=scene_id,
        asset_id=asset_id,
        metadata=dict(metadata or {}),
        importance=max(0.0, min(1.0, float(importance))),
        expires_at=_expire_for(memory_type),
    )
    # Keep plaintext in-process for retrieval after decrypt path
    if encrypt:
        rec.content = plain
    store.save_memory(rec)
    store.add_timeline(
        TimelineEntry(
            entry_id=new_id("tl"),
            user_id=uid,
            project_id=project_id,
            event_type=f"memory.{memory_type}",
            summary=title or mid,
            ref_id=mid,
        )
    )
    security.audit(uid, "store", "memory", mid, project_id=project_id, detail=memory_type)
    cache.clear()  # invalidate retrieval cache
    return rec.to_dict(include_content=True)


def _alive(rec: MemoryRecord) -> bool:
    if not rec.expires_at:
        return True
    try:
        exp = datetime.fromisoformat(rec.expires_at.replace("Z", "+00:00"))
        return exp > datetime.now(timezone.utc)
    except ValueError:
        return True


def retrieve_memory(
    *,
    user_id: str,
    query: str | None = None,
    project_id: str | None = None,
    memory_type: MemoryType | None = None,
    character_id: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    from app.services.memory_knowledge.retrieval import semantic_search

    uid = security.assert_user(user_id)
    t0 = metrics.timed()
    cache_key = f"ret:{uid}:{project_id}:{memory_type}:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        metrics.record_retrieval(metrics.elapsed_ms(t0), score=cached.get("_top_score"))
        return {
            "ok": True,
            "count": cached.get("count", 0),
            "results": cached.get("results", []),
        }

    rows = [
        m
        for m in store.memories_for(user_id=uid, project_id=project_id, memory_type=memory_type)
        if _alive(m) and (not character_id or m.character_id == character_id)
    ]
    for m in rows:
        security.require_access(uid, owner_id=m.user_id, project_id=m.project_id)
        if not m.content and m.content_encrypted:
            try:
                m.content = crypto.decrypt_text(m.content_encrypted)
            except ValueError:
                m.content = ""

    results = []
    top_score = 0.0
    if query:
        corpus = [
            {
                "id": m.memory_id,
                "title": m.title,
                "body": f"{m.title} {m.content} {' '.join(m.tags)}",
                "tags": m.tags,
                "source": "memory",
                "metadata": {
                    "memory_type": m.memory_type,
                    "project_id": m.project_id,
                    "character_id": m.character_id,
                },
            }
            for m in rows
        ]
        hits = semantic_search(query, corpus, top_k=limit)
        top_score = hits[0].score if hits else 0.0
        by_id = {m.memory_id: m for m in rows}
        for h in hits:
            m = by_id.get(h.ref_id)
            if m:
                results.append({**m.to_dict(), "score": h.score})
    else:
        rows.sort(key=lambda m: (-m.importance, m.updated_at), reverse=False)
        rows.sort(key=lambda m: (-m.importance, m.created_at))
        results = [m.to_dict() for m in rows[:limit]]
        top_score = 1.0 if results else 0.0

    payload = {
        "ok": True,
        "count": len(results),
        "results": results,
        "_top_score": top_score,
    }
    cache.set(cache_key, payload)
    metrics.record_retrieval(metrics.elapsed_ms(t0), score=top_score)
    security.audit(uid, "retrieve", "memory", project_id or "all", project_id=project_id)
    return {"ok": True, "count": len(results), "results": results}


def project_memory(user_id: str, project_id: str) -> dict[str, Any]:
    uid = security.assert_user(user_id)
    store.register_project_member(project_id, uid)
    mems = [m for m in store.memories_for(user_id=uid, project_id=project_id) if _alive(m)]
    by_type: dict[str, list] = {}
    for m in mems:
        if not m.content and m.content_encrypted:
            try:
                m.content = crypto.decrypt_text(m.content_encrypted)
            except ValueError:
                pass
        by_type.setdefault(m.memory_type, []).append(m.to_dict())
    history = [e.to_dict() for e in store.timeline(user_id=uid, project_id=project_id, limit=100)]
    security.audit(uid, "project_memory", "project", project_id, project_id=project_id)
    return {
        "ok": True,
        "project_id": project_id,
        "memory_count": len(mems),
        "by_type": by_type,
        "production_history": history,
        "characters": by_type.get("character", []),
        "prompts": by_type.get("prompt", []),
        "assets": by_type.get("asset", []) + by_type.get("asset_references", []),
        "conversations": by_type.get("conversation", []),
    }


def memory_history(
    *,
    user_id: str,
    project_id: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    uid = security.assert_user(user_id)
    entries = store.timeline(user_id=uid, project_id=project_id, limit=limit)
    return {
        "ok": True,
        "count": len(entries),
        "history": [e.to_dict() for e in entries],
        "audits": [a.to_dict() for a in store.audits(limit=min(20, limit))],
    }
