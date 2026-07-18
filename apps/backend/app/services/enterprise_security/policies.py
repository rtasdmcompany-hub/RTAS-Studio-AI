"""Security Policy Manager."""

from __future__ import annotations

from typing import Any

from app.services.enterprise_security import store
from app.services.enterprise_security.models import SecurityPolicy, new_id
from app.services.enterprise_security.version import (
    DEFAULT_RATE_LIMIT_PER_MINUTE,
    DEFAULT_RETENTION_DAYS,
    JWT_TTL_SEC,
)


def ensure_default_policies() -> list[SecurityPolicy]:
    existing = store.all_policies()
    if existing:
        return existing
    defaults = [
        SecurityPolicy(
            policy_id=new_id("pol"),
            name="authentication",
            rules={
                "jwt_ttl_sec": JWT_TTL_SEC,
                "methods": ["jwt", "session", "api_key", "service_account"],
                "rbac_roles": ["admin", "team", "user", "service"],
            },
        ),
        SecurityPolicy(
            policy_id=new_id("pol"),
            name="api_security",
            rules={
                "rate_limit_per_minute": DEFAULT_RATE_LIMIT_PER_MINUTE,
                "require_signature": False,
                "csrf_on_session": True,
                "replay_protection": True,
                "secure_headers": True,
            },
        ),
        SecurityPolicy(
            policy_id=new_id("pol"),
            name="data_retention",
            rules={
                "audit_retention_days": DEFAULT_RETENTION_DAYS,
                "secure_logging": True,
                "privacy_controls": True,
            },
        ),
        SecurityPolicy(
            policy_id=new_id("pol"),
            name="secrets",
            rules={
                "source": "environment_variables_only",
                "hardcoded_forbidden": True,
            },
        ),
    ]
    for p in defaults:
        store.save_policy(p)
    return defaults


def list_policies() -> list[dict[str, Any]]:
    return [p.to_dict() for p in ensure_default_policies()]


def get_policy(name: str) -> SecurityPolicy | None:
    for p in ensure_default_policies():
        if p.name == name:
            return p
    return None


def update_policy(name: str, rules: dict[str, Any], *, enabled: bool = True) -> dict[str, Any]:
    pol = get_policy(name)
    if not pol:
        pol = SecurityPolicy(policy_id=new_id("pol"), name=name, rules=rules, enabled=enabled)
    else:
        pol.rules.update(rules)
        pol.enabled = enabled
    store.save_policy(pol)
    return pol.to_dict()
