"""Future SSO integration surface (OIDC / SAML ready stubs)."""

from __future__ import annotations

from typing import Any

from app.services.enterprise_auth.models import SSOProviderConfig

# Modular provider registry — enable when credentials are configured
_PROVIDERS: list[SSOProviderConfig] = [
    SSOProviderConfig(
        key="oidc_generic",
        name="OpenID Connect (Generic)",
        enabled=False,
        protocol="oidc",
        metadata={"scopes": ["openid", "profile", "email"]},
    ),
    SSOProviderConfig(
        key="saml_enterprise",
        name="SAML 2.0 Enterprise",
        enabled=False,
        protocol="saml",
        metadata={"bindings": ["http-post", "http-redirect"]},
    ),
    SSOProviderConfig(
        key="google_workspace",
        name="Google Workspace",
        enabled=False,
        protocol="oidc",
        metadata={"issuer": "https://accounts.google.com"},
    ),
    SSOProviderConfig(
        key="microsoft_entra",
        name="Microsoft Entra ID",
        enabled=False,
        protocol="oidc",
        metadata={"issuer": "https://login.microsoftonline.com"},
    ),
]


def list_sso_providers() -> dict[str, Any]:
    return {
        "ok": True,
        "ssoReady": True,
        "count": len(_PROVIDERS),
        "providers": [p.to_dict() for p in _PROVIDERS],
        "note": "SSO providers are registered and ready for credential configuration.",
    }


def get_sso_provider(key: str) -> SSOProviderConfig | None:
    for p in _PROVIDERS:
        if p.key == key:
            return p
    return None


def begin_sso_login(*, provider_key: str, organization_id: str) -> dict[str, Any]:
    """Stub for future SSO redirect initiation."""
    provider = get_sso_provider(provider_key)
    if provider is None:
        return {
            "ok": False,
            "error": "unknown_provider",
            "detail": f"SSO provider '{provider_key}' not found",
        }
    return {
        "ok": True,
        "ready": True,
        "enabled": provider.enabled,
        "provider": provider.to_dict(),
        "organizationId": organization_id,
        "nextStep": "configure_credentials" if not provider.enabled else "redirect",
        "message": (
            "SSO integration surface is ready; enable provider credentials to activate."
            if not provider.enabled
            else "SSO redirect would begin here."
        ),
    }
