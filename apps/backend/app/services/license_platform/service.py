"""Enterprise License, API Access & Developer Platform Engine — Phase 8 Sprint 7."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.license_platform import store
from app.services.license_platform.catalog import (
    API_DOCS_METADATA,
    API_KEY_ACCESS,
    API_KEY_TYPES,
    API_SCOPES,
    LICENSE_DURATION_DAYS,
    LICENSE_STATUSES,
    LICENSE_TIERS,
    PAT_DEFAULT_EXPIRY_DAYS,
    RATE_LIMIT_POLICIES,
    SDK_METADATA,
    WEBHOOK_EVENTS,
    WEBHOOK_MAX_RETRIES,
    WEBHOOK_RETRY_BACKOFF_MINUTES,
    WORKSPACE_LIMIT_FRACTION,
    generate_license_key,
    generate_secret,
    rate_policy,
)
from app.services.license_platform.models import (
    ApiKey,
    ApiUsageRecord,
    License,
    LicenseHistoryEntry,
    PersonalAccessToken,
    RateLimitState,
    Webhook,
    WebhookDelivery,
    new_id,
)
from app.services.license_platform.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _validation():
    from app.services.multi_tenant.validation import ValidationError, require_non_empty

    return ValidationError, require_non_empty


def _auth_errors():
    from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError

    return ForbiddenError, NotFoundError


def _require_access(**kwargs: Any) -> None:
    from app.services.enterprise_auth.middleware import require_access

    require_access(**kwargs)


def _repo():
    from app.services.multi_tenant.repository import get_repository

    return get_repository()


def _audit(action: str, actor_id: str, detail: str | None = None, **meta: Any) -> None:
    from app.services.enterprise_auth.audit import log_auth_event

    log_auth_event(
        action,
        actor_id=actor_id,
        success=True,
        detail=detail or action,
        metadata=meta,
    )


def _require_read(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id,
        organization_id=organization_id,
        permission="org.read",
    )


def _require_manage(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id,
        organization_id=organization_id,
        permission="org.update",
    )


def _require_org_exists(organization_id: str) -> None:
    _, NotFoundError = _auth_errors()
    if _repo().get_organization(organization_id) is None:
        raise NotFoundError("organization not found")


def _history(
    lic: License, action: str, *, actor_id: str | None, detail: str = ""
) -> None:
    store.save_license_history(
        LicenseHistoryEntry(
            id=new_id("lich_"),
            license_id=lic.id,
            organization_id=lic.organization_id,
            action=action,
            tier=lic.tier,
            detail=detail,
            actor_id=actor_id,
        )
    )


class LicenseValidationEngine:
    """Validates license state; auto-expires stale licenses."""

    def refresh(self, lic: License) -> License:
        if (
            lic.status == "active"
            and lic.expires_at is not None
            and lic.expires_at <= _now()
        ):
            lic.status = "expired"
            lic.updated_at = _now()
            store.save_license(lic)
            _history(lic, "expired", actor_id=None, detail="license period ended")
        return lic

    def validate(self, license_key: str) -> dict[str, Any]:
        with store.timed_op():
            lic = store.get_license_by_key(license_key)
            if lic is None:
                return {"ok": True, "valid": False, "reason": "license not found"}
            lic = self.refresh(lic)
            valid = lic.status == "active"
            reason = "" if valid else f"license is {lic.status}"
            return {
                "ok": True,
                "valid": valid,
                "reason": reason,
                "tier": lic.tier,
                "status": lic.status,
                "expiresAt": lic.to_dict()["expiresAt"],
            }


class LicenseManagementEngine:
    def __init__(self) -> None:
        self.validator = LicenseValidationEngine()

    def activate(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_manage(actor_id=actor_id, organization_id=org_id)
            _require_org_exists(org_id)
            tier = str(payload.get("tier") or "free")
            if tier not in LICENSE_TIERS:
                raise ValidationError(f"unknown license tier: {tier}")

            existing = store.get_license_by_org(org_id)
            if existing is not None and existing.status == "active":
                raise ValidationError(
                    "organization already has an active license; renew or revoke first"
                )

            duration = LICENSE_DURATION_DAYS[tier]
            now = _now()
            lic = License(
                id=new_id("lic_"),
                organization_id=org_id,
                license_key=generate_license_key(),
                tier=tier,
                status="active",
                activated_at=now,
                expires_at=(now + timedelta(days=duration)) if duration else None,
                activated_by=actor_id,
                seats=int(payload.get("seats") or 1),
            )
            store.save_license(lic)
            _history(lic, "activated", actor_id=actor_id, detail=f"tier={tier}")
            _audit(
                "license.activated",
                actor_id,
                lic.license_key,
                organizationId=org_id,
                tier=tier,
            )
            result = lic.to_dict(mask_key=False)
            return {"ok": True, "license": result}

    def _get_owned(self, organization_id: str, actor_id: str) -> License:
        _, NotFoundError = _auth_errors()
        _require_read(actor_id=actor_id, organization_id=organization_id)
        lic = store.get_license_by_org(organization_id)
        if lic is None:
            raise NotFoundError("no license found for organization")
        return self.validator.refresh(lic)

    def status(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            lic = self._get_owned(organization_id, actor_id)
            history = store.list_license_history(organization_id, limit=20)
            return {
                "ok": True,
                "license": lic.to_dict(),
                "rateLimits": rate_policy(lic.tier),
                "history": [h.to_dict() for h in history],
            }

    def renew(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_manage(actor_id=actor_id, organization_id=org_id)
            lic = self._get_owned(org_id, actor_id)
            if lic.status == "revoked":
                raise ValidationError("cannot renew a revoked license")
            tier = str(payload.get("tier") or lic.tier)
            if tier not in LICENSE_TIERS:
                raise ValidationError(f"unknown license tier: {tier}")
            duration = LICENSE_DURATION_DAYS[tier]
            base = lic.expires_at if (lic.status == "active" and lic.expires_at and lic.expires_at > _now()) else _now()
            lic.tier = tier
            lic.status = "active"
            lic.suspended_at = None
            lic.expires_at = (base + timedelta(days=duration)) if duration else None
            lic.updated_at = _now()
            store.save_license(lic)
            _history(lic, "renewed", actor_id=actor_id, detail=f"tier={tier}")
            _audit(
                "license.renewed",
                actor_id,
                lic.license_key,
                organizationId=org_id,
                tier=tier,
            )
            return {"ok": True, "license": lic.to_dict()}

    def suspend(self, organization_id: str, *, actor_id: str, reason: str = "") -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _require_manage(actor_id=actor_id, organization_id=organization_id)
            lic = self._get_owned(organization_id, actor_id)
            if lic.status != "active":
                raise ValidationError(f"cannot suspend license in status {lic.status}")
            lic.status = "suspended"
            lic.suspended_at = _now()
            lic.updated_at = _now()
            store.save_license(lic)
            _history(lic, "suspended", actor_id=actor_id, detail=reason)
            _audit("license.suspended", actor_id, lic.license_key, organizationId=organization_id)
            return {"ok": True, "license": lic.to_dict()}

    def resume(self, organization_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _require_manage(actor_id=actor_id, organization_id=organization_id)
            lic = self._get_owned(organization_id, actor_id)
            if lic.status != "suspended":
                raise ValidationError(f"cannot resume license in status {lic.status}")
            lic.status = "active"
            lic.suspended_at = None
            lic.updated_at = _now()
            store.save_license(lic)
            _history(lic, "resumed", actor_id=actor_id)
            _audit("license.resumed", actor_id, lic.license_key, organizationId=organization_id)
            return {"ok": True, "license": lic.to_dict()}

    def revoke(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_manage(actor_id=actor_id, organization_id=org_id)
            lic = self._get_owned(org_id, actor_id)
            if lic.status == "revoked":
                raise ValidationError("license already revoked")
            lic.status = "revoked"
            lic.revoked_at = _now()
            lic.updated_at = _now()
            store.save_license(lic)
            _history(
                lic, "revoked", actor_id=actor_id, detail=str(payload.get("reason") or "")
            )
            _audit("license.revoked", actor_id, lic.license_key, organizationId=org_id)
            return {"ok": True, "license": lic.to_dict()}

    def history(self, *, actor_id: str, organization_id: str, limit: int = 100) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            items = store.list_license_history(organization_id, limit=limit)
            return {"ok": True, "count": len(items), "history": [h.to_dict() for h in items]}


class ApiKeyManagementEngine:
    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            key_type = str(payload.get("keyType") or "personal")
            if key_type not in API_KEY_TYPES:
                raise ValidationError(f"unknown key type: {key_type}")
            # Personal keys need only membership; org/workspace keys need manage rights.
            if key_type == "personal":
                _require_read(actor_id=actor_id, organization_id=org_id)
            else:
                _require_manage(actor_id=actor_id, organization_id=org_id)
            _require_org_exists(org_id)

            access = str(payload.get("access") or "full_access")
            if access not in API_KEY_ACCESS:
                raise ValidationError(f"unknown access level: {access}")
            scopes = [str(s) for s in (payload.get("scopes") or [])]
            if access == "scoped":
                if not scopes:
                    raise ValidationError("scoped keys require at least one scope")
                unknown = [s for s in scopes if s not in API_SCOPES]
                if unknown:
                    raise ValidationError(f"unknown scopes: {', '.join(unknown)}")
            elif access == "read_only":
                scopes = [s for s in API_SCOPES if s.endswith(":read")]
            else:
                scopes = list(API_SCOPES)

            workspace_id = payload.get("workspaceId") or None
            if key_type == "workspace" and not workspace_id:
                raise ValidationError("workspace keys require workspaceId")

            secret = f"rtas_{key_type[:3]}_{generate_secret(40)}"
            key = ApiKey(
                id=new_id("akey_"),
                organization_id=org_id,
                key_type=key_type,
                access=access,
                name=str(payload.get("name") or f"{key_type} key"),
                key_prefix=secret[:12],
                key_hash=_sha256(secret),
                scopes=scopes,
                owner_user_id=actor_id if key_type == "personal" else None,
                workspace_id=str(workspace_id) if workspace_id else None,
            )
            store.save_api_key(key)
            _audit(
                "apikey.created",
                actor_id,
                key.key_prefix,
                organizationId=org_id,
                keyType=key_type,
                access=access,
            )
            result = key.to_dict()
            result["secret"] = secret  # shown once; only the hash is stored
            return {"ok": True, "apiKey": result}

    def list(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            items = store.list_api_keys(organization_id)
            visible = [
                k
                for k in items
                if k.key_type != "personal" or k.owner_user_id == actor_id
            ]
            return {
                "ok": True,
                "count": len(visible),
                "apiKeys": [k.to_dict() for k in visible],
            }

    def _get_owned(self, key_id: str, actor_id: str) -> ApiKey:
        ForbiddenError, NotFoundError = _auth_errors()
        key = store.get_api_key(key_id)
        if key is None:
            raise NotFoundError("api key not found")
        if key.key_type == "personal":
            _require_read(actor_id=actor_id, organization_id=key.organization_id)
            if key.owner_user_id != actor_id:
                _require_manage(actor_id=actor_id, organization_id=key.organization_id)
        else:
            _require_manage(actor_id=actor_id, organization_id=key.organization_id)
        return key

    def rotate(self, key_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            key = self._get_owned(key_id, actor_id)
            if not key.active:
                raise ValidationError("cannot rotate a revoked key")
            store.drop_key_hash(key.key_hash)
            secret = f"rtas_{key.key_type[:3]}_{generate_secret(40)}"
            key.key_prefix = secret[:12]
            key.key_hash = _sha256(secret)
            key.rotated_at = _now()
            key.updated_at = _now()
            store.save_api_key(key)
            _audit(
                "apikey.rotated",
                actor_id,
                key.key_prefix,
                organizationId=key.organization_id,
            )
            result = key.to_dict()
            result["secret"] = secret
            return {"ok": True, "apiKey": result}

    def revoke(self, key_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            key = self._get_owned(key_id, actor_id)
            key.active = False
            key.revoked_at = _now()
            key.updated_at = _now()
            store.drop_key_hash(key.key_hash)
            store.save_api_key(key)
            _audit(
                "apikey.revoked",
                actor_id,
                key.key_prefix,
                organizationId=key.organization_id,
            )
            return {"ok": True, "apiKey": key.to_dict()}

    def authenticate(self, secret: str) -> ApiKey | None:
        """Resolve a plaintext secret to an active key (for request auth)."""
        key = store.get_api_key_by_hash(_sha256(secret or ""))
        if key is None or not key.active:
            return None
        key.last_used_at = _now()
        store.save_api_key(key)
        return key


class PersonalAccessTokenEngine:
    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_read(actor_id=actor_id, organization_id=org_id)
            scopes = [str(s) for s in (payload.get("scopes") or [])]
            unknown = [s for s in scopes if s not in API_SCOPES]
            if unknown:
                raise ValidationError(f"unknown scopes: {', '.join(unknown)}")
            if not scopes:
                scopes = [s for s in API_SCOPES if s.endswith(":read")]
            days = int(payload.get("expiresInDays") or PAT_DEFAULT_EXPIRY_DAYS)
            secret = f"rtas_pat_{generate_secret(48)}"
            pat = PersonalAccessToken(
                id=new_id("pat_"),
                user_id=actor_id,
                organization_id=org_id,
                name=str(payload.get("name") or "personal token"),
                token_prefix=secret[:13],
                token_hash=_sha256(secret),
                scopes=scopes,
                expires_at=_now() + timedelta(days=days),
            )
            store.save_pat(pat)
            _audit("pat.created", actor_id, pat.token_prefix, organizationId=org_id)
            result = pat.to_dict()
            result["secret"] = secret
            return {"ok": True, "token": result}

    def list(self, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            items = store.list_pats(actor_id)
            return {"ok": True, "count": len(items), "tokens": [p.to_dict() for p in items]}

    def revoke(self, pat_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ForbiddenError, NotFoundError = _auth_errors()
            pat = store.get_pat(pat_id)
            if pat is None:
                raise NotFoundError("token not found")
            if pat.user_id != actor_id:
                raise ForbiddenError("token belongs to another user")
            pat.active = False
            pat.revoked_at = _now()
            pat.updated_at = _now()
            store.save_pat(pat)
            _audit("pat.revoked", actor_id, pat.token_prefix)
            return {"ok": True, "token": pat.to_dict()}

    def authenticate(self, secret: str) -> PersonalAccessToken | None:
        pat = store.get_pat_by_hash(_sha256(secret or ""))
        if pat is None or not pat.active:
            return None
        if pat.expires_at and pat.expires_at <= _now():
            return None
        pat.last_used_at = _now()
        store.save_pat(pat)
        return pat


class ApiRateLimitingEngine:
    def _tier(self, organization_id: str) -> str:
        lic = store.get_license_by_org(organization_id)
        if lic is not None and lic.status == "active":
            return lic.tier
        return "free"

    def _windows(self, now: datetime) -> tuple[str, str, str]:
        return (
            now.strftime("%Y%m%d%H%M"),
            now.strftime("%Y%m%d%H"),
            now.strftime("%Y%m%d"),
        )

    def _state(self, organization_id: str, scope: str, scope_id: str) -> RateLimitState:
        state = store.get_rate_state(scope, scope_id)
        tier = self._tier(organization_id)
        policy = rate_policy(tier)
        if scope == "workspace" and policy["perMinute"] > 0:
            policy = {
                k: max(1, int(v * WORKSPACE_LIMIT_FRACTION)) if v else 0
                for k, v in policy.items()
            }
        if state is None:
            state = RateLimitState(
                id=new_id("rls_"),
                organization_id=organization_id,
                scope=scope,
                scope_id=scope_id,
            )
        state.tier = tier
        state.per_minute = policy["perMinute"]
        state.per_hour = policy["perHour"]
        state.per_day = policy["perDay"]
        return state

    def check(
        self,
        organization_id: str,
        *,
        scope: str = "organization",
        scope_id: str | None = None,
        record: bool = True,
    ) -> dict[str, Any]:
        """Check and count one request against the rate limit windows."""
        with store.timed_op():
            ValidationError, _ = _validation()
            state = self._state(organization_id, scope, scope_id or organization_id)
            now = _now()
            minute_w, hour_w, day_w = self._windows(now)
            if state.minute_window != minute_w:
                state.minute_window, state.minute_count = minute_w, 0
            if state.hour_window != hour_w:
                state.hour_window, state.hour_count = hour_w, 0
            if state.day_window != day_w:
                state.day_window, state.day_count = day_w, 0

            unlimited = state.per_minute == 0 and state.per_hour == 0 and state.per_day == 0
            allowed = True
            reason = ""
            if not unlimited:
                if state.per_minute and state.minute_count >= state.per_minute:
                    allowed, reason = False, "per-minute limit exceeded"
                elif state.per_hour and state.hour_count >= state.per_hour:
                    allowed, reason = False, "per-hour limit exceeded"
                elif state.per_day and state.day_count >= state.per_day:
                    allowed, reason = False, "per-day limit exceeded"

            if allowed and record:
                state.minute_count += 1
                state.hour_count += 1
                state.day_count += 1
            state.updated_at = now
            store.save_rate_state(state)
            return {
                "ok": True,
                "allowed": allowed,
                "reason": reason,
                "unlimited": unlimited,
                "state": state.to_dict(),
            }

    def status(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            state = self._state(organization_id, "organization", organization_id)
            return {
                "ok": True,
                "tier": state.tier,
                "policy": rate_policy(state.tier),
                "state": state.to_dict(),
                "policies": {k: dict(v) for k, v in RATE_LIMIT_POLICIES.items()},
            }


class DeveloperPlatformEngine:
    def __init__(self, keys: ApiKeyManagementEngine) -> None:
        self.keys = keys

    def docs(self) -> dict[str, Any]:
        return {
            "ok": True,
            "documentation": dict(API_DOCS_METADATA),
            "sdks": [dict(s) for s in SDK_METADATA],
            "webhookEvents": list(WEBHOOK_EVENTS),
            "scopes": list(API_SCOPES),
        }

    def register_webhook(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_manage(actor_id=actor_id, organization_id=org_id)
            _require_org_exists(org_id)
            url = str(require_non_empty(payload.get("url"), "url"))
            if not url.startswith("https://"):
                raise ValidationError("webhook url must use https")
            events = [str(e) for e in (payload.get("events") or [])]
            if not events:
                raise ValidationError("at least one event is required")
            unknown = [e for e in events if e not in WEBHOOK_EVENTS]
            if unknown:
                raise ValidationError(f"unknown events: {', '.join(unknown)}")
            secret = f"rtas_whsec_{generate_secret(32)}"
            hook = Webhook(
                id=new_id("wh_"),
                organization_id=org_id,
                url=url,
                events=events,
                secret_hash=_sha256(secret),
                secret_prefix=secret[:15],
                created_by=actor_id,
            )
            store.save_webhook(hook)
            _audit("webhook.registered", actor_id, url, organizationId=org_id)
            result = hook.to_dict()
            result["secret"] = secret
            return {"ok": True, "webhook": result}

    def list_webhooks(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            items = store.list_webhooks(organization_id)
            return {"ok": True, "count": len(items), "webhooks": [w.to_dict() for w in items]}

    def _owned_hook(self, webhook_id: str, actor_id: str) -> Webhook:
        _, NotFoundError = _auth_errors()
        hook = store.get_webhook(webhook_id)
        if hook is None:
            raise NotFoundError("webhook not found")
        _require_manage(actor_id=actor_id, organization_id=hook.organization_id)
        return hook

    def set_webhook_active(
        self, webhook_id: str, active: bool, *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            hook = self._owned_hook(webhook_id, actor_id)
            hook.active = active
            hook.updated_at = _now()
            store.save_webhook(hook)
            _audit(
                "webhook.updated",
                actor_id,
                f"{hook.id}:active={active}",
                organizationId=hook.organization_id,
            )
            return {"ok": True, "webhook": hook.to_dict()}

    def delete_webhook(self, webhook_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            hook = self._owned_hook(webhook_id, actor_id)
            store.delete_webhook(hook.id)
            _audit("webhook.deleted", actor_id, hook.id, organizationId=hook.organization_id)
            return {"ok": True, "deleted": True, "webhookId": hook.id}

    def emit(
        self,
        organization_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        *,
        deliver: bool = True,
    ) -> list[WebhookDelivery]:
        """Queue an event for all matching webhooks (simulated delivery)."""
        deliveries: list[WebhookDelivery] = []
        for hook in store.list_webhooks(organization_id):
            if not hook.active or event_type not in hook.events:
                continue
            delivery = WebhookDelivery(
                id=new_id("whd_"),
                webhook_id=hook.id,
                organization_id=organization_id,
                event_type=event_type,
                payload=dict(payload or {}),
            )
            if deliver:
                delivery.status = "delivered"
                delivery.attempts = 1
                delivery.delivered_at = _now()
            store.save_delivery(delivery)
            deliveries.append(delivery)
        return deliveries

    def fail_delivery(self, delivery_id: str, error: str = "connection failed") -> WebhookDelivery:
        """Mark a delivery attempt failed and schedule a retry (retry queue)."""
        _, NotFoundError = _auth_errors()
        delivery = store.get_delivery(delivery_id)
        if delivery is None:
            raise NotFoundError("delivery not found")
        delivery.attempts += 1
        delivery.last_error = error
        if delivery.attempts >= WEBHOOK_MAX_RETRIES:
            delivery.status = "exhausted"
            delivery.next_retry_at = None
        else:
            delivery.status = "failed"
            backoff = WEBHOOK_RETRY_BACKOFF_MINUTES[
                min(delivery.attempts, len(WEBHOOK_RETRY_BACKOFF_MINUTES)) - 1
            ]
            delivery.next_retry_at = _now() + timedelta(minutes=backoff)
        delivery.updated_at = _now()
        store.save_delivery(delivery)
        return delivery

    def retry_queue(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            failed = store.list_deliveries(organization_id, status="failed")
            exhausted = store.list_deliveries(organization_id, status="exhausted")
            return {
                "ok": True,
                "pendingRetries": [d.to_dict() for d in failed],
                "exhausted": [d.to_dict() for d in exhausted],
            }

    def record_usage(
        self,
        organization_id: str,
        *,
        endpoint: str,
        method: str = "GET",
        status_code: int = 200,
        latency_ms: float = 0.0,
        api_key_id: str | None = None,
        workspace_id: str | None = None,
    ) -> ApiUsageRecord:
        rec = ApiUsageRecord(
            id=new_id("ausg_"),
            organization_id=organization_id,
            api_key_id=api_key_id,
            workspace_id=workspace_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            latency_ms=latency_ms,
        )
        store.save_usage(rec)
        return rec

    def usage(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_read(actor_id=actor_id, organization_id=organization_id)
            records = store.list_usage(organization_id, limit=5000)
            by_endpoint: dict[str, int] = {}
            errors = 0
            total_latency = 0.0
            for r in records:
                by_endpoint[r.endpoint] = by_endpoint.get(r.endpoint, 0) + 1
                if r.status_code >= 400:
                    errors += 1
                total_latency += r.latency_ms
            count = len(records)
            return {
                "ok": True,
                "usage": {
                    "totalRequests": count,
                    "errorCount": errors,
                    "errorRatePct": round((errors / count * 100.0) if count else 0.0, 2),
                    "avgLatencyMs": round((total_latency / count) if count else 0.0, 3),
                    "byEndpoint": by_endpoint,
                },
                "recent": [r.to_dict() for r in records[:25]],
            }


class LicensePlatformService:
    def __init__(self) -> None:
        self.licenses = LicenseManagementEngine()
        self.validator = self.licenses.validator
        self.keys = ApiKeyManagementEngine()
        self.tokens = PersonalAccessTokenEngine()
        self.rate_limits = ApiRateLimitingEngine()
        self.platform = DeveloperPlatformEngine(self.keys)

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "licenseManagement": "ready",
                "licenseValidation": "ready",
                "apiKeys": "ready",
                "personalAccessTokens": "ready",
                "developerPlatform": "ready",
                "rateLimiting": "ready",
            },
            "licenseTiers": list(LICENSE_TIERS),
            "licenseStatuses": list(LICENSE_STATUSES),
            "apiKeyTypes": list(API_KEY_TYPES),
            "webhookEvents": len(WEBHOOK_EVENTS),
            "stats": store.metrics(),
        }


_service: LicensePlatformService | None = None


def get_license_platform_service() -> LicensePlatformService:
    global _service
    if _service is None:
        _service = LicensePlatformService()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    _service = None


get_engine = get_license_platform_service
