"""RC-2 module and surface catalogs."""

from __future__ import annotations

from typing import Final

RC2_SURFACES: Final[tuple[str, ...]] = (
    "authentication",
    "organizations",
    "projects",
    "workspace",
    "ai_generation",
    "marketplace",
    "billing",
    "credits",
    "subscriptions",
    "developer_apis",
    "plugins",
    "automation",
    "analytics",
    "storage",
    "export",
    "download",
)

RC2_SURFACE_PACKAGES: Final[dict[str, tuple[str, ...]]] = {
    "authentication": ("app.services.enterprise_auth", "app.api.routes.access"),
    "organizations": ("app.services.org_management", "app.api.routes.organizations"),
    "projects": ("app.api.routes.projects",),
    "workspace": ("app.api.routes.workspaces",),
    "ai_generation": ("app.services.provider_orchestration", "app.api.routes.generate"),
    "marketplace": ("app.services.marketplace", "app.api.routes.marketplace"),
    "billing": ("app.services.billing", "app.api.routes.billing"),
    "credits": ("app.api.routes.credits",),
    "subscriptions": ("app.api.routes.billing",),
    "developer_apis": ("app.services.public_api_platform", "app.api.routes.public_api_platform"),
    "plugins": ("app.services.plugin_framework", "app.api.routes.plugin_framework"),
    "automation": ("app.services.enterprise_automation",),
    "analytics": ("app.services.analytics_bi", "app.api.routes.analytics"),
    "storage": ("app.services.storage",),
    "export": ("app.api.routes.export",),
    "download": ("app.api.routes.download",),
}

PROD_ENV_SURFACES: Final[tuple[str, ...]] = (
    "nextjs",
    "fastapi",
    "vercel",
    "supabase",
    "prisma",
    "redis",
    "storage",
    "ai_providers",
    "billing",
    "marketplace",
    "developer_platform",
)

DEPLOY_CHECKS: Final[tuple[str, ...]] = (
    "github",
    "build_pipeline",
    "deployment_scripts",
    "environment_loading",
    "migration_flow",
    "rollback_strategy",
    "release_pipeline",
)
