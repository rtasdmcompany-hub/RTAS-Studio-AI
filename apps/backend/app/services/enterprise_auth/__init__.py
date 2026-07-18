"""RTAS Studio AI — Enterprise Authentication & Access Control (Phase 7 Sprint 2)."""

from app.services.enterprise_auth.engine import (
    EnterpriseAuthService,
    get_engine,
    get_enterprise_auth_service,
    reset_engine,
)
from app.services.enterprise_auth.middleware import get_access_middleware, require_access
from app.services.enterprise_auth.version import (
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
    "EnterpriseAuthService",
    "get_engine",
    "get_enterprise_auth_service",
    "reset_engine",
    "get_access_middleware",
    "require_access",
]
