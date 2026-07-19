"""RTAS Studio AI — Enterprise Plugin Framework, Extension SDK & Third-Party Integration Engine (Phase 9 Sprint 5)."""

from app.services.plugin_framework.engine import (
    PluginFrameworkFacade,
    get_engine,
    get_plugin_framework_service,
    reset_engine,
)
from app.services.plugin_framework.version import (
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
    "PluginFrameworkFacade",
    "get_plugin_framework_service",
    "get_engine",
    "reset_engine",
]
