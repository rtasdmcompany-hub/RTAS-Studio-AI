"""Public API Platform, SDK & Developer Ecosystem APIs — Phase 9 Sprint 6."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import public_api_platform as pap_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

developers_router = APIRouter(prefix="/developers", tags=["developers"])
oauth_router = APIRouter(prefix="/oauth", tags=["oauth"])
api_keys_router = APIRouter(prefix="/api-keys", tags=["api-keys"])
sdk_router = APIRouter(prefix="/sdk", tags=["sdk"])
developer_usage_router = APIRouter(prefix="/developer", tags=["developer-portal"])
public_api_router = APIRouter(prefix="/public-api", tags=["public-api"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return pap_svc.get_public_api_platform_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Public API platform operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class DeveloperRegisterRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    display_name: str = Field("", alias="displayName")
    email: str = ""
    company: str = ""
    website: str = ""
    model_config = {"populate_by_name": True}


class OAuthClientRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    application_id: str | None = Field(None, alias="applicationId")
    description: str = ""
    redirect_uris: list[str] = Field(default_factory=list, alias="redirectUris")
    grant_types: list[str] | None = Field(None, alias="grantTypes")
    scopes: list[str] | None = None
    model_config = {"populate_by_name": True}


class OAuthTokenRequest(BaseModel):
    client_id: str = Field(..., alias="clientId")
    client_secret: str = Field(..., alias="clientSecret")
    grant_type: str = Field("client_credentials", alias="grantType")
    model_config = {"populate_by_name": True}


class ApiKeyCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    application_id: str | None = Field(None, alias="applicationId")
    workspace_id: str | None = Field(None, alias="workspaceId")
    scopes: list[str] | None = None
    rate_limit_per_minute: int | None = Field(None, alias="rateLimitPerMinute")
    model_config = {"populate_by_name": True}


class WebhookRegisterRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    target_url: str = Field(..., alias="targetUrl")
    events: list[str] = Field(default_factory=list)
    application_id: str | None = Field(None, alias="applicationId")
    model_config = {"populate_by_name": True}


class GatewayDispatchRequest(BaseModel):
    surface: str
    version: str = "v1"
    method: str = "GET"
    path: str = ""
    api_key: str | None = Field(None, alias="apiKey")
    client_id: str | None = Field(None, alias="clientId")
    client_secret: str | None = Field(None, alias="clientSecret")
    workspace_id: str | None = Field(None, alias="workspaceId")
    required_scope: str = Field("", alias="requiredScope")
    model_config = {"populate_by_name": True}


# --- Developers ---


@developers_router.get("/status")
async def developers_status():
    return _svc().status()


@developers_router.get("")
async def developers_root():
    return _svc().status()


@developers_router.post("/register")
async def register_developer(
    body: DeveloperRegisterRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().portal.register(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@developers_router.get("/profile")
async def developer_profile(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().portal.profile(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@developers_router.post("/webhooks")
async def register_webhook(
    body: WebhookRegisterRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().portal.register_webhook(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@developers_router.get("/webhooks")
async def list_webhooks(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().portal.list_webhooks(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- OAuth ---


@oauth_router.post("/client")
async def create_oauth_client(
    body: OAuthClientRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().oauth.create_client(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@oauth_router.get("/clients")
async def list_oauth_clients(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().oauth.list_clients(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@oauth_router.post("/token")
async def oauth_token(body: OAuthTokenRequest):
    try:
        if body.grant_type != "client_credentials":
            raise ValidationError("only client_credentials supported on this endpoint")
        return _svc().oauth.authenticate_client(body.client_id, body.client_secret)
    except Exception as exc:
        raise _map(exc) from exc


# --- API Keys ---


@api_keys_router.post("/create")
async def create_api_key(
    body: ApiKeyCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().portal.create_api_key(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@api_keys_router.get("")
async def list_api_keys(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().portal.list_api_keys(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@api_keys_router.delete("/{key_id}")
async def delete_api_key(
    key_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().portal.revoke_api_key(key_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


# --- Developer usage (spec path) ---


@developer_usage_router.get("/usage")
async def developer_usage(
    organization_id: str = Query(..., alias="organizationId"),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().portal.usage(
            actor_id=actor, organization_id=organization_id, limit=limit
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- SDK ---


@sdk_router.get("/releases")
async def sdk_releases(
    language: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    try:
        return _svc().sdk.list(language=language, limit=limit)
    except Exception as exc:
        raise _map(exc) from exc


@sdk_router.get("/architecture")
async def sdk_architecture():
    return _svc().sdk.architecture()


# --- Public API platform status / docs / gateway ---


@public_api_router.get("/status")
async def public_api_status():
    return _svc().status()


@public_api_router.get("/docs")
async def public_api_docs(version: str = Query("v1")):
    try:
        return _svc().docs.openapi(version)
    except Exception as exc:
        raise _map(exc) from exc


@public_api_router.get("/playground")
async def public_api_playground():
    return _svc().docs.playground()


@public_api_router.get("/versions")
async def list_api_versions():
    return _svc().versioning.list()


@public_api_router.post("/gateway/dispatch")
async def gateway_dispatch(
    body: GatewayDispatchRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().gateway.dispatch(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc
