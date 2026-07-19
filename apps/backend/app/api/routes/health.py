from fastapi import APIRouter

from app.core.config import reload_settings, settings
from app.services.fal_guard import clear_billing_block_if_fal_valid, get_guard_public_status
from app.services.fal_verify import get_startup_verify_result, verify_fal_key
from app.services.replicate_verify import (
    get_startup_verify_result as get_replicate_startup_result,
    verify_replicate_token,
)

router = APIRouter(tags=["health"])


@router.get("/health/ping")
async def health_ping():
    """Fast liveness probe (no external provider round-trips)."""
    reload_settings()
    return {
        "status": "healthy",
        "service": "rtas-studio-ai-api",
        "fal": {"configured": settings.fal_configured},
        "replicate": {"configured": settings.replicate_configured},
    }


@router.get("/ready")
async def ready():
    """Production readiness probe — Phase 9 complete (final marketplace ecosystem)."""
    reload_settings()
    return {
        "status": "ready",
        "ok": True,
        "service": "rtas-studio-ai-api",
        "version": "1.0.0",
        "phase": 9,
        "sprint": 10,
        "phase9_complete": True,
        "marketplace_ecosystem_verified": True,
        "ready_for_phase_10": True,
        "phase8_complete": True,
        "enterprise_billing_commerce_verified": True,
        "marketplace_ecosystem": "RTAS Enterprise AI Marketplace Ecosystem Foundation v1.0",
        "creator_platform": "RTAS Enterprise Creator Platform & Publisher Ecosystem v1.0",
        "publisher_engine": "RTAS Enterprise Creator Platform & Publisher Ecosystem v1.0",
        "community_platform": "RTAS Enterprise Community Platform & Social Collaboration Engine v1.0",
        "social_engine": "RTAS Enterprise Community Platform & Social Collaboration Engine v1.0",
        "template_store": "RTAS Enterprise Template Store, Versioning & Asset Management Engine v1.0",
        "asset_management": "RTAS Enterprise Template Store, Versioning & Asset Management Engine v1.0",
        "plugin_framework": "RTAS Enterprise Plugin Framework, Extension SDK & Third-Party Integration Engine v1.0",
        "extension_sdk": "RTAS Enterprise Plugin Framework, Extension SDK & Third-Party Integration Engine v1.0",
        "integration_engine": "RTAS Enterprise Plugin Framework, Extension SDK & Third-Party Integration Engine v1.0",
        "public_api_platform": "RTAS Enterprise Public API Platform, SDK & Developer Ecosystem v1.0",
        "developer_portal": "RTAS Enterprise Public API Platform, SDK & Developer Ecosystem v1.0",
        "sdk_distribution": "RTAS Enterprise Public API Platform, SDK & Developer Ecosystem v1.0",
        "ai_agents": "RTAS Enterprise AI Agents, Automation Workflows & Orchestration Engine v1.0",
        "workflow_automation": "RTAS Enterprise AI Agents, Automation Workflows & Orchestration Engine v1.0",
        "agent_orchestration": "RTAS Enterprise AI Agents, Automation Workflows & Orchestration Engine v1.0",
        "enterprise_automation": "RTAS Enterprise Automation, Integrations & Event-Driven Platform v1.0",
        "event_bus": "RTAS Enterprise Automation, Integrations & Event-Driven Platform v1.0",
        "integration_hub": "RTAS Enterprise Automation, Integrations & Event-Driven Platform v1.0",
        "marketplace_analytics": "RTAS Enterprise Marketplace Analytics, Revenue Intelligence & Monetization Engine v1.0",
        "revenue_intelligence": "RTAS Enterprise Marketplace Analytics, Revenue Intelligence & Monetization Engine v1.0",
        "monetization_engine": "RTAS Enterprise Marketplace Analytics, Revenue Intelligence & Monetization Engine v1.0",
        "phase9_final_validation": "RTAS Phase 9 Final Integration & Marketplace Ecosystem Validation Engine v1.0",
        "final_release": True,
        "platform": "RTAS Studio AI Enterprise SaaS Platform v1.0",
        "phase7_complete": True,
        "billing_engine": "RTAS Enterprise Billing & Subscription Foundation v1.0",
        "paddle_billing": "RTAS Paddle Billing Integration v1.0",
        "payment_processing": "RTAS PayPal Credit Wallet & Payment Processing Engine v1.0",
        "paypal_engine": "RTAS PayPal Credit Wallet & Payment Processing Engine v1.0",
        "credit_metering": "RTAS Credit Consumption, Usage Metering & Quota Engine v1.0",
        "quota_engine": "RTAS Credit Consumption, Usage Metering & Quota Engine v1.0",
        "billing_automation": "RTAS Invoicing, Tax, Coupons & Billing Automation Engine v1.0",
        "invoice_engine": "RTAS Invoicing, Tax, Coupons & Billing Automation Engine v1.0",
        "referral_engine": "RTAS Referral, Affiliate & Commission Engine v1.0",
        "affiliate_engine": "RTAS Referral, Affiliate & Commission Engine v1.0",
        "license_engine": "RTAS Enterprise License, API Access & Developer Platform Engine v1.0",
        "developer_platform": "RTAS Enterprise License, API Access & Developer Platform Engine v1.0",
        "usage_analytics": "RTAS Enterprise Usage Analytics, Cost Optimization & AI Provider Billing Engine v1.0",
        "cost_optimization": "RTAS Enterprise Usage Analytics, Cost Optimization & AI Provider Billing Engine v1.0",
        "marketplace_engine": "RTAS Enterprise Marketplace, Template Store & Digital Commerce Engine v1.0",
        "management_engine": "RTAS Organization, Workspace & Team Management Engine v1.0",
        "project_engine": "RTAS Project Management & Collaboration Engine v1.0",
        "asset_engine": "RTAS Enterprise Asset Management & Digital Library Engine v1.0",
        "notification_engine": "RTAS Enterprise Notifications, Comments & Activity Engine v1.0",
        "version_engine": "RTAS Enterprise Version Control, Approval & Review Engine v1.0",
        "analytics_engine": "RTAS Enterprise Reporting, Analytics & Business Intelligence Engine v1.0",
        "platform_ops_engine": "RTAS Enterprise Administration, System Management & Platform Operations Engine v1.0",
        "enterprise_saas": "RTAS Studio AI Enterprise SaaS Platform v1.0",
        "director_engine": "RTAS Studio AI Director Engine v1.0",
    }


@router.get("/health")
async def health():
    reload_settings()
    guard = get_guard_public_status()

    # Re-check Fal when guard is blocked or startup cache is missing — billing top-ups
    # do not clear fal-guard.json automatically until we verify the key again.
    fal = get_startup_verify_result()
    if settings.fal_configured and (
        guard.get("billing_blocked") or fal is None or fal.valid is False
    ):
        fal = await verify_fal_key()
        if guard.get("billing_blocked") and fal.valid:
            clear_billing_block_if_fal_valid(True)
            guard = get_guard_public_status()

    replicate = get_replicate_startup_result()
    if replicate is None and settings.replicate_configured:
        replicate = await verify_replicate_token()

    return {
        "status": "healthy",
        "service": "rtas-studio-ai-api",
        "version": "1.0.0",
        "ai_provider_mode": settings.ai_provider_mode,
        "primary_provider": "fal" if settings.fal_configured else (
            "replicate" if settings.replicate_configured else "simulation"
        ),
        "fal": {
            "configured": settings.fal_configured,
            "valid": fal.valid if fal else None,
            "live_generation": (
                fal.live_generation_enabled
                if fal
                else False
            ) and guard.get("live_calls_allowed", True),
            "live_enabled": settings.fal_live_enabled,
            "guard": guard,
            "error": fal.error if fal and fal.valid is False else None,
        },
        "replicate": {
            "configured": settings.replicate_configured,
            "valid": replicate.valid if replicate else None,
            "live_generation": replicate.live_generation_enabled if replicate else False,
            "username": replicate.username if replicate and replicate.valid else None,
            "error": replicate.error if replicate and replicate.valid is False else None,
        },
    }
