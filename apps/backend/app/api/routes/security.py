"""Enterprise Security, Compliance & Audit APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import enterprise_security as es

router = APIRouter(prefix="/security", tags=["enterprise-security"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class SecurityValidateRequest(BaseModel):
    actor_id: str | None = Field(None, alias="actorId")
    subject: str | None = None
    auth_method: str | None = Field(None, alias="authMethod")
    method: str | None = None
    credential: str | None = None
    token: str | None = None
    account_id: str | None = Field(None, alias="accountId")
    permission: str | None = None
    signature: str | None = None
    body: str | None = None
    timestamp: str | None = None
    csrf_token: str | None = Field(None, alias="csrfToken")
    session_token: str | None = Field(None, alias="sessionToken")
    origin: str | None = None
    nonce: str | None = None
    prompt: str | None = None
    track_action: str | None = Field(None, alias="trackAction")
    resource: str | None = None
    detail: str | None = None

    model_config = {"populate_by_name": True}

    def as_payload(self) -> dict[str, Any]:
        return self.model_dump(by_alias=False, exclude_none=True)


@router.get("/status")
async def security_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return es.get_security_engine().status()


@router.get("/audit")
async def security_audit(
    limit: int = Query(50, ge=1, le=500),
    action: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return es.get_security_engine().audit_logs(limit=limit, action=action)


@router.get("/events")
async def security_events(
    limit: int = Query(50, ge=1, le=500),
    severity: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return es.get_security_engine().events(limit=limit, severity=severity)


@router.get("/compliance")
async def security_compliance(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return es.get_security_engine().compliance()


@router.post("/validate")
async def security_validate(
    body: SecurityValidateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = es.get_security_engine()
    try:
        return engine.validate(body.as_payload())
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Security validate failed") from exc
