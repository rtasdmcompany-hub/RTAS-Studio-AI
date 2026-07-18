"""RTAS Studio AI — AI Model Routing Engine (Phase 6 Sprint 3)."""

from app.services.model_routing.engine import (
    list_models,
    plan_dict,
    plan_route,
    reset_routing,
    router_status,
    select_dict,
    select_provider,
    select_route,
)
from app.services.model_routing.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ENGINE_LABEL",
    "plan_route",
    "plan_dict",
    "select_provider",
    "select_dict",
    "select_route",
    "list_models",
    "router_status",
    "reset_routing",
]
