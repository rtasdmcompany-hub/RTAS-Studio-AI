"""RTAS Studio AI — Enterprise License, API Access & Developer Platform (Phase 8 Sprint 7)."""

from app.services.license_platform.engine import (
    LicensePlatformService,
    get_engine,
    get_license_platform_service,
    reset_engine,
)
from app.services.license_platform.version import (
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
    "LicensePlatformService",
    "get_license_platform_service",
    "get_engine",
    "reset_engine",
]
