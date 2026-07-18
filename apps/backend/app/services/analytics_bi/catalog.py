"""Report types, metric keys, and KPI definitions."""

from __future__ import annotations

from typing import Final

REPORT_TYPES: Final[tuple[str, ...]] = (
    "daily",
    "weekly",
    "monthly",
    "organization",
    "workspace",
    "team",
    "user",
    "ai_usage",
    "performance",
    "storage",
)

ANALYTICS_CATEGORIES: Final[tuple[str, ...]] = (
    "organization",
    "workspace",
    "team",
    "user",
    "project",
    "ai",
    "storage",
    "api",
    "export",
    "download",
    "asset",
    "provider",
    "queue",
)

KPI_DEFS: Final[list[dict]] = [
    {"key": "active_users", "label": "Active Users", "unit": "users", "target": 100},
    {"key": "ai_success_rate", "label": "AI Success Rate", "unit": "%", "target": 95},
    {"key": "avg_generation_ms", "label": "Avg Generation Time", "unit": "ms", "target": 5000},
    {"key": "active_projects", "label": "Active Projects", "unit": "projects", "target": 50},
    {"key": "storage_gb", "label": "Storage Used", "unit": "GB", "target": 100},
    {"key": "api_error_rate", "label": "API Error Rate", "unit": "%", "target": 1},
]


def normalize_report_type(value: str) -> str:
    key = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "day": "daily",
        "week": "weekly",
        "month": "monthly",
        "org": "organization",
        "ai": "ai_usage",
        "ai-usage": "ai_usage",
        "perf": "performance",
    }
    key = aliases.get(key, key)
    if key not in REPORT_TYPES:
        raise ValueError(f"unsupported report type: {value}")
    return key
