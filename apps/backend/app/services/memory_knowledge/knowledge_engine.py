"""Knowledge Engine — searchable KB + smart recommendations."""

from __future__ import annotations

from typing import Any

from app.services.memory_knowledge import cache, metrics, security, store
from app.services.memory_knowledge.models import KnowledgeKind, KnowledgeRecord, new_id
from app.services.memory_knowledge.retrieval import (
    detect_duplicates,
    prompt_suggestions,
    semantic_search,
    similar_projects,
    tokenize,
)
from app.services.memory_knowledge.version import RETRIEVAL_TOP_K


def index_knowledge(
    *,
    user_id: str,
    kind: KnowledgeKind,
    title: str,
    body: str,
    project_id: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    uid = security.assert_user(user_id)
    if project_id:
        store.register_project_member(project_id, uid)
    text = f"{title}\n{body}"
    dups = detect_duplicates(
        text,
        [
            {"id": k.knowledge_id, "title": k.title, "body": f"{k.title}\n{k.body}"}
            for k in store.all_knowledge()
            if k.user_id == uid
        ],
    )
    rec = KnowledgeRecord(
        knowledge_id=new_id("know"),
        kind=kind,
        user_id=uid,
        project_id=project_id,
        title=title or kind,
        body=body or "",
        tokens=tokenize(text),
        tags=list(tags or []),
        metadata={**(metadata or {}), "duplicates": dups[:3]},
    )
    store.save_knowledge(rec)
    cache.clear()
    security.audit(uid, "index", "knowledge", rec.knowledge_id, project_id=project_id)
    return rec.to_dict()


def search(
    *,
    user_id: str,
    query: str,
    kind: KnowledgeKind | None = None,
    project_id: str | None = None,
    top_k: int = RETRIEVAL_TOP_K,
) -> dict[str, Any]:
    uid = security.assert_user(user_id)
    t0 = metrics.timed()
    cache_key = f"ks:{uid}:{kind}:{project_id}:{query}:{top_k}"
    cached = cache.get(cache_key)
    if cached is not None:
        metrics.record_retrieval(metrics.elapsed_ms(t0), score=cached.get("_top"))
        return {k: v for k, v in cached.items() if not k.startswith("_")}

    rows = [
        k
        for k in store.all_knowledge()
        if k.user_id == uid
        and (not kind or k.kind == kind)
        and (not project_id or k.project_id == project_id)
    ]
    corpus = [
        {
            "id": k.knowledge_id,
            "title": k.title,
            "body": f"{k.title} {k.body} {' '.join(k.tags)}",
            "tags": k.tags,
            "source": k.kind,
            "metadata": {"kind": k.kind, "project_id": k.project_id, **k.metadata},
        }
        for k in rows
    ]
    hits = semantic_search(query, corpus, top_k=top_k)
    top = hits[0].score if hits else 0.0
    metrics.record_retrieval(metrics.elapsed_ms(t0), score=top)

    # Smart extras
    project_docs = [c for c in corpus if c["source"] == "project"]
    similar = similar_projects(query, project_docs, top_k=5)
    prompts = [k.body for k in rows if k.kind == "prompt"]
    suggestions = prompt_suggestions(query, prompts, top_k=5)
    characters = [
        h.to_dict()
        for h in semantic_search(
            query,
            [c for c in corpus if c["source"] == "character"],
            top_k=5,
        )
    ]
    assets = [
        h.to_dict()
        for h in semantic_search(
            query,
            [c for c in corpus if c["source"] == "asset"],
            top_k=5,
        )
    ]
    dups = detect_duplicates(query, corpus, threshold=0.7)

    payload = {
        "ok": True,
        "query": query,
        "count": len(hits),
        "results": [h.to_dict() for h in hits],
        "similar_projects": [s.to_dict() for s in similar],
        "prompt_suggestions": suggestions,
        "character_recall": characters,
        "asset_recommendations": assets,
        "duplicates": dups[:10],
        "_top": top,
    }
    cache.set(cache_key, payload)
    security.audit(uid, "search", "knowledge", "query", project_id=project_id, detail=query[:80])
    return {k: v for k, v in payload.items() if not k.startswith("_")}
