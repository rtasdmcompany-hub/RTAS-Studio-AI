"""Best-provider selection using prompt understanding + capabilities."""

from __future__ import annotations

from typing import Any

from app.services.multi_ai.registry import DEFAULT_FAILOVER_ORDER
from app.services.providers.base import BaseAIProvider


def _score_provider(
    name: str,
    adapter: BaseAIProvider,
    *,
    category: str | None,
    mood: str | None,
    preferred: str | None,
) -> float:
    if not adapter.is_configured():
        return -1.0
    score = 10.0
    strengths = {s.lower() for s in adapter.strengths}
    cat = (category or "").lower()
    md = (mood or "").lower()

    if preferred and name == preferred:
        score += 50.0

    # Category / scene affinity
    affinities = {
        "music video": ("pika", "luma", "kling"),
        "advertisement": ("runway", "fal", "kling"),
        "product video": ("runway", "svd", "fal"),
        "movie scene": ("veo", "kling", "luma"),
        "trailer": ("luma", "veo", "kling"),
        "short film": ("hailuo", "veo", "kling"),
        "tiktok": ("pika", "hailuo", "fal"),
        "instagram reel": ("pika", "fal", "runway"),
        "youtube shorts": ("pika", "fal", "hailuo"),
        "documentary": ("veo", "replicate", "fal"),
        "anime": ("cogvideo", "pika", "fal"),
    }
    for key, names in affinities.items():
        if key in cat and name in names:
            score += 12.0 - names.index(name)

    if md in ("emotional", "dark", "intimate") and name in ("veo", "hailuo", "kling"):
        score += 6.0
    if "cinematic" in strengths:
        score += 3.0

    # Prefer lower cost / faster ETA lightly
    score += max(0.0, 5.0 - adapter.cost_per_second_usd * 20.0)
    score += max(0.0, 3.0 - adapter.typical_eta_seconds / 60.0)
    return score


def select_best_provider(
    registry: dict[str, BaseAIProvider],
    *,
    available: list[str] | None = None,
    category: str | None = None,
    mood: str | None = None,
    preferred: str | None = None,
) -> str | None:
    candidates = available or [n for n, a in registry.items() if a.is_configured()]
    if preferred and preferred in candidates:
        return preferred
    if not candidates:
        return None
    ranked = sorted(
        candidates,
        key=lambda n: _score_provider(
            n,
            registry[n],
            category=category,
            mood=mood,
            preferred=preferred,
        ),
        reverse=True,
    )
    return ranked[0] if ranked else None


def build_failover_chain(
    primary: str | None,
    available: list[str],
    *,
    max_providers: int = 4,
) -> list[str]:
    chain: list[str] = []
    if primary and primary in available:
        chain.append(primary)
    for name in DEFAULT_FAILOVER_ORDER:
        if name in available and name not in chain:
            chain.append(name)
        if len(chain) >= max_providers:
            break
    # Include any remaining available not in default order
    for name in available:
        if name not in chain and len(chain) < max_providers:
            chain.append(name)
    return chain


def selection_context_from_fields(fields: dict[str, Any] | None) -> dict[str, str | None]:
    fields = fields or {}
    preferred = fields.get("preferredProvider") or fields.get("aiProvider")
    category = None
    mood = None
    understanding = fields.get("rtasPromptUnderstanding")
    if isinstance(understanding, str):
        try:
            import json

            understanding = json.loads(understanding)
        except Exception:
            understanding = None
    if isinstance(understanding, dict):
        category = understanding.get("category") or understanding.get("scene_type")
        mood = understanding.get("mood")
    return {
        "preferred": preferred if isinstance(preferred, str) else None,
        "category": category if isinstance(category, str) else None,
        "mood": mood if isinstance(mood, str) else None,
    }
