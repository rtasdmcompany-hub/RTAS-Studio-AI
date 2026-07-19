"""RTAS Studio AI — Enterprise Community Platform & Social Collaboration Engine (Phase 9 Sprint 3)."""

from app.services.community_platform.engine import (
    CommunityEngine,
    get_community_platform_service,
    get_engine,
    reset_engine,
)
from app.services.community_platform.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "PHASE",
    "SPRINT",
    "CommunityEngine",
    "get_community_platform_service",
    "get_engine",
    "reset_engine",
]
