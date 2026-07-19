"""Plugin Framework, Extension SDK & Third-Party Integration APIs — Phase 9 Sprint 5."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import plugin_framework as pf_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

plugins_router = APIRouter(prefix="/plugins", tags=["plugin-framework"])
integrations_router = APIRouter(prefix="/integrations", tags=["integrations"])


def _auth(secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=secret)


def _svc():
    return pf_svc.get_plugin_framework_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Plugin framework operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class PluginRegisterRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str | None = None
    description: str = ""
    manifest: dict[str, Any] = Field(default_factory=dict)
    signature: str = ""
    publisher_key: str = Field("", alias="publisherKey")
    model_config = {"populate_by_name": True}


class PluginUpdateRequest(BaseModel):
    description: str | None = None
    status: str | None = None
    manifest: dict[str, Any] | None = None
    signature: str | None = None
    model_config = {"populate_by_name": True}


class PluginInstallRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    plugin_id: str = Field(..., alias="pluginId")
    workspace_id: str | None = Field(None, alias="workspaceId")
    version: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    secrets_ref: str = Field("", alias="secretsRef")
    model_config = {"populate_by_name": True}


class PluginUninstallRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    plugin_id: str = Field(..., alias="pluginId")
    workspace_id: str | None = Field(None, alias="workspaceId")
    model_config = {"populate_by_name": True}


class VersionPublishRequest(BaseModel):
    version: str
    changelog: str = ""
    manifest: dict[str, Any] | None = None
    signature: str = ""
    model_config = {"populate_by_name": True}


class ConfigUpdateRequest(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)
    secrets_ref: str | None = Field(None, alias="secretsRef")
    model_config = {"populate_by_name": True}


class IntegrationConnectRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    provider: str
    workspace_id: str | None = Field(None, alias="workspaceId")
    display_name: str = Field("", alias="displayName")
    credentials_ref: str = Field(..., alias="credentialsRef")
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class SdkEventRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    plugin_id: str = Field(..., alias="pluginId")
    event_type: str = Field("custom", alias="eventType")
    channel: str = "plugin.lifecycle"
    payload: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class ManifestValidateRequest(BaseModel):
    manifest: dict[str, Any] = Field(default_factory=dict)
    signature: str = ""
    publisher_key: str = Field("", alias="publisherKey")
    model_config = {"populate_by_name": True}


# --- Static plugin routes (before /{plugin_id}) ---


@plugins_router.get("")
async def plugins_root():
    return _svc().status()


@plugins_router.get("/status")
async def plugin_framework_status():
    return _svc().status()


@plugins_router.get("/sdk")
async def sdk_metadata():
    return {"ok": True, "sdk": _svc().sdk.sdk_metadata()}


@plugins_router.post("/sdk/validate")
async def validate_manifest(body: ManifestValidateRequest):
    try:
        result = _svc().sdk.validate_manifest(body.manifest)
        if body.signature:
            sig = _svc().sdk.verify_signature(
                body.manifest, body.signature, body.publisher_key
            )
            result["signature"] = sig
        return result
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.post("/sdk/events")
async def publish_sdk_event(
    body: SdkEventRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().sdk.publish_event(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.get("/sdk/events")
async def list_sdk_events(
    organization_id: str = Query(..., alias="organizationId"),
    plugin_id: str | None = Query(None, alias="pluginId"),
    channel: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().sdk.list_events(
            actor_id=actor,
            organization_id=organization_id,
            plugin_id=plugin_id,
            channel=channel,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.post("/register")
async def register_plugin(
    body: PluginRegisterRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().framework.register(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.post("/install")
async def install_plugin(
    body: PluginInstallRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().installation.install(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.post("/uninstall")
async def uninstall_plugin(
    body: PluginUninstallRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().installation.uninstall(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.get("/installed")
async def list_installed_plugins(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().installation.list_installed(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.post("/installations/{install_id}/enable")
async def enable_plugin(
    install_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().installation.enable(install_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.post("/installations/{install_id}/disable")
async def disable_plugin(
    install_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().installation.disable(install_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.patch("/installations/{install_id}/config")
async def update_installation_config(
    install_id: str,
    body: ConfigUpdateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().installation.update_config(
            install_id,
            body.model_dump(by_alias=True, exclude_unset=True),
            actor_id=actor,
        )
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.get("/installations/{install_id}/permissions")
async def list_installation_permissions(
    install_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().permissions.list_for_installation(
            install_id, actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Plugin CRUD ---


@plugins_router.get("")
async def list_plugins(
    organization_id: str = Query(..., alias="organizationId"),
    plugin_type: str | None = Query(None, alias="pluginType"),
    status: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().registry.list(
            actor_id=actor,
            organization_id=organization_id,
            plugin_type=plugin_type,
            status=status,
        )
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.get("/{plugin_id}")
async def get_plugin(
    plugin_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().framework.get(plugin_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.patch("/{plugin_id}")
async def update_plugin(
    plugin_id: str,
    body: PluginUpdateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().framework.update(
            plugin_id,
            body.model_dump(by_alias=True, exclude_unset=True),
            actor_id=actor,
        )
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.delete("/{plugin_id}")
async def delete_plugin(
    plugin_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().framework.delete(plugin_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@plugins_router.post("/{plugin_id}/versions")
async def publish_plugin_version(
    plugin_id: str,
    body: VersionPublishRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().framework.publish_version(
            plugin_id, body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Integrations ---


@integrations_router.post("/connect")
async def connect_integration(
    body: IntegrationConnectRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().integrations.connect(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@integrations_router.get("")
async def list_integrations(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    provider: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().integrations.list(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
            provider=provider,
        )
    except Exception as exc:
        raise _map(exc) from exc


@integrations_router.post("/{connection_id}/disconnect")
async def disconnect_integration(
    connection_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().integrations.disconnect(connection_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@integrations_router.get("/{connection_id}/logs")
async def integration_logs(
    connection_id: str,
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().integrations.logs(
            connection_id, actor_id=actor, limit=limit
        )
    except Exception as exc:
        raise _map(exc) from exc
