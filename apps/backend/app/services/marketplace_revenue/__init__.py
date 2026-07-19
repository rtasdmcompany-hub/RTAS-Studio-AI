"""RTAS Studio AI — Marketplace Analytics, Revenue Intelligence & Monetization (Phase 9 Sprint 9)."""

from app.services.marketplace_revenue.engine import (
    MarketplaceRevenueFacade,
    get_engine,
    get_marketplace_revenue_service,
    reset_engine,
)
from app.services.marketplace_revenue.version import (
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
    "MarketplaceRevenueFacade",
    "get_marketplace_revenue_service",
    "get_engine",
    "reset_engine",
]
