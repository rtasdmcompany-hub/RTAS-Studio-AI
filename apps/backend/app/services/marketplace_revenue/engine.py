"""Engine entrypoint for marketplace revenue intelligence & monetization."""

from app.services.marketplace_revenue.service import (
    MarketplaceRevenueFacade,
    get_engine,
    get_marketplace_revenue_service,
    reset_engine,
)

__all__ = [
    "MarketplaceRevenueFacade",
    "get_marketplace_revenue_service",
    "get_engine",
    "reset_engine",
]
