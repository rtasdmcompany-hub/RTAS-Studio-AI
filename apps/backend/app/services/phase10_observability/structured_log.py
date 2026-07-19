"""Structured JSON logging helpers with correlation support."""

from __future__ import annotations

import json
import logging
from typing import Any

_LOGGER = logging.getLogger("rtas.observability")

LOG_CATEGORIES = (
    "application",
    "api",
    "error",
    "audit",
    "security",
    "billing",
    "ai_generation",
    "queue",
)


def structured_log(
    message: str,
    *,
    category: str = "application",
    level: int = logging.INFO,
    correlation_id: str | None = None,
    component: str | None = None,
    **fields: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "msg": message,
        "category": category if category in LOG_CATEGORIES else "application",
        "correlation_id": correlation_id,
        "component": component,
        **fields,
    }
    # Drop nulls for cleaner sinks
    clean = {k: v for k, v in payload.items() if v is not None}
    _LOGGER.log(level, json.dumps(clean, default=str))
    return clean


def logging_architecture_report() -> dict[str, Any]:
    return {
        "ok": True,
        "structuredLogging": True,
        "logCorrelation": True,
        "traceability": True,
        "categories": list(LOG_CATEGORIES),
        "correlationHeaders": ["X-Correlation-Id", "X-Request-Id"],
        "middleware": "CorrelationIdMiddleware",
        "sinks": ["stdlib_logging_json", "monitoring_events", "security_audit", "auth_audit"],
    }
