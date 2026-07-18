"""Phase 8 Sprint 6 — Referral, Affiliate & Commission Engine tests."""

from __future__ import annotations

import importlib.util
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVC = ROOT / "app" / "services"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_parents(pkg_name: str):
    parts = pkg_name.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            mod = type(sys)(parent)
            mod.__path__ = []
            sys.modules[parent] = mod
    if "app" in sys.modules:
        sys.modules["app"].__path__ = [str(ROOT / "app")]
    if "app.services" in sys.modules:
        sys.modules["app.services"].__path__ = [str(SVC)]


def _load_folder(folder: str, modules: tuple[str, ...]):
    path = SVC / folder
    pkg = f"app.services.{folder}"
    _ensure_parents(pkg)
    mod = type(sys)(pkg)
    mod.__path__ = [str(path)]
    sys.modules[pkg] = mod
    for name in modules:
        _load(f"{pkg}.{name}", path / f"{name}.py")
    return mod


def _bootstrap():
    _load_folder(
        "multi_tenant",
        ("version", "roles", "models", "validation", "store", "repository", "service", "engine"),
    )
    mt = sys.modules["app.services.multi_tenant"]
    mt.get_multi_tenant_service = sys.modules[
        "app.services.multi_tenant.service"
    ].get_multi_tenant_service
    mt.reset_engine = sys.modules["app.services.multi_tenant.service"].reset_engine

    _load_folder(
        "enterprise_auth",
        (
            "version",
            "errors",
            "models",
            "store",
            "audit",
            "permission_engine",
            "sessions",
            "validators",
            "middleware",
            "sso",
            "service",
            "engine",
        ),
    )
    ea = sys.modules["app.services.enterprise_auth"]
    ea.get_enterprise_auth_service = sys.modules[
        "app.services.enterprise_auth.service"
    ].get_enterprise_auth_service
    ea.reset_engine = sys.modules["app.services.enterprise_auth.service"].reset_engine
    ea.require_access = sys.modules["app.services.enterprise_auth.middleware"].require_access

    _load_folder(
        "referral_affiliate",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    ra = sys.modules["app.services.referral_affiliate"]
    ra.get_referral_affiliate_service = sys.modules[
        "app.services.referral_affiliate.service"
    ].get_referral_affiliate_service
    ra.reset_engine = sys.modules["app.services.referral_affiliate.service"].reset_engine


_bootstrap()


def _ra():
    return sys.modules["app.services.referral_affiliate.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.referral_affiliate.version"]


def _catalog():
    return sys.modules["app.services.referral_affiliate.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    _bootstrap()
    mod = _ra()
    mod._service = None
    sys.modules["app.services.referral_affiliate.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"ra-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Referral Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _svc():
    return _ra().get_referral_affiliate_service()


def _register_affiliate(org_id: str, actor: str, **extra):
    return _svc().affiliates.register(
        {"organizationId": org_id, "name": "Aff", "email": f"{actor}@x.io", **extra},
        actor_id=actor,
    )


# --- Unit ---


def test_version_unit():
    v = _version()
    assert v.PHASE == 8
    assert v.SPRINT == 6
    assert "Referral" in v.ENGINE_NAME
    assert "Commission" in v.ENGINE_NAME


def test_catalog_unit():
    c = _catalog()
    assert "converted" in c.REFERRAL_STATUSES
    assert "active" in c.AFFILIATE_STATUSES
    assert c.MIN_PAYOUT_THRESHOLD_USD == 50.0
    assert c.level_rate_pct(1) == 20.0
    assert c.level_rate_pct(2) == 5.0
    assert c.level_rate_pct(3) == 0.0
    code = c.generate_code("RTAS")
    assert code.startswith("RTAS-") and len(code) == 13


def test_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["sprint"] == 6
    for engine in ("referrals", "affiliates", "commissions", "rewards", "payouts", "analytics"):
        assert status["engines"][engine] == "ready"


# --- Referrals ---


def test_referral_code_create_and_list():
    org_id = _seed_org("owner_rc")
    created = _svc().referrals.create_code({"organizationId": org_id}, actor_id="owner_rc")
    rc = created["referralCode"]
    assert rc["code"].startswith("RTAS-")
    assert rc["link"].endswith(rc["code"])
    listed = _svc().referrals.list(actor_id="owner_rc", organization_id=org_id)
    assert listed["totals"]["codes"] == 1


def test_referral_full_lifecycle_with_reward():
    org_id = _seed_org("owner_rl")
    svc = _svc()
    rc = svc.referrals.create_code({"organizationId": org_id}, actor_id="owner_rl")[
        "referralCode"
    ]
    invited = svc.referrals.invite(
        {"organizationId": org_id, "code": rc["code"], "emails": ["friend@x.io"]},
        actor_id="owner_rl",
    )
    assert invited["count"] == 1
    assert invited["referrals"][0]["status"] == "invited"

    signed = svc.referrals.track_signup(
        {"code": rc["code"], "referredUserId": "friend_user", "email": "friend@x.io"},
        actor_id="system",
    )
    assert signed["referral"]["status"] == "signed_up"
    assert signed["referral"]["referredUserId"] == "friend_user"

    converted = svc.referrals.mark_converted(
        {"referredUserId": "friend_user"}, actor_id="system"
    )
    ref = converted["referral"]
    assert ref["status"] == "rewarded"
    assert ref["rewardCredits"] == _catalog().REFERRER_REWARD_CREDITS
    assert ref["referredBonusCredits"] == _catalog().REFERRED_BONUS_CREDITS

    # Duplicate conversion is idempotent
    again = svc.referrals.mark_converted(
        {"referredUserId": "friend_user"}, actor_id="system"
    )
    assert again.get("duplicate") is True

    history = svc.referrals.history(actor_id="owner_rl", organization_id=org_id)
    assert history["count"] == 1
    assert history["history"][0]["status"] == "rewarded"


def test_referral_duplicate_signup_rejected():
    org_id = _seed_org("owner_rd")
    svc = _svc()
    rc = svc.referrals.create_code({"organizationId": org_id}, actor_id="owner_rd")[
        "referralCode"
    ]
    svc.referrals.track_signup(
        {"code": rc["code"], "referredUserId": "dup_user"}, actor_id="system"
    )
    try:
        svc.referrals.track_signup(
            {"code": rc["code"], "referredUserId": "dup_user"}, actor_id="system"
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "already referred" in str(exc)


def test_referral_max_uses():
    org_id = _seed_org("owner_mu")
    svc = _svc()
    rc = svc.referrals.create_code(
        {"organizationId": org_id, "maxUses": 1}, actor_id="owner_mu"
    )["referralCode"]
    svc.referrals.track_signup(
        {"code": rc["code"], "referredUserId": "u1"}, actor_id="system"
    )
    try:
        svc.referrals.track_signup(
            {"code": rc["code"], "referredUserId": "u2"}, actor_id="system"
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "limit" in str(exc)


# --- Affiliates ---


def test_affiliate_register_and_dashboard():
    org_id = _seed_org("owner_af")
    result = _register_affiliate(org_id, "owner_af")
    aff = result["affiliate"]
    assert aff["status"] == "active"
    assert aff["commissionType"] == "percentage"
    assert result["campaign"]["link"].startswith("https://rtasstudio.ai/a/")

    dash = _svc().affiliates.dashboard(actor_id="owner_af", organization_id=org_id)
    assert dash["stats"]["clicks"] == 0
    assert dash["stats"]["conversions"] == 0
    assert len(dash["campaigns"]) == 1


def test_affiliate_duplicate_registration_rejected():
    org_id = _seed_org("owner_dd")
    _register_affiliate(org_id, "owner_dd")
    try:
        _register_affiliate(org_id, "owner_dd")
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "already an affiliate" in str(exc)


def test_click_and_conversion_tracking():
    org_id = _seed_org("owner_ct")
    svc = _svc()
    reg = _register_affiliate(org_id, "owner_ct")
    aff_id = reg["affiliate"]["id"]
    camp_id = reg["campaign"]["id"]

    for i in range(4):
        svc.affiliates.track_click(
            {
                "affiliateId": aff_id,
                "campaignId": camp_id,
                "source": "twitter",
                "ip": f"10.0.0.{i}",
            },
            actor_id="system",
        )
    conv = svc.affiliates.track_conversion(
        {"affiliateId": aff_id, "campaignId": camp_id, "amountUsd": 100.0},
        actor_id="system",
    )
    assert conv["conversion"]["amountUsd"] == 100.0
    assert len(conv["commissions"]) == 1
    assert conv["commissions"][0]["amountUsd"] == 20.0  # 20% default

    dash = svc.affiliates.dashboard(actor_id="owner_ct", organization_id=org_id)
    assert dash["stats"]["clicks"] == 4
    assert dash["stats"]["conversions"] == 1
    assert dash["stats"]["conversionRatePct"] == 25.0
    assert dash["stats"]["salesUsd"] == 100.0
    assert dash["stats"]["pendingUsd"] == 20.0
    camp = dash["campaigns"][0]
    assert camp["clicks"] == 4
    assert camp["conversions"] == 1
    assert camp["revenueUsd"] == 100.0


# --- Commissions ---


def test_commission_types_and_recurring():
    org_id = _seed_org("owner_cm")
    svc = _svc()
    fixed = _register_affiliate(
        org_id, "owner_cm", commissionType="fixed", commissionRate=15.0
    )
    aff_id = fixed["affiliate"]["id"]
    conv = svc.affiliates.track_conversion(
        {"affiliateId": aff_id, "amountUsd": 500.0}, actor_id="system"
    )
    assert conv["commissions"][0]["amountUsd"] == 15.0  # fixed

    rec = svc.affiliates.track_conversion(
        {"affiliateId": aff_id, "amountUsd": 500.0, "kind": "recurring"},
        actor_id="system",
    )
    # fixed-type affiliate still gets fixed amount on recurring
    assert rec["commissions"][0]["amountUsd"] == 15.0

    pct = _register_affiliate(org_id, "editor_1", commissionRate=25.0)
    pct_id = pct["affiliate"]["id"]
    one = svc.affiliates.track_conversion(
        {"affiliateId": pct_id, "amountUsd": 200.0}, actor_id="system"
    )
    assert one["commissions"][0]["amountUsd"] == 50.0  # 25%
    recurring = svc.affiliates.track_conversion(
        {"affiliateId": pct_id, "amountUsd": 200.0, "kind": "recurring"},
        actor_id="system",
    )
    assert recurring["commissions"][0]["amountUsd"] == 20.0  # 10% recurring
    assert recurring["commissions"][0]["kind"] == "recurring"


def test_multi_level_commission():
    org_id = _seed_org("owner_ml")
    svc = _svc()
    parent = _register_affiliate(org_id, "owner_ml")
    parent_id = parent["affiliate"]["id"]
    child = _register_affiliate(org_id, "editor_1", parentAffiliateId=parent_id)
    child_id = child["affiliate"]["id"]

    conv = svc.affiliates.track_conversion(
        {"affiliateId": child_id, "amountUsd": 100.0}, actor_id="system"
    )
    coms = conv["commissions"]
    assert len(coms) == 2
    assert coms[0]["level"] == 1
    assert coms[0]["amountUsd"] == 20.0
    assert coms[1]["level"] == 2
    assert coms[1]["affiliateId"] == parent_id
    assert coms[1]["amountUsd"] == 5.0  # 5% level-2 override


def test_commission_approval_flow():
    org_id = _seed_org("owner_ca")
    svc = _svc()
    reg = _register_affiliate(org_id, "owner_ca")
    aff_id = reg["affiliate"]["id"]
    conv = svc.affiliates.track_conversion(
        {"affiliateId": aff_id, "amountUsd": 300.0}, actor_id="system"
    )
    com_id = conv["commissions"][0]["id"]
    approved = svc.commissions.approve(com_id, actor_id="owner_ca")
    assert approved["commission"]["status"] == "approved"

    stmt = svc.payouts.statement(actor_id="owner_ca", organization_id=org_id)
    assert stmt["statement"]["approvedUsd"] == 60.0
    assert stmt["statement"]["pendingUsd"] == 0.0
    assert stmt["statement"]["eligibleForPayout"] is True

    # Cannot approve twice
    try:
        svc.commissions.approve(com_id, actor_id="owner_ca")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


# --- Payouts ---


def test_payout_threshold_and_lifecycle():
    org_id = _seed_org("owner_po")
    svc = _svc()
    reg = _register_affiliate(org_id, "owner_po")
    aff_id = reg["affiliate"]["id"]

    # Below threshold
    small = svc.affiliates.track_conversion(
        {"affiliateId": aff_id, "amountUsd": 100.0}, actor_id="system"
    )
    svc.commissions.approve(small["commissions"][0]["id"], actor_id="owner_po")
    try:
        svc.payouts.request({"organizationId": org_id}, actor_id="owner_po")
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "threshold" in str(exc)

    # Reach threshold
    big = svc.affiliates.track_conversion(
        {"affiliateId": aff_id, "amountUsd": 200.0}, actor_id="system"
    )
    svc.commissions.approve(big["commissions"][0]["id"], actor_id="owner_po")
    payout = svc.payouts.request({"organizationId": org_id}, actor_id="owner_po")["payout"]
    assert payout["status"] == "requested"
    assert payout["amountUsd"] == 60.0

    approved = svc.payouts.process(payout["id"], "approved", actor_id="owner_po")
    assert approved["payout"]["status"] == "approved"
    paid = svc.payouts.process(payout["id"], "paid", actor_id="owner_po")
    assert paid["payout"]["status"] == "paid"

    stmt = svc.payouts.statement(actor_id="owner_po", organization_id=org_id)
    assert stmt["statement"]["paidUsd"] == 60.0
    assert stmt["statement"]["approvedUsd"] == 0.0
    paid_coms = [c for c in stmt["commissions"] if c["status"] == "paid"]
    assert len(paid_coms) == 2

    hist = svc.payouts.history(actor_id="owner_po", organization_id=org_id)
    actions = [h["action"] for h in hist["history"]]
    assert "requested" in actions
    assert "approved" in actions
    assert "paid" in actions


def test_payout_exceeding_balance_rejected():
    org_id = _seed_org("owner_pe")
    svc = _svc()
    reg = _register_affiliate(org_id, "owner_pe")
    conv = svc.affiliates.track_conversion(
        {"affiliateId": reg["affiliate"]["id"], "amountUsd": 300.0}, actor_id="system"
    )
    svc.commissions.approve(conv["commissions"][0]["id"], actor_id="owner_pe")
    try:
        svc.payouts.request(
            {"organizationId": org_id, "amountUsd": 999.0}, actor_id="owner_pe"
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "exceeds" in str(exc)


# --- Analytics ---


def test_analytics_summary():
    org_id = _seed_org("owner_an")
    svc = _svc()
    rc = svc.referrals.create_code({"organizationId": org_id}, actor_id="owner_an")[
        "referralCode"
    ]
    svc.referrals.track_signup(
        {"code": rc["code"], "referredUserId": "an_user"}, actor_id="system"
    )
    svc.referrals.mark_converted({"referredUserId": "an_user"}, actor_id="system")

    reg = _register_affiliate(org_id, "owner_an")
    aff_id = reg["affiliate"]["id"]
    svc.affiliates.track_click({"affiliateId": aff_id, "ip": "1.2.3.4"}, actor_id="system")
    svc.affiliates.track_click({"affiliateId": aff_id, "ip": "1.2.3.5"}, actor_id="system")
    conv = svc.affiliates.track_conversion(
        {"affiliateId": aff_id, "amountUsd": 400.0}, actor_id="system"
    )
    svc.commissions.approve(conv["commissions"][0]["id"], actor_id="owner_an")

    analytics = svc.analytics.analytics(actor_id="owner_an", organization_id=org_id)[
        "analytics"
    ]
    assert analytics["totalReferrals"] == 1
    assert analytics["successfulReferrals"] == 1
    assert analytics["affiliates"] == 1
    assert analytics["clicks"] == 2
    assert analytics["conversions"] == 1
    assert analytics["conversionRatePct"] == 50.0
    assert analytics["affiliateSalesUsd"] == 400.0
    assert analytics["commissionEarnedUsd"] == 80.0
    assert analytics["approvedCommissionUsd"] == 80.0
    assert analytics["commissionPaidUsd"] == 0.0
    assert analytics["pendingCommissionUsd"] == 0.0


# --- Security ---


def test_ownership_isolation():
    org_a = _seed_org("owner_sa")
    org_b = _seed_org("owner_sb")
    svc = _svc()
    _register_affiliate(org_a, "owner_sa")

    # Non-member cannot read another org's referrals/analytics
    try:
        svc.referrals.list(actor_id="owner_sb", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        svc.analytics.analytics(actor_id="owner_sb", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass

    # Member of org_b but not an affiliate cannot see dashboard
    try:
        svc.affiliates.dashboard(actor_id="owner_sb", organization_id=org_b)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass

    # Non-admin cannot process payouts
    reg = _register_affiliate(org_b, "editor_1")
    conv = svc.affiliates.track_conversion(
        {"affiliateId": reg["affiliate"]["id"], "amountUsd": 500.0}, actor_id="system"
    )
    com_id = conv["commissions"][0]["id"]
    try:
        svc.commissions.approve(com_id, actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


# --- Performance ---


def test_performance_bulk_tracking():
    org_id = _seed_org("owner_pf")
    svc = _svc()
    reg = _register_affiliate(org_id, "owner_pf")
    aff_id = reg["affiliate"]["id"]
    start = time.perf_counter()
    for i in range(200):
        svc.affiliates.track_click(
            {"affiliateId": aff_id, "ip": f"10.1.{i // 250}.{i % 250}"},
            actor_id="system",
        )
    for _ in range(50):
        svc.affiliates.track_conversion(
            {"affiliateId": aff_id, "amountUsd": 10.0}, actor_id="system"
        )
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0

    dash = svc.affiliates.dashboard(actor_id="owner_pf", organization_id=org_id)
    assert dash["stats"]["clicks"] == 200
    assert dash["stats"]["conversions"] == 50
    assert dash["stats"]["pendingUsd"] == 100.0  # 50 × $2 (20% of $10)
    metrics = sys.modules["app.services.referral_affiliate.store"].metrics()
    assert metrics["errorCount"] == 0
