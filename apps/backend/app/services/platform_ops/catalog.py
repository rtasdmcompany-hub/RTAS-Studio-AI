"""Platform setting categories, feature flags, and config namespaces."""

from __future__ import annotations

from typing import Any, Final

SETTING_CATEGORIES: Final[tuple[str, ...]] = (
    "general",
    "security",
    "billing",
    "email",
    "storage",
    "providers",
    "backup",
    "maintenance",
)

CONFIG_NAMESPACES: Final[tuple[str, ...]] = (
    "global",
    "environment",
    "providers",
    "storage",
    "email",
    "billing",
    "security",
    "backup",
)

DEFAULT_FEATURE_FLAGS: Final[list[dict[str, Any]]] = [
    {"key": "ai_generation", "enabled": True, "description": "AI generation pipelines"},
    {"key": "asset_library", "enabled": True, "description": "Enterprise asset library"},
    {"key": "analytics_bi", "enabled": True, "description": "Analytics & BI dashboards"},
    {"key": "version_control", "enabled": True, "description": "Project version control"},
    {"key": "maintenance_banner", "enabled": False, "description": "Show maintenance banner"},
    {"key": "billing_enforcement", "enabled": True, "description": "Enforce billing limits"},
]

DEFAULT_SETTINGS: Final[list[dict[str, Any]]] = [
    {"key": "platform.name", "category": "general", "value": "RTAS Studio AI", "isSecret": False},
    {"key": "platform.supportEmail", "category": "email", "value": "support@rtas.ai", "isSecret": False},
    {"key": "security.requireMfa", "category": "security", "value": False, "isSecret": False},
    {"key": "security.sessionTtlHours", "category": "security", "value": 24, "isSecret": False},
    {"key": "billing.currency", "category": "billing", "value": "USD", "isSecret": False},
    {"key": "storage.maxGbPerOrg", "category": "storage", "value": 100, "isSecret": False},
    {"key": "providers.default", "category": "providers", "value": "fal", "isSecret": False},
    {"key": "backup.enabled", "category": "backup", "value": True, "isSecret": False},
    {"key": "maintenance.enabled", "category": "maintenance", "value": False, "isSecret": False},
]

DEFAULT_SCHEDULED_TASKS: Final[list[dict[str, Any]]] = [
    {"name": "cleanup_expired_sessions", "cronExpr": "0 * * * *", "status": "idle"},
    {"name": "aggregate_analytics", "cronExpr": "15 * * * *", "status": "idle"},
    {"name": "rotate_system_logs", "cronExpr": "0 2 * * *", "status": "idle"},
    {"name": "health_probe", "cronExpr": "*/5 * * * *", "status": "idle"},
]

SENSITIVE_SETTING_KEYS: Final[frozenset[str]] = frozenset(
    {
        "providers.apiKey",
        "email.smtpPassword",
        "billing.secretKey",
        "security.signingKey",
    }
)
