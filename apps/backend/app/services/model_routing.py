"""
Cost-optimized AI model routing for RTAS Studio.

Prioritizes the lowest cost-per-second model that still meets category quality
requirements, with a hard ceiling of $0.020/s. Weighted credit deduction scales
from 1:1 (cheap models) up to 5x (models near the budget ceiling).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal, TYPE_CHECKING

from app.core.config import settings

if TYPE_CHECKING:
    from app.services.ai_service import GenerationJobInput

logger = logging.getLogger(__name__)

HARD_BUDGET_CEILING_USD = 0.020
CHEAP_FLOOR_USD = 0.005
MAX_CREDIT_WEIGHT = 5.0

ProviderName = Literal["fal", "replicate"]


class ModelRoutingError(Exception):
    """Raised when no model can be selected within the hard budget ceiling."""


@dataclass(frozen=True)
class CategoryRequirements:
    min_quality_tier: int = 2
    required_capabilities: frozenset[str] = frozenset()
    visual_style_capabilities: dict[str, frozenset[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelSpec:
    id: str
    display_name: str
    provider: ProviderName
    endpoint_setting: str
    cost_per_second: float
    quality_tier: int
    capabilities: frozenset[str]
    supported_categories: frozenset[str]
    supported_visual_styles: frozenset[str]
    requires_image: bool = False


@dataclass(frozen=True)
class ModelSelection:
    model_id: str
    display_name: str
    provider: ProviderName
    endpoint: str
    cost_per_second: float
    quality_tier: int
    credit_weight: float
    reason: str
    quality_match: bool


CATEGORY_REQUIREMENTS: dict[str, CategoryRequirements] = {
    "islamic": CategoryRequirements(
        min_quality_tier=2,
        required_capabilities=frozenset({"talking_head"}),
    ),
    "podcast": CategoryRequirements(
        min_quality_tier=2,
        required_capabilities=frozenset({"talking_head"}),
    ),
    "business": CategoryRequirements(
        min_quality_tier=2,
        visual_style_capabilities={
            "real": frozenset({"identity", "talking_head"}),
            "avatar": frozenset({"talking_head", "cinematic"}),
            "cartoon": frozenset({"cartoon", "cinematic"}),
        },
    ),
    "song": CategoryRequirements(
        min_quality_tier=3,
        required_capabilities=frozenset({"cinematic"}),
    ),
    "story": CategoryRequirements(
        min_quality_tier=3,
        required_capabilities=frozenset({"cinematic"}),
    ),
    "cartoon": CategoryRequirements(
        min_quality_tier=2,
        required_capabilities=frozenset({"cartoon", "cinematic"}),
    ),
}

MODEL_CATALOG: tuple[ModelSpec, ...] = (
    ModelSpec(
        id="flashhead",
        display_name="FlashHead",
        provider="fal",
        endpoint_setting="fal_model_flashhead",
        cost_per_second=0.005,
        quality_tier=2,
        capabilities=frozenset({"talking_head", "identity", "i2v"}),
        supported_categories=frozenset({"islamic", "podcast", "business"}),
        supported_visual_styles=frozenset({"real", "avatar"}),
        requires_image=True,
    ),
    ModelSpec(
        id="wan_t2v",
        display_name="Wan 2.7 T2V",
        provider="fal",
        endpoint_setting="fal_model_t2v",
        cost_per_second=0.010,
        quality_tier=3,
        capabilities=frozenset({"cinematic", "t2v", "cartoon"}),
        supported_categories=frozenset({"song", "story", "cartoon", "business"}),
        supported_visual_styles=frozenset({"real", "avatar", "cartoon"}),
    ),
    ModelSpec(
        id="wan_i2v",
        display_name="Wan 2.7 I2V",
        provider="fal",
        endpoint_setting="fal_model_i2v",
        cost_per_second=0.012,
        quality_tier=3,
        capabilities=frozenset({"cinematic", "identity", "i2v", "cartoon"}),
        supported_categories=frozenset(
            {"song", "story", "cartoon", "business", "islamic", "podcast"}
        ),
        supported_visual_styles=frozenset({"real", "avatar", "cartoon"}),
    ),
    ModelSpec(
        id="wan_real_face",
        display_name="Wan 2.7 Real Face",
        provider="fal",
        endpoint_setting="fal_model_real_face",
        cost_per_second=0.015,
        quality_tier=4,
        capabilities=frozenset({"cinematic", "identity", "i2v", "talking_head"}),
        supported_categories=frozenset(
            {"song", "story", "business", "islamic", "podcast"}
        ),
        supported_visual_styles=frozenset({"real"}),
        requires_image=True,
    ),
    ModelSpec(
        id="wan_cinematic",
        display_name="Wan 2.7 Cinematic",
        provider="fal",
        endpoint_setting="fal_model_cinematic",
        cost_per_second=0.020,
        quality_tier=5,
        capabilities=frozenset({"cinematic", "identity", "i2v", "cartoon"}),
        supported_categories=frozenset({"song", "story", "cartoon", "business"}),
        supported_visual_styles=frozenset({"real", "avatar", "cartoon"}),
    ),
    ModelSpec(
        id="replicate_wan_i2v",
        display_name="Replicate Wan 2.1 I2V",
        provider="replicate",
        endpoint_setting="replicate_model_i2v",
        cost_per_second=0.014,
        quality_tier=3,
        capabilities=frozenset({"cinematic", "identity", "i2v"}),
        supported_categories=frozenset(
            {"song", "story", "business", "islamic", "podcast", "cartoon"}
        ),
        supported_visual_styles=frozenset({"real", "avatar", "cartoon"}),
    ),
    ModelSpec(
        id="replicate_wan_t2v",
        display_name="Replicate Wan 2.1 T2V",
        provider="replicate",
        endpoint_setting="replicate_model_t2v",
        cost_per_second=0.012,
        quality_tier=3,
        capabilities=frozenset({"cinematic", "t2v", "cartoon"}),
        supported_categories=frozenset({"song", "story", "cartoon", "business"}),
        supported_visual_styles=frozenset({"real", "avatar", "cartoon"}),
    ),
    ModelSpec(
        id="replicate_real_face",
        display_name="Replicate Wan Real Face",
        provider="replicate",
        endpoint_setting="replicate_model_real_face",
        cost_per_second=0.018,
        quality_tier=4,
        capabilities=frozenset({"cinematic", "identity", "i2v", "talking_head"}),
        supported_categories=frozenset(
            {"song", "story", "business", "islamic", "podcast"}
        ),
        supported_visual_styles=frozenset({"real"}),
        requires_image=True,
    ),
)


def get_routing_policy_summary() -> dict:
    return {
        "strategy": "cost_optimization",
        "hard_budget_ceiling_usd_per_second": HARD_BUDGET_CEILING_USD,
        "cheap_floor_usd_per_second": CHEAP_FLOOR_USD,
        "max_credit_weight": MAX_CREDIT_WEIGHT,
        "catalog_size": len(MODEL_CATALOG),
        "deduction_ratio": "1:1 at cheap floor, up to 5:1 at budget ceiling",
    }


def get_cost_policy_payload(duration_seconds: int = 30) -> dict:
    """Public cost-policy payload for API routes and frontend estimates."""
    duration = max(1, int(duration_seconds))
    return {
        **get_routing_policy_summary(),
        "duration_seconds": duration,
        "weighted_credits_at_floor": weighted_credits_for_duration(
            duration, CHEAP_FLOOR_USD
        ),
        "weighted_credits_at_ceiling": weighted_credits_for_duration(
            duration, HARD_BUDGET_CEILING_USD
        ),
        "credit_weight_at_floor": credit_weight_for_cost(CHEAP_FLOOR_USD),
        "credit_weight_at_ceiling": credit_weight_for_cost(HARD_BUDGET_CEILING_USD),
    }


def credit_weight_for_cost(cost_per_second: float) -> float:
    """1:1 at $0.005/s, scales linearly up to 5x at $0.020/s."""
    cost = min(max(cost_per_second, CHEAP_FLOOR_USD), HARD_BUDGET_CEILING_USD)
    if cost <= CHEAP_FLOOR_USD:
        return 1.0
    span = HARD_BUDGET_CEILING_USD - CHEAP_FLOOR_USD
    return 1.0 + ((cost - CHEAP_FLOOR_USD) / span) * (MAX_CREDIT_WEIGHT - 1.0)


def weighted_credits_for_duration(
    duration_seconds: int, cost_per_second: float
) -> int:
    weight = credit_weight_for_cost(cost_per_second)
    return max(1, round(int(duration_seconds) * weight))


def _resolve_endpoint(spec: ModelSpec) -> str:
    return str(getattr(settings, spec.endpoint_setting))


def _job_wants_i2v(job: GenerationJobInput) -> bool:
    return job.mode == "image" or job.driving_image_path is not None


def _model_supports_input_mode(spec: ModelSpec, job: GenerationJobInput) -> bool:
    wants_i2v = _job_wants_i2v(job)
    if wants_i2v:
        if "i2v" not in spec.capabilities:
            return False
        if spec.requires_image and job.driving_image_path is None:
            return False
        return True
    return "t2v" in spec.capabilities


def _meets_quality(spec: ModelSpec, job: GenerationJobInput) -> bool:
    req = CATEGORY_REQUIREMENTS.get(job.category, CategoryRequirements())
    if spec.quality_tier < req.min_quality_tier:
        return False

    style_caps = req.visual_style_capabilities
    if style_caps and job.visual_style in style_caps:
        needed = style_caps[job.visual_style]
        if not needed.intersection(spec.capabilities):
            return False
    elif req.required_capabilities:
        if not req.required_capabilities.intersection(spec.capabilities):
            return False

    return True


def _eligible_models(job: GenerationJobInput, provider: ProviderName) -> list[ModelSpec]:
    eligible: list[ModelSpec] = []
    for spec in MODEL_CATALOG:
        if spec.provider != provider:
            continue
        if job.category not in spec.supported_categories:
            continue
        if job.visual_style not in spec.supported_visual_styles:
            continue
        if not _model_supports_input_mode(spec, job):
            continue
        endpoint = _resolve_endpoint(spec)
        if not endpoint.strip():
            continue
        eligible.append(spec)
    return eligible


def select_optimal_model(job: GenerationJobInput, provider: ProviderName) -> ModelSelection:
    """
    Pick the lowest cost-per-second model within HARD_BUDGET_CEILING that meets
    category quality requirements. Falls back to the best model still under the
    ceiling when no strict quality match exists.
    """
    eligible = _eligible_models(job, provider)
    within_budget = [
        spec for spec in eligible if spec.cost_per_second <= HARD_BUDGET_CEILING_USD
    ]

    if not within_budget:
        raise ModelRoutingError(
            f"No {provider} model available under ${HARD_BUDGET_CEILING_USD:.3f}/s "
            f"for category={job.category} style={job.visual_style}."
        )

    quality_matches = [spec for spec in within_budget if _meets_quality(spec, job)]
    pool = quality_matches if quality_matches else within_budget
    quality_match = bool(quality_matches)

    pool.sort(key=lambda spec: (spec.cost_per_second, -spec.quality_tier))
    chosen = pool[0]
    endpoint = _resolve_endpoint(chosen)
    weight = credit_weight_for_cost(chosen.cost_per_second)

    if quality_match:
        reason = (
            f"{chosen.display_name} selected for lowest cost (${chosen.cost_per_second:.3f}/s) "
            f"while maintaining quality standards for {job.category}/{job.visual_style}."
        )
    else:
        reason = (
            f"{chosen.display_name} selected as highest-quality option within "
            f"${HARD_BUDGET_CEILING_USD:.3f}/s budget "
            f"(no strict quality match for {job.category}/{job.visual_style})."
        )
        logger.warning(
            "Model routing quality fallback job=%s category=%s style=%s model=%s",
            job.job_id,
            job.category,
            job.visual_style,
            chosen.id,
        )

    logger.info(
        "Model routing job=%s provider=%s model=%s cost=$%.3f/s weight=%.2fx — %s",
        job.job_id,
        provider,
        chosen.id,
        chosen.cost_per_second,
        weight,
        reason,
    )

    return ModelSelection(
        model_id=chosen.id,
        display_name=chosen.display_name,
        provider=chosen.provider,
        endpoint=endpoint,
        cost_per_second=chosen.cost_per_second,
        quality_tier=chosen.quality_tier,
        credit_weight=weight,
        reason=reason,
        quality_match=quality_match,
    )


def apply_model_selection(job: GenerationJobInput, selection: ModelSelection) -> None:
    job.selected_model_id = selection.model_id
    job.selected_model_name = selection.display_name
    job.selected_endpoint = selection.endpoint
    job.selected_cost_per_second = selection.cost_per_second
    job.selection_reason = selection.reason
    job.credit_weight = selection.credit_weight
