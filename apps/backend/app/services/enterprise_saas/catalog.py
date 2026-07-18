"""Phase 7 module registry for final verification."""

from __future__ import annotations

from typing import Final

PHASE7_MODULES: Final[list[dict[str, str]]] = [
    {"key": "multi_tenant", "label": "Organizations / Workspaces / Teams / Members"},
    {"key": "enterprise_auth", "label": "Authentication / Authorization / Roles / Permissions"},
    {"key": "org_management", "label": "Organization / Workspace / Team Management"},
    {"key": "project_collaboration", "label": "Projects / Collaboration"},
    {"key": "asset_library", "label": "Asset Library"},
    {"key": "enterprise_comms", "label": "Notifications / Activity / Comments"},
    {"key": "version_control", "label": "Version Control / Reviews / Approvals"},
    {"key": "analytics_bi", "label": "Reporting / Analytics / Business Intelligence"},
    {"key": "platform_ops", "label": "Administration / Platform Operations"},
]

# Prefer */status probes for secret-only smoke; list routes often need X-Rtas-User-Id.
PRODUCTION_ENDPOINTS: Final[tuple[str, ...]] = (
    "/api/ready",
    "/api/providers",
    "/api/providers/status",
    "/api/router/status",
    "/api/jobs/status",
    "/api/projects/status",
    "/api/assets/status",
    "/api/notifications/status",
    "/api/analytics/status",
    "/api/admin/ops/status",
    "/api/versions/status",
    "/api/enterprise/status",
)
