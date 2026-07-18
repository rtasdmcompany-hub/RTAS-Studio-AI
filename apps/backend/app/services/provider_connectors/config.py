"""Provider configuration loader — env-based, never expose secrets."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderConfig:
    provider_id: str
    api_key_env: str
    base_url: str | None = None
    default_model: str | None = None
    timeout_sec: float = 30.0
    max_retries: int = 2
    priority: int = 100
    enabled: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def api_key_present(self) -> bool:
        return bool((os.getenv(self.api_key_env) or "").strip())

    def public_dict(self) -> dict[str, Any]:
        """Safe config for APIs — never includes credentials."""
        return {
            "provider_id": self.provider_id,
            "api_key_env": self.api_key_env,
            "api_key_configured": self.api_key_present,
            "base_url": self.base_url,
            "default_model": self.default_model,
            "timeout_sec": self.timeout_sec,
            "max_retries": self.max_retries,
            "priority": self.priority,
            "enabled": self.enabled,
        }


_DEFAULTS: dict[str, ProviderConfig] = {
    "openai": ProviderConfig(
        provider_id="openai",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
        priority=10,
    ),
    "gemini": ProviderConfig(
        provider_id="gemini",
        api_key_env="GOOGLE_API_KEY",
        base_url="https://generativelanguage.googleapis.com",
        default_model="gemini-2.0-flash",
        priority=20,
    ),
    "claude": ProviderConfig(
        provider_id="claude",
        api_key_env="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com",
        default_model="claude-sonnet-4-20250514",
        priority=15,
    ),
    "runpod": ProviderConfig(
        provider_id="runpod",
        api_key_env="RUNPOD_API_KEY",
        base_url="https://api.runpod.ai/v2",
        default_model="runpod-gpu",
        priority=40,
        timeout_sec=120.0,
    ),
    "stability": ProviderConfig(
        provider_id="stability",
        api_key_env="STABILITY_API_KEY",
        base_url="https://api.stability.ai",
        default_model="stable-diffusion-xl",
        priority=30,
    ),
    "elevenlabs": ProviderConfig(
        provider_id="elevenlabs",
        api_key_env="ELEVENLABS_API_KEY",
        base_url="https://api.elevenlabs.io/v1",
        default_model="eleven_multilingual_v2",
        priority=25,
    ),
}


def load_provider_config(provider_id: str) -> ProviderConfig:
    key = (provider_id or "").strip().lower()
    cfg = _DEFAULTS.get(key)
    if not cfg:
        raise ValueError(f"Unknown provider config: {provider_id}")
    # Allow env override for enable/disable
    disabled = (os.getenv(f"RTAS_PROVIDER_{key.upper()}_DISABLED") or "").strip() in (
        "1",
        "true",
        "yes",
    )
    return ProviderConfig(
        provider_id=cfg.provider_id,
        api_key_env=cfg.api_key_env,
        base_url=cfg.base_url,
        default_model=cfg.default_model,
        timeout_sec=cfg.timeout_sec,
        max_retries=cfg.max_retries,
        priority=cfg.priority,
        enabled=cfg.enabled and not disabled,
        extra=dict(cfg.extra),
    )


def load_all_configs() -> dict[str, ProviderConfig]:
    return {k: load_provider_config(k) for k in _DEFAULTS}


def list_config_ids() -> list[str]:
    return sorted(_DEFAULTS.keys())
