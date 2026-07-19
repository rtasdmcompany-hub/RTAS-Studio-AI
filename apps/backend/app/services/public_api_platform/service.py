"""Enterprise Public API Platform, SDK & Developer Ecosystem — Phase 9 Sprint 6."""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from app.services.public_api_platform import store
from app.services.public_api_platform.catalog import (
    API_VERSION_STATUSES,
    DEFAULT_RATE_LIMIT_PER_MINUTE,
    OAUTH_GRANT_TYPES,
    OAUTH_SCOPES,
    PUBLIC_API_SURFACES,
    SDK_LANGUAGES,
    generate_api_key,
    generate_client_id,
    generate_secret,
    hash_secret,
    is_api_version_label,
    is_semver,
    mask_secret,
    openapi_skeleton,
    playground_metadata,
    slugify,
    verify_secret,
)
from app.services.public_api_platform.models import (
    ApiApplicationRecord,
    ApiTokenRecord,
    ApiUsageLogRecord,
    ApiVersionRecord,
    DeveloperAccountRecord,
    OAuthClientRecord,
    SdkReleaseRecord,
    WebhookSubscriptionRecord,
    new_id,
)
from app.services.public_api_platform.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validation():
    from app.services.multi_tenant.validation import ValidationError, require_non_empty

    return ValidationError, require_non_empty


def _auth_errors():
    from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError

    return ForbiddenError, NotFoundError


def _require_access(**kwargs: Any) -> None:
    from app.services.enterprise_auth.middleware import require_access

    require_access(**kwargs)


def _audit(action: str, actor_id: str, detail: str | None = None, **meta: Any) -> None:
    from app.services.enterprise_auth.audit import log_auth_event

    log_auth_event(
        action, actor_id=actor_id, success=True, detail=detail or action, metadata=meta
    )


def _require_member(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id, organization_id=organization_id, permission="org.read"
    )


def _require_manager(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id, organization_id=organization_id, permission="org.update"
    )


def _validate_redirect_uri(uri: str) -> None:
    ValidationError, _ = _validation()
    parsed = urlparse(uri)
    if parsed.scheme not in ("https", "http"):
        raise ValidationError(f"invalid redirect URI scheme: {uri}")
    if not parsed.netloc:
        raise ValidationError(f"invalid redirect URI: {uri}")
    if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1"):
        raise ValidationError("http redirect URIs are only allowed for localhost")


class ApiVersioningEngine:
    """API version control, deprecation, routing, and request validation."""

    def ensure_defaults(self) -> None:
        if store.list_versions():
            return
        store.save_version(
            ApiVersionRecord(
                id=new_id("apv_"),
                version="v1",
                status="active",
                changelog="Initial public API release",
                compatibility={"backwardCompatible": True},
            )
        )

    def list(self) -> dict[str, Any]:
        self.ensure_defaults()
        return {
            "ok": True,
            "versions": [v.to_dict() for v in store.list_versions()],
            "default": "v1",
        }

    def register(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            version = str(require_non_empty(payload.get("version"), "version")).lower()
            if not is_api_version_label(version):
                raise ValidationError("version must match vN (e.g. v1, v2)")
            if store.get_version_by_label(version) is not None:
                raise ValidationError(f"version {version} already exists")
            status = str(payload.get("status") or "active")
            if status not in API_VERSION_STATUSES:
                raise ValidationError(f"unknown version status: {status}")
            record = ApiVersionRecord(
                id=new_id("apv_"),
                version=version,
                status=status,
                changelog=str(payload.get("changelog") or ""),
                compatibility=dict(payload.get("compatibility") or {"backwardCompatible": True}),
            )
            store.save_version(record)
            _audit("public_api.version_registered", actor_id, version)
            return {"ok": True, "version": record.to_dict()}

    def deprecate(self, version: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            _, NotFoundError = _auth_errors()
            ValidationError, _ = _validation()
            record = store.get_version_by_label(version)
            if record is None:
                raise NotFoundError("api version not found")
            if record.status == "sunset":
                raise ValidationError("cannot deprecate a sunset version")
            record.status = "deprecated"
            record.deprecated_at = _now()
            store.save_version(record)
            _audit("public_api.version_deprecated", actor_id, version)
            return {"ok": True, "version": record.to_dict()}

    def resolve(self, version: str | None = None) -> dict[str, Any]:
        self.ensure_defaults()
        label = (version or "v1").lower()
        ValidationError, _ = _validation()
        record = store.get_version_by_label(label)
        if record is None:
            raise ValidationError(f"unknown API version: {label}")
        if record.status == "sunset":
            raise ValidationError(f"API version {label} has been sunset")
        return {
            "ok": True,
            "version": record.version,
            "status": record.status,
            "deprecated": record.status == "deprecated",
            "routePrefix": f"/api/{record.version}",
        }

    def validate_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        ValidationError, require_non_empty = _validation()
        version = str(payload.get("version") or "v1")
        surface = str(require_non_empty(payload.get("surface"), "surface"))
        if surface not in PUBLIC_API_SURFACES:
            raise ValidationError(f"unknown API surface: {surface}")
        resolved = self.resolve(version)
        method = str(payload.get("method") or "GET").upper()
        if method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            raise ValidationError(f"unsupported method: {method}")
        return {
            "ok": True,
            "valid": True,
            "version": resolved["version"],
            "surface": surface,
            "method": method,
            "deprecated": resolved["deprecated"],
        }


class ApiDocumentationEngine:
    """OpenAPI docs and API playground metadata."""

    def __init__(self, versioning: ApiVersioningEngine) -> None:
        self._versioning = versioning

    def openapi(self, version: str = "v1") -> dict[str, Any]:
        resolved = self._versioning.resolve(version)
        doc = openapi_skeleton(resolved["version"])
        return {"ok": True, "documentation": doc}

    def playground(self) -> dict[str, Any]:
        self._versioning.ensure_defaults()
        return {"ok": True, "playground": playground_metadata()}

    def surfaces(self) -> dict[str, Any]:
        return {
            "ok": True,
            "surfaces": [
                {
                    "key": s,
                    "name": s.replace("_", " ").title(),
                    "path": f"/api/v1/{s.replace('_', '-')}",
                }
                for s in PUBLIC_API_SURFACES
            ],
        }


class SdkDistributionEngine:
    """SDK release catalog for multi-language client SDKs."""

    def ensure_seed_releases(self) -> None:
        if store.list_sdk_releases(limit=1):
            return
        packages = {
            "javascript": "@rtas/studio-sdk",
            "typescript": "@rtas/studio-sdk",
            "python": "rtas-studio-sdk",
            "php": "rtas/studio-sdk",
            "csharp": "Rtas.Studio.Sdk",
            "java": "ai.rtas.studio.sdk",
            "go": "github.com/rtas/studio-sdk-go",
            "rest": "rtas-public-api",
        }
        for lang in SDK_LANGUAGES:
            checksum = hashlib.sha256(f"{lang}|1.0.0".encode()).hexdigest()
            store.save_sdk_release(
                SdkReleaseRecord(
                    id=new_id("sdk_"),
                    language=lang,
                    version="1.0.0",
                    package_name=packages[lang],
                    download_url=f"https://sdk.rtas.ai/{lang}/1.0.0",
                    checksum=checksum,
                    changelog="Initial SDK release architecture",
                )
            )

    def list(self, *, language: str | None = None, limit: int = 50) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            if language and language not in SDK_LANGUAGES:
                raise ValidationError(f"unsupported SDK language: {language}")
            self.ensure_seed_releases()
            items = store.list_sdk_releases(language=language, limit=limit)
            return {
                "ok": True,
                "count": len(items),
                "languages": list(SDK_LANGUAGES),
                "releases": [r.to_dict() for r in items],
            }

    def publish(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            language = str(require_non_empty(payload.get("language"), "language"))
            if language not in SDK_LANGUAGES:
                raise ValidationError(f"unsupported SDK language: {language}")
            version = str(require_non_empty(payload.get("version"), "version"))
            if not is_semver(version):
                raise ValidationError("version must be semver")
            package_name = str(
                require_non_empty(payload.get("packageName"), "packageName")
            )
            checksum = hashlib.sha256(
                f"{language}|{version}|{package_name}".encode()
            ).hexdigest()
            record = SdkReleaseRecord(
                id=new_id("sdk_"),
                language=language,
                version=version,
                package_name=package_name,
                download_url=str(payload.get("downloadUrl") or ""),
                checksum=checksum,
                changelog=str(payload.get("changelog") or ""),
            )
            store.save_sdk_release(record)
            _audit("public_api.sdk_published", actor_id, f"{language}@{version}")
            return {"ok": True, "release": record.to_dict()}

    def architecture(self) -> dict[str, Any]:
        return {
            "ok": True,
            "architecture": {
                "pattern": "thin-client-over-public-api",
                "transport": "REST",
                "auth": ["api_key", "oauth2"],
                "versioning": "path (/api/vN)",
                "languages": list(SDK_LANGUAGES),
                "extensible": True,
                "note": "Future SDKs integrate via the same REST surfaces without backend changes",
            },
        }


class OAuth2AuthEngine:
    """OAuth 2.0 clients, credentials, redirect URIs, and token validation."""

    def create_client(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            developer = _require_developer(actor_id, payload)
            name = str(require_non_empty(payload.get("name"), "name"))
            app_id = payload.get("applicationId")
            application: ApiApplicationRecord | None = None
            if app_id:
                application = store.get_application(str(app_id))
                if application is None or application.developer_id != developer.id:
                    _, NotFoundError = _auth_errors()
                    raise NotFoundError("application not found")
            else:
                application = ApiApplicationRecord(
                    id=new_id("app_"),
                    developer_id=developer.id,
                    organization_id=developer.organization_id,
                    name=name,
                    slug=slugify(name),
                    description=str(payload.get("description") or ""),
                )
                store.save_application(application)

            redirect_uris = [
                str(u) for u in (payload.get("redirectUris") or payload.get("redirect_uris") or [])
            ]
            for uri in redirect_uris:
                _validate_redirect_uri(uri)

            grant_types = [
                str(g)
                for g in (
                    payload.get("grantTypes")
                    or payload.get("grant_types")
                    or ["authorization_code", "client_credentials", "refresh_token"]
                )
            ]
            for g in grant_types:
                if g not in OAUTH_GRANT_TYPES:
                    raise ValidationError(f"unsupported grant type: {g}")
            if "authorization_code" in grant_types and not redirect_uris:
                raise ValidationError(
                    "redirectUris required for authorization_code grant"
                )

            scopes = [str(s) for s in (payload.get("scopes") or ["openid", "profile"])]
            for s in scopes:
                if s not in OAUTH_SCOPES:
                    raise ValidationError(f"unknown scope: {s}")

            plain_secret = generate_secret()
            client = OAuthClientRecord(
                id=new_id("ocl_"),
                developer_id=developer.id,
                application_id=application.id,
                organization_id=developer.organization_id,
                client_id=generate_client_id(),
                client_secret_hash=hash_secret(plain_secret),
                name=name,
                redirect_uris=redirect_uris,
                grant_types=grant_types,
                scopes=scopes,
            )
            store.save_oauth_client(client)
            _audit("public_api.oauth_client_created", actor_id, client.client_id)
            return {
                "ok": True,
                "client": client.to_dict(include_secret=True, secret=plain_secret),
            }

    def list_clients(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            developer = _require_developer_for_org(actor_id, organization_id)
            items = store.list_oauth_clients(developer_id=developer.id)
            return {
                "ok": True,
                "count": len(items),
                "clients": [c.to_dict() for c in items],
            }

    def authenticate_client(
        self, client_id: str, client_secret: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            client = store.get_oauth_by_client_id(client_id)
            if client is None or client.status != "active":
                raise ValidationError("invalid client credentials")
            if not verify_secret(client_secret, client.client_secret_hash):
                raise ValidationError("invalid client credentials")
            if "client_credentials" not in client.grant_types:
                raise ValidationError("client_credentials grant not enabled")
            return {
                "ok": True,
                "authenticated": True,
                "clientId": client.client_id,
                "organizationId": client.organization_id,
                "scopes": list(client.scopes),
                "tokenType": "Bearer",
                "accessToken": hash_secret(f"access|{client.client_id}|{time.time()}"),
                "expiresIn": 3600,
            }

    def validate_redirect(self, client_id: str, redirect_uri: str) -> dict[str, Any]:
        ValidationError, _ = _validation()
        client = store.get_oauth_by_client_id(client_id)
        if client is None:
            raise ValidationError("unknown client")
        if redirect_uri not in client.redirect_uris:
            raise ValidationError("redirect_uri not registered")
        return {"ok": True, "valid": True}


class DeveloperPortalEngine:
    """Developer accounts, applications, tokens, usage, webhooks."""

    def register(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            existing = store.get_developer_by_user(actor_id, org_id)
            if existing is not None:
                raise ValidationError("developer account already exists for this organization")
            display_name = str(
                payload.get("displayName")
                or payload.get("name")
                or f"Developer {actor_id[:8]}"
            )
            account = DeveloperAccountRecord(
                id=new_id("dev_"),
                user_id=actor_id,
                organization_id=org_id,
                display_name=display_name,
                email=str(payload.get("email") or ""),
                company=str(payload.get("company") or ""),
                website=str(payload.get("website") or ""),
            )
            store.save_developer(account)
            _audit("public_api.developer_registered", actor_id, account.id)
            return {"ok": True, "developer": account.to_dict()}

    def profile(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            developer = _require_developer_for_org(actor_id, organization_id)
            apps = store.list_applications(developer.id)
            return {
                "ok": True,
                "developer": developer.to_dict(),
                "applications": [a.to_dict() for a in apps],
                "playground": playground_metadata(),
            }

    def create_api_key(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            developer = _require_developer(actor_id, payload)
            name = str(require_non_empty(payload.get("name"), "name"))
            scopes = [str(s) for s in (payload.get("scopes") or ["org.read", "ai.generate"])]
            for s in scopes:
                if s not in OAUTH_SCOPES:
                    raise ValidationError(f"unknown scope: {s}")
            workspace_id = payload.get("workspaceId")
            ws_id = str(workspace_id) if workspace_id else None
            app_id = payload.get("applicationId")
            application_id = str(app_id) if app_id else None
            if application_id:
                app = store.get_application(application_id)
                if app is None or app.developer_id != developer.id:
                    _, NotFoundError = _auth_errors()
                    raise NotFoundError("application not found")
            plain = generate_api_key()
            token = ApiTokenRecord(
                id=new_id("atk_"),
                developer_id=developer.id,
                organization_id=developer.organization_id,
                application_id=application_id,
                workspace_id=ws_id,
                name=name,
                token_prefix=plain[:12],
                token_hash=hash_secret(plain),
                scopes=scopes,
                rate_limit_per_minute=int(
                    payload.get("rateLimitPerMinute") or DEFAULT_RATE_LIMIT_PER_MINUTE
                ),
            )
            store.save_token(token)
            _audit("public_api.api_key_created", actor_id, token.id)
            return {
                "ok": True,
                "apiKey": token.to_dict(include_token=True, token=plain),
            }

    def list_api_keys(
        self, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            developer = _require_developer_for_org(actor_id, organization_id)
            items = store.list_tokens(developer_id=developer.id)
            return {
                "ok": True,
                "count": len(items),
                "apiKeys": [t.to_dict() for t in items],
            }

    def revoke_api_key(self, token_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            _, NotFoundError = _auth_errors()
            ForbiddenError, _ = _auth_errors()
            token = store.get_token(token_id)
            if token is None or token.status == "revoked":
                raise NotFoundError("api key not found")
            developer = store.get_developer(token.developer_id)
            if developer is None or developer.user_id != actor_id:
                raise ForbiddenError("only the key owner can revoke this key")
            token.status = "revoked"
            token.revoked_at = _now()
            store.save_token(token)
            _audit("public_api.api_key_revoked", actor_id, token_id)
            return {"ok": True, "apiKeyId": token_id, "status": "revoked"}

    def usage(
        self, *, actor_id: str, organization_id: str, limit: int = 100
    ) -> dict[str, Any]:
        with store.timed_op():
            developer = _require_developer_for_org(actor_id, organization_id)
            logs = store.list_usage(developer_id=developer.id, limit=limit)
            by_surface: dict[str, int] = {}
            for log in logs:
                by_surface[log.surface] = by_surface.get(log.surface, 0) + 1
            return {
                "ok": True,
                "developerId": developer.id,
                "count": len(logs),
                "bySurface": by_surface,
                "logs": [l.to_dict() for l in logs],
            }

    def register_webhook(
        self, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            developer = _require_developer(actor_id, payload)
            target_url = str(require_non_empty(payload.get("targetUrl"), "targetUrl"))
            _validate_redirect_uri(target_url)
            events = [str(e) for e in (payload.get("events") or ["api.request"])]
            secret = generate_secret(16)
            hook = WebhookSubscriptionRecord(
                id=new_id("whk_"),
                developer_id=developer.id,
                organization_id=developer.organization_id,
                application_id=str(payload["applicationId"])
                if payload.get("applicationId")
                else None,
                target_url=target_url,
                events=events,
                secret_hash=hash_secret(secret),
            )
            store.save_webhook(hook)
            _audit("public_api.webhook_registered", actor_id, hook.id)
            return {
                "ok": True,
                "webhook": hook.to_dict(),
                "signingSecret": secret,
            }

    def list_webhooks(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            developer = _require_developer_for_org(actor_id, organization_id)
            items = store.list_webhooks(developer.id)
            return {
                "ok": True,
                "count": len(items),
                "webhooks": [w.to_dict() for w in items],
            }


class PublicApiGatewayEngine:
    """Public API gateway: auth validation, rate limits, surface routing, usage."""

    def __init__(
        self,
        portal: DeveloperPortalEngine,
        oauth: OAuth2AuthEngine,
        versioning: ApiVersioningEngine,
    ) -> None:
        self._portal = portal
        self._oauth = oauth
        self._versioning = versioning

    def authenticate_api_key(self, api_key: str) -> dict[str, Any]:
        ValidationError, _ = _validation()
        token = store.get_token_by_hash(hash_secret(api_key))
        if token is None or token.status != "active":
            raise ValidationError("invalid api key")
        if token.expires_at and token.expires_at < _now():
            token.status = "expired"
            store.save_token(token)
            raise ValidationError("api key expired")
        if not store.check_rate_limit(
            f"token:{token.id}", token.rate_limit_per_minute
        ):
            raise ValidationError("rate limit exceeded")
        token.last_used_at = _now()
        store.save_token(token)
        return {
            "ok": True,
            "authenticated": True,
            "tokenId": token.id,
            "developerId": token.developer_id,
            "organizationId": token.organization_id,
            "workspaceId": token.workspace_id,
            "scopes": list(token.scopes),
            "authType": "api_key",
        }

    def dispatch(self, payload: dict[str, Any], *, actor_id: str = "") -> dict[str, Any]:
        """Route a public API request through versioning, auth, and usage logging."""
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            start = time.perf_counter()
            validated = self._versioning.validate_request(payload)
            surface = validated["surface"]
            api_key = payload.get("apiKey") or payload.get("api_key")
            client_id = payload.get("clientId")
            client_secret = payload.get("clientSecret")
            auth: dict[str, Any]
            if api_key:
                auth = self.authenticate_api_key(str(api_key))
            elif client_id and client_secret:
                auth = self._oauth.authenticate_client(
                    str(client_id), str(client_secret)
                )
                auth["authType"] = "oauth2_client_credentials"
                auth["tokenId"] = None
                auth["developerId"] = ""
                client = store.get_oauth_by_client_id(str(client_id))
                if client:
                    auth["developerId"] = client.developer_id
            else:
                raise ValidationError("apiKey or OAuth client credentials required")

            required_scope = str(payload.get("requiredScope") or "")
            if required_scope and required_scope not in auth.get("scopes", []):
                ForbiddenError, _ = _auth_errors()
                raise ForbiddenError(f"missing required scope: {required_scope}")

            org_id = str(auth.get("organizationId") or "")
            workspace_id = payload.get("workspaceId") or auth.get("workspaceId")
            if workspace_id and auth.get("workspaceId") and str(workspace_id) != str(
                auth["workspaceId"]
            ):
                ForbiddenError, _ = _auth_errors()
                raise ForbiddenError("workspace isolation violation")

            latency = (time.perf_counter() - start) * 1000
            developer_id = str(auth.get("developerId") or "")
            if developer_id:
                store.save_usage(
                    ApiUsageLogRecord(
                        id=new_id("aul_"),
                        developer_id=developer_id,
                        organization_id=org_id,
                        token_id=auth.get("tokenId"),
                        client_id=str(client_id) if client_id else None,
                        surface=surface,
                        method=validated["method"],
                        path=str(
                            payload.get("path")
                            or f"/api/{validated['version']}/{surface.replace('_', '-')}"
                        ),
                        status_code=200,
                        latency_ms=round(latency, 3),
                        version=validated["version"],
                        workspace_id=str(workspace_id) if workspace_id else None,
                    )
                )
            return {
                "ok": True,
                "routed": True,
                "surface": surface,
                "version": validated["version"],
                "authType": auth.get("authType"),
                "organizationId": org_id,
                "workspaceId": workspace_id,
                "deprecated": validated["deprecated"],
                "latencyMs": round(latency, 3),
                "response": {
                    "surface": surface,
                    "message": f"{surface} public API acknowledged",
                },
            }

    def catalog(self) -> dict[str, Any]:
        return {
            "ok": True,
            "surfaces": list(PUBLIC_API_SURFACES),
            "defaultVersion": "v1",
            "authMethods": ["api_key", "oauth2"],
            "rateLimitPerMinute": DEFAULT_RATE_LIMIT_PER_MINUTE,
        }


def _require_developer(actor_id: str, payload: dict[str, Any]) -> DeveloperAccountRecord:
    ValidationError, require_non_empty = _validation()
    org_id = str(require_non_empty(payload.get("organizationId"), "organizationId"))
    return _require_developer_for_org(actor_id, org_id)


def _require_developer_for_org(
    actor_id: str, organization_id: str
) -> DeveloperAccountRecord:
    _require_member(actor_id=actor_id, organization_id=organization_id)
    _, NotFoundError = _auth_errors()
    developer = store.get_developer_by_user(actor_id, organization_id)
    if developer is None:
        raise NotFoundError("developer account not found; register first")
    return developer


class PublicApiPlatformFacade:
    """Facade combining all public API platform engines."""

    def __init__(self) -> None:
        self.versioning = ApiVersioningEngine()
        self.docs = ApiDocumentationEngine(self.versioning)
        self.sdk = SdkDistributionEngine()
        self.oauth = OAuth2AuthEngine()
        self.portal = DeveloperPortalEngine()
        self.gateway = PublicApiGatewayEngine(self.portal, self.oauth, self.versioning)
        self.versioning.ensure_defaults()
        self.sdk.ensure_seed_releases()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "publicApiGateway": "ready",
                "developerPortal": "ready",
                "sdkDistribution": "ready",
                "oauth2Authentication": "ready",
                "apiVersioning": "ready",
                "apiDocumentation": "ready",
            },
            "surfaces": list(PUBLIC_API_SURFACES),
            "sdkLanguages": list(SDK_LANGUAGES),
            "stats": store.metrics(),
        }


_service: PublicApiPlatformFacade | None = None


def get_public_api_platform_service() -> PublicApiPlatformFacade:
    global _service
    if _service is None:
        _service = PublicApiPlatformFacade()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    _service = None


get_engine = get_public_api_platform_service
