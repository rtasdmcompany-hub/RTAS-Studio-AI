"""RTAS Studio AI — Enterprise AI Orchestration Platform v1.0 (Phase 6 Sprint 10 Final)."""

from app.services.enterprise_platform.engine import get_platform_engine, reset_engine
from app.services.enterprise_platform.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PLATFORM_LABEL,
    PLATFORM_NAME,
    PLATFORM_VERSION,
)

__all__ = [
    "PLATFORM_NAME",
    "PLATFORM_VERSION",
    "PLATFORM_LABEL",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "get_platform_engine",
    "reset_engine",
]
