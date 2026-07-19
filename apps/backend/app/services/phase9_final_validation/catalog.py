"""Phase 9 module registry, production endpoints, load batches, quality weights."""

from __future__ import annotations

from typing import Final

PHASE9_MODULES: Final[tuple[tuple[str, str, int], ...]] = (
    ("marketplace_ecosystem", "Marketplace Core", 1),
    ("creator_platform", "Creator Platform", 2),
    ("creator_platform", "Publisher Platform", 2),
    ("community_platform", "Community Platform", 3),
    ("community_platform", "Social Features", 3),
    ("template_store", "Template Store", 4),
    ("template_store", "Asset Management", 4),
    ("plugin_framework", "Plugin Framework", 5),
    ("plugin_framework", "SDK Engine", 5),
    ("plugin_framework", "Third Party Integrations", 5),
    ("public_api_platform", "Public API Platform", 6),
    ("public_api_platform", "Developer Portal", 6),
    ("agent_orchestration", "AI Agents", 7),
    ("agent_orchestration", "Workflow Automation", 7),
    ("enterprise_automation", "Event Bus", 8),
    ("enterprise_automation", "Integration Hub", 8),
    ("marketplace_revenue", "Revenue Analytics", 9),
    ("marketplace_revenue", "Marketplace Analytics", 9),
    ("marketplace_revenue", "Business Intelligence", 9),
)

PHASE9_ENGINE_PACKAGES: Final[tuple[str, ...]] = (
    "marketplace_ecosystem",
    "creator_platform",
    "community_platform",
    "template_store",
    "plugin_framework",
    "public_api_platform",
    "agent_orchestration",
    "enterprise_automation",
    "marketplace_revenue",
)

REGRESSION_PHASES: Final[tuple[int, ...]] = (1, 2, 3, 4, 5, 6, 7, 8, 9)

REGRESSION_CAPABILITIES: Final[tuple[str, ...]] = (
    "authentication",
    "authorization",
    "organizations",
    "workspaces",
    "projects",
    "ai_generation",
    "video_engine",
    "asset_library",
    "marketplace",
    "billing",
    "credits",
    "subscriptions",
    "api_gateway",
    "developer_platform",
    "plugin_framework",
    "ai_agents",
    "automation",
    "analytics",
)

PRODUCTION_ENDPOINTS: Final[tuple[tuple[str, str], ...]] = (
    ("GET", "/api/ready"),
    ("GET", "/api/router/status"),
    ("GET", "/api/video-engine/version"),
    ("GET", "/api/projects"),
    ("GET", "/api/assets"),
    ("GET", "/api/billing/plans"),
    ("GET", "/api/billing/subscription"),
    ("GET", "/api/marketplace"),
    ("GET", "/api/plugins"),
    ("GET", "/api/developers"),
    ("GET", "/api/automation"),
    ("GET", "/api/analytics"),
    ("GET", "/api/admin/system"),
)

LOAD_BATCHES: Final[tuple[int, ...]] = (50, 100, 250, 500, 1000)

SECURITY_CHECKS: Final[tuple[str, ...]] = (
    "rbac",
    "organization_isolation",
    "workspace_isolation",
    "api_security",
    "plugin_security",
    "developer_api_security",
    "marketplace_ownership",
    "webhook_validation",
    "financial_data_protection",
    "audit_logging",
)

QUALITY_WEIGHTS: Final[dict[str, float]] = {
    "enterprise_quality": 1.0,
    "security": 1.0,
    "performance": 1.0,
    "marketplace": 1.0,
    "developer_platform": 1.0,
    "scalability": 1.0,
    "production_readiness": 1.0,
}


def clamp_score(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return round(max(lo, min(hi, value)), 2)


def aggregate_scores(scores: dict[str, float]) -> float:
    if not scores:
        return 0.0
    return clamp_score(sum(scores.values()) / len(scores))
