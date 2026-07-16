"""Scene Breakdown & Shot Generation Engine — public API."""

from app.services.intelligence.scene_breakdown.bridge import to_legacy_plans
from app.services.intelligence.scene_breakdown.engine import (
    build_production_breakdown,
    build_production_breakdown_dict,
)
from app.services.intelligence.scene_breakdown.models import ProductionBreakdown

__all__ = [
    "ProductionBreakdown",
    "build_production_breakdown",
    "build_production_breakdown_dict",
    "to_legacy_plans",
]
