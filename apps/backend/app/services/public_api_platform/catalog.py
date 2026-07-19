"""Public API surfaces, SDK languages, OAuth scopes, versioning policies."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from typing import Any, Final

PUBLIC_API_SURFACES: Final[tuple[str, ...]] = (
    "authentication",
    "users",
    "organizations",
    "workspaces",
    "projects",
    "assets",
    "ai_generation",
    "billing",
    "marketplace",
    "analytics",
)

SDK_LANGUAGES: Final[tuple[str, ...]] = (
    "javascript",
    "typescript",
    "python",
    "php",
    "csharp",
    "java",
    "go",
    "rest",
)

OAUTH_GRANT_TYPES: Final[tuple[str, ...]] = (
    "authorization_code",
    "client_credentials",
    "refresh_token",
)

OAUTH_SCOPES: Final[tuple[str, ...]] = (
    "openid",
    "profile",
    "email",
    "org.read",
    "org.write",
    "workspace.read",
    "workspace.write",
    "project.read",
    "project.write",
    "asset.read",
    "asset.write",
    "ai.generate",
    "billing.read",
    "marketplace.read",
    "analytics.read",
    "webhooks.manage",
)

API_VERSION_STATUSES: Final[tuple[str, ...]] = (
    "active",
    "deprecated",
    "sunset",
)

TOKEN_STATUSES: Final[tuple[str, ...]] = ("active", "revoked", "expired")

DEFAULT_RATE_LIMIT_PER_MINUTE: Final[int] = 120
TOKEN_PREFIX: Final[str] = "rtas_sk_"
CLIENT_ID_PREFIX: Final[str] = "rtas_cid_"
# Deprecated constant — use public_api_hash_secret() (env-backed).
HASH_SECRET: Final[str] = "rtas-public-api-key-v1"

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_VERSION_PATH_RE = re.compile(r"^v\d+$")


def is_semver(value: str) -> bool:
    return bool(_SEMVER_RE.match(value or ""))


def is_api_version_label(value: str) -> bool:
    return bool(_VERSION_PATH_RE.match(value or ""))


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug or "app"


def generate_secret(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def generate_api_key() -> str:
    return f"{TOKEN_PREFIX}{secrets.token_urlsafe(32)}"


def generate_client_id() -> str:
    return f"{CLIENT_ID_PREFIX}{secrets.token_hex(8)}"


def hash_secret(value: str) -> str:
    from app.core.signing_secrets import public_api_hash_secret

    return hmac.new(
        public_api_hash_secret().encode("utf-8"),
        (value or "").encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_secret(value: str, digest: str) -> bool:
    if not value or not digest:
        return False
    return hmac.compare_digest(hash_secret(value), digest)


def mask_secret(value: str) -> str:
    if not value or len(value) < 12:
        return "****"
    return f"{value[:8]}…{value[-4:]}"


def playground_metadata() -> dict[str, Any]:
    return {
        "baseUrl": "/api/v1",
        "auth": ["api_key", "oauth2_client_credentials", "oauth2_authorization_code"],
        "surfaces": [
            {"key": key, "path": f"/api/v1/{key.replace('_', '-')}"}
            for key in PUBLIC_API_SURFACES
        ],
        "sdkLanguages": list(SDK_LANGUAGES),
        "rateLimitPerMinute": DEFAULT_RATE_LIMIT_PER_MINUTE,
    }


def openapi_skeleton(version: str = "v1") -> dict[str, Any]:
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "RTAS Studio AI Public API",
            "version": version,
            "description": "Enterprise public API platform for RTAS Studio AI",
        },
        "servers": [{"url": f"/api/{version}"}],
        "paths": {
            f"/{surface.replace('_', '-')}": {
                "get": {
                    "summary": f"{surface} API",
                    "tags": [surface],
                    "security": [{"ApiKeyAuth": []}, {"OAuth2": []}],
                }
            }
            for surface in PUBLIC_API_SURFACES
        },
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-Api-Key",
                },
                "OAuth2": {
                    "type": "oauth2",
                    "flows": {
                        "clientCredentials": {
                            "tokenUrl": "/api/oauth/token",
                            "scopes": {s: s for s in OAUTH_SCOPES},
                        },
                        "authorizationCode": {
                            "authorizationUrl": "/api/oauth/authorize",
                            "tokenUrl": "/api/oauth/token",
                            "scopes": {s: s for s in OAUTH_SCOPES},
                        },
                    },
                },
            }
        },
    }
