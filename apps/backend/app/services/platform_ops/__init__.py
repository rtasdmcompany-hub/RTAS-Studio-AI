"""RTAS Studio AI — Enterprise Administration, System Management & Platform Operations Engine (Phase 7 Sprint 9)."""

from app.services.platform_ops.engine import (
    PlatformOpsService,
    get_engine,
    get_platform_ops_service,
    reset_engine,
)
from app.services.platform_ops.version import (
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
    "PlatformOpsService",
    "get_platform_ops_service",
    "get_engine",
    "reset_engine",
]
