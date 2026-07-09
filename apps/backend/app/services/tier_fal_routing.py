"""
Strict Fal.ai endpoint routing by authenticated user billing tier.

Economy tiers (Creator Starter / Pro Studio) → cost-optimized models.
Production Enterprise → ultra-premium cinematic models.

Missing or invalid billing metadata rejects live cloud renders (402).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.config import settings
from app.schemas.generation import GenerateRequest, UserProfileSnapshot
from app.services.model_routing import credit_weight_for_cost

if TYPE_CHECKING:
    from app.services.ai_service import GenerationJobInput

logger = logging.getLogger(__name__)

BILLING_REQUIRED_MESSAGE = (
    "Payment required: a valid paid plan, active subscription, and credits "
    "are required for cloud rendering."
)

PAID_TIERS = frozenset({"tester", "standard", "premium"})
ECONOMY_TIERS = frozenset({"tester", "standard"})
ENTERPRISE_TIERS = frozenset({"premium"})

ECONOMY_COST_PER_SECOND = 0.005
ENTERPRISE_COST_PER_SECOND = 0.020


class BillingAccessError(Exception):
    """Raised when billing metadata is missing or insufficient for live Fal calls."""

    def __init__(self, message: str, *, error_code: str = "billing_required"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


@dataclass(frozen=True)
class TierFalSelection:
    model_id: str
    display_name: str
    endpoint: str
    resolution: str
    cost_per_second: float
    credit_weight: float
    tier_band: str
    reason: str


def _normalize_tier(tier: str | None) -> str | None:
    if not tier or not isinstance(tier, str):
        return None
    normalized = tier.strip().lower()
    return normalized if normalized in PAID_TIERS else None


def assert_billing_for_live_generation(body: GenerateRequest) -> None:
    """
    Hard gate for paid cloud renders. Preview and free-trial paths are exempt.
    """
    if body.preview_only or body.use_free_trial:
        return

    profile = body.profile
    if profile is None:
        raise BillingAccessError(
            "Missing billing profile snapshot.",
            error_code="billing_required",
        )

    tier = _normalize_tier(profile.tier)
    if tier is None:
        raise BillingAccessError(BILLING_REQUIRED_MESSAGE, error_code="billing_required")

    if profile.credits is None or int(profile.credits) <= 0:
        raise BillingAccessError(BILLING_REQUIRED_MESSAGE, error_code="billing_required")

    if tier in ("standard", "premium") and not profile.subscription_active:
        raise BillingAccessError(BILLING_REQUIRED_MESSAGE, error_code="billing_required")


def _job_wants_i2v(job: GenerationJobInput) -> bool:
    return job.mode == "image" or job.driving_image_path is not None


def resolve_tier_fal_endpoint(
    job: GenerationJobInput,
    profile: UserProfileSnapshot,
) -> TierFalSelection:
    """
    Map billing tier → Fal model endpoint. No cost-optimization fallback.
    """
    tier = _normalize_tier(profile.tier)
    if tier is None:
        raise BillingAccessError(BILLING_REQUIRED_MESSAGE, error_code="billing_required")

    wants_i2v = _job_wants_i2v(job)
    is_cinematic = job.category in ("song", "story")

    if tier in ECONOMY_TIERS:
        if job.visual_style == "real":
            endpoint = settings.fal_tier_economy_real_face
            model_id = "mochi_real"
            display = "Mochi Video (Economy — Real Face)"
        elif wants_i2v:
            endpoint = settings.fal_tier_economy_i2v
            model_id = "mochi_i2v"
            display = "Mochi Video (Economy — I2V)"
        else:
            endpoint = settings.fal_tier_economy_t2v
            model_id = "mochi_t2v"
            display = "Mochi Video (Economy — T2V)"
        resolution = settings.fal_tier_economy_resolution
        cost = ECONOMY_COST_PER_SECOND
        band = "economy"
        reason = (
            f"Tier {tier} routes to cost-optimized Fal model ({endpoint}) "
            f"to protect operational margins."
        )
    elif tier in ENTERPRISE_TIERS:
        if is_cinematic and not wants_i2v:
            endpoint = settings.fal_tier_enterprise_cinematic
            model_id = "luma_cinematic"
            display = "Luma Dream Machine (Enterprise — Cinematic)"
        elif job.visual_style == "real":
            endpoint = settings.fal_tier_enterprise_real_face
            model_id = "kling_real"
            display = "Kling Video (Enterprise — Real Face)"
        elif wants_i2v:
            endpoint = settings.fal_tier_enterprise_i2v
            model_id = "kling_i2v"
            display = "Kling Video (Enterprise — I2V)"
        else:
            endpoint = settings.fal_tier_enterprise_t2v
            model_id = "kling_t2v"
            display = "Kling Video (Enterprise — T2V)"
        resolution = settings.fal_tier_enterprise_resolution
        cost = ENTERPRISE_COST_PER_SECOND
        band = "enterprise"
        reason = (
            f"Tier {tier} routes to premium Fal model ({endpoint}) "
            f"for hyper-fidelity cinematic output."
        )
    else:
        raise BillingAccessError(BILLING_REQUIRED_MESSAGE, error_code="billing_required")

    endpoint = endpoint.strip()
    if not endpoint:
        raise BillingAccessError(
            f"Fal endpoint not configured for tier band={band}.",
            error_code="billing_required",
        )

    if job.visual_style == "real" and job.driving_image_path is None:
        raise BillingAccessError(
            "Real face mode requires a face reference image for cloud rendering.",
            error_code="billing_required",
        )

    weight = credit_weight_for_cost(cost)
    logger.info(
        "Tier Fal routing job=%s tier=%s band=%s endpoint=%s resolution=%s",
        job.job_id,
        tier,
        band,
        endpoint,
        resolution,
    )

    return TierFalSelection(
        model_id=model_id,
        display_name=display,
        endpoint=endpoint,
        resolution=resolution,
        cost_per_second=cost,
        credit_weight=weight,
        tier_band=band,
        reason=reason,
    )


def apply_tier_fal_routing(job: GenerationJobInput, body: GenerateRequest) -> TierFalSelection:
    """Assert billing and stamp tier-routed Fal endpoint on the job."""
    assert_billing_for_live_generation(body)
    profile = body.profile
    if profile is None:
        raise BillingAccessError(
            "Missing billing profile snapshot.",
            error_code="billing_required",
        )

    selection = resolve_tier_fal_endpoint(job, profile)
    job.selected_model_id = selection.model_id
    job.selected_model_name = selection.display_name
    job.selected_endpoint = selection.endpoint
    job.selected_cost_per_second = selection.cost_per_second
    job.selection_reason = selection.reason
    job.credit_weight = selection.credit_weight
    job.fal_resolution = selection.resolution
    return selection
