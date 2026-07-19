"""Versioned legal policy catalog (references shared legal sources)."""

from __future__ import annotations

import hashlib
from typing import Any

# Canonical policy inventory — content lives in @rtas/shared; backend tracks versions.
POLICY_CATALOG: dict[str, dict[str, Any]] = {
    "privacy_policy": {
        "title": "Privacy Policy",
        "webPath": "/privacy",
        "source": "packages/shared/src/legal/privacy.ts",
        "lastUpdated": "July 2026",
        "frameworks": ["GDPR", "UK_GDPR", "CCPA", "CPRA", "PIPEDA"],
    },
    "terms_of_service": {
        "title": "Terms of Service",
        "webPath": "/terms",
        "source": "packages/shared/src/legal/terms.ts",
        "lastUpdated": "July 2026",
        "sections": ["subscriptions", "refunds", "AUP", "commercial_license", "copyright"],
    },
    "cookie_policy": {
        "title": "Cookie Policy",
        "webPath": "/cookies",
        "source": "packages/shared/src/legal/cookies.ts",
        "lastUpdated": "July 2026",
        "frameworks": ["ePrivacy", "GDPR", "UK_PECR"],
    },
    "acceptable_use_policy": {
        "title": "Acceptable Use Policy",
        "webPath": "/terms#aup",
        "source": "packages/shared/src/legal/terms.ts",
        "embeddedIn": "terms_of_service",
        "lastUpdated": "July 2026",
    },
    "refund_policy": {
        "title": "Refund Policy",
        "webPath": "/terms#refunds",
        "source": "packages/shared/src/legal/terms.ts",
        "embeddedIn": "terms_of_service",
        "lastUpdated": "July 2026",
    },
    "subscription_policy": {
        "title": "Subscription Policy",
        "webPath": "/terms#subscriptions",
        "source": "packages/shared/src/legal/terms.ts",
        "embeddedIn": "terms_of_service",
        "lastUpdated": "July 2026",
    },
    "copyright_notice": {
        "title": "Copyright Notice",
        "webPath": "/terms",
        "source": "packages/shared/src/legal/terms.ts",
        "notice": "© RTAS DIGITAL MARKETING COMPANY / RTAS GROUP OF COMPANIES",
        "lastUpdated": "July 2026",
    },
    "license_notice": {
        "title": "Proprietary License Notice",
        "webPath": "/terms",
        "source": "LICENSE",
        "license": "Proprietary — All Rights Reserved",
        "lastUpdated": "July 2026",
    },
}


def policy_fingerprint(policy_id: str) -> str:
    meta = POLICY_CATALOG.get(policy_id) or {}
    raw = f"{policy_id}:{meta.get('source')}:{meta.get('lastUpdated')}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def list_policies() -> dict[str, Any]:
    items = []
    for pid, meta in POLICY_CATALOG.items():
        items.append(
            {
                "id": pid,
                "fingerprint": policy_fingerprint(pid),
                **meta,
                "status": "published",
            }
        )
    return {
        "ok": True,
        "count": len(items),
        "policies": items,
        "required": list(POLICY_CATALOG.keys()),
    }
