"""RTAS Studio AI — AI Model Routing Engine (Phase 6 Sprint 3).

Also re-exports legacy cost-optimized generation routing used by ai_service.
"""

from app.services.model_routing.cost_policy import (
    HARD_BUDGET_CEILING_USD,
    MODEL_CATALOG,
    ModelRoutingError,
    ModelSelection,
    ModelSpec,
    apply_model_selection,
    credit_weight_for_cost,
    get_cost_policy_payload,
    get_routing_policy_summary,
    select_optimal_model,
    weighted_credits_for_duration,
)
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
    # Legacy cost routing (generation pipeline)
    "ModelRoutingError",
    "ModelSelection",
    "ModelSpec",
    "MODEL_CATALOG",
    "HARD_BUDGET_CEILING_USD",
    "apply_model_selection",
    "credit_weight_for_cost",
    "get_cost_policy_payload",
    "get_routing_policy_summary",
    "select_optimal_model",
    "weighted_credits_for_duration",
]
