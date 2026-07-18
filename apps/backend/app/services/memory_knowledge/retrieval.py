"""Smart retrieval — semantic token search, similarity, suggestions, duplicates."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Iterable

from app.services.memory_knowledge.models import RetrievalResult

_TOKEN_RE = re.compile(r"[a-z0-9_]{2,}")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def _tfidf_vectors(docs: list[list[str]]) -> list[dict[str, float]]:
    n = len(docs) or 1
    df: Counter[str] = Counter()
    for toks in docs:
        for t in set(toks):
            df[t] += 1
    vectors = []
    for toks in docs:
        tf = Counter(toks)
        length = sum(tf.values()) or 1
        vec = {}
        for t, c in tf.items():
            idf = math.log((n + 1) / (df[t] + 1)) + 1.0
            vec[t] = (c / length) * idf
        vectors.append(vec)
    return vectors


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values())) or 1.0
    nb = math.sqrt(sum(v * v for v in b.values())) or 1.0
    return max(0.0, min(1.0, dot / (na * nb)))


def semantic_search(
    query: str,
    corpus: Iterable[dict[str, Any]],
    *,
    text_key: str = "body",
    id_key: str = "id",
    title_key: str = "title",
    top_k: int = 20,
) -> list[RetrievalResult]:
    items = list(corpus)
    if not items:
        return []
    docs = [tokenize(str(it.get(text_key) or "") + " " + str(it.get(title_key) or "")) for it in items]
    q_toks = tokenize(query)
    vectors = _tfidf_vectors(docs + [q_toks])
    q_vec = vectors[-1]
    doc_vecs = vectors[:-1]
    scored: list[RetrievalResult] = []
    for it, vec in zip(items, doc_vecs):
        score = _cosine(q_vec, vec)
        # Boost tag / title overlap
        title = str(it.get(title_key) or "")
        tags = it.get("tags") or []
        tag_hits = sum(1 for t in tokenize(" ".join(tags) + " " + title) if t in q_toks)
        score = min(1.0, score + 0.05 * tag_hits)
        if score <= 0:
            continue
        body = str(it.get(text_key) or "")
        scored.append(
            RetrievalResult(
                ref_id=str(it.get(id_key)),
                source=str(it.get("source") or "knowledge"),
                score=round(score, 4),
                title=title or str(it.get(id_key)),
                snippet=body[:180],
                metadata=dict(it.get("metadata") or {}),
            )
        )
    scored.sort(key=lambda r: (-r.score, r.title))
    return scored[: max(1, min(100, top_k))]


def jaccard(a: str, b: str) -> float:
    ta, tb = set(tokenize(a)), set(tokenize(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def detect_duplicates(
    text: str,
    candidates: Iterable[dict[str, Any]],
    *,
    threshold: float = 0.85,
    text_key: str = "body",
) -> list[dict[str, Any]]:
    out = []
    for it in candidates:
        score = jaccard(text, str(it.get(text_key) or ""))
        if score >= threshold:
            out.append({"id": it.get("id"), "score": round(score, 4), "title": it.get("title")})
    out.sort(key=lambda x: -x["score"])
    return out


def similar_projects(
    query: str,
    projects: Iterable[dict[str, Any]],
    *,
    top_k: int = 5,
) -> list[RetrievalResult]:
    return semantic_search(
        query,
        [{**p, "source": "project"} for p in projects],
        text_key="body",
        id_key="id",
        title_key="title",
        top_k=top_k,
    )


def prompt_suggestions(
    partial: str,
    prompts: Iterable[str],
    *,
    top_k: int = 5,
) -> list[str]:
    q = tokenize(partial)
    scored = []
    for p in prompts:
        toks = set(tokenize(p))
        if not toks:
            continue
        overlap = len(set(q) & toks) / max(1, len(set(q) or {1}))
        if overlap > 0 or (partial and partial.lower() in p.lower()):
            scored.append((overlap, p))
    scored.sort(key=lambda x: (-x[0], len(x[1])))
    return [p for _, p in scored[:top_k]]
