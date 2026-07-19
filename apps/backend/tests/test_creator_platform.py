"""Phase 9 Sprint 2 — Creator Platform & Publisher Ecosystem tests."""

from __future__ import annotations

import importlib.util
import sys
import uuid
from datetime import datetime, timedelta, timezone
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
        "creator_platform",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    cp = sys.modules["app.services.creator_platform"]
    cp.get_creator_platform_service = sys.modules[
        "app.services.creator_platform.service"
    ].get_creator_platform_service
    cp.reset_engine = sys.modules["app.services.creator_platform.service"].reset_engine


_bootstrap()


def _cp():
    return sys.modules["app.services.creator_platform.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.creator_platform.version"]


def _catalog():
    return sys.modules["app.services.creator_platform.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    _bootstrap()
    mod = _cp()
    mod._service = None
    sys.modules["app.services.creator_platform.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"cp-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Creator Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _svc():
    return _cp().get_creator_platform_service()


def _make_creator(org_id: str, actor: str, **overrides):
    payload = {
        "organizationId": org_id,
        "displayName": f"Creator {actor}",
        "bio": "AI content creator",
        "categories": ["ai_art", "video"],
    }
    payload.update(overrides)
    return _svc().creators.create_profile(payload, actor_id=actor)


def _publish_asset(org_id: str, actor: str, **overrides):
    payload = {
        "organizationId": org_id,
        "name": "Neon City Video Template",
        "assetType": "video_template",
        "category": "video",
        "tags": ["neon", "city"],
        "assetUri": "https://cdn.rtas.example/assets/neon-city.zip",
        "priceCredits": 25.0,
    }
    payload.update(overrides)
    return _svc().publishing.publish(payload, actor_id=actor)


# --- Unit ---


def test_version_unit():
    v = _version()
    assert v.PHASE == 9
    assert v.SPRINT == 2
    assert "Creator Platform" in v.ENGINE_NAME


def test_catalog_unit():
    c = _catalog()
    assert "verified" in c.BADGE_DEFINITIONS
    assert "scheduled" in c.ASSET_STATUSES
    assert c.is_https_url("https://rtas.example") is True
    assert c.is_https_url("http://insecure.example") is False
    rep = c.compute_reputation(
        badges=3, downloads=50, purchases=10, avg_rating=4.5,
        followers=20, verified=True,
    )
    assert 0 < rep <= 100
    score = c.compute_engagement({"download": 10, "purchase": 2, "follower": 5})
    assert score == 10 * 1.0 + 2 * 3.0 + 5 * 2.5


def test_engine_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["phase"] == 9
    assert status["sprint"] == 2
    assert all(v == "ready" for v in status["engines"].values())
    assert len(status["engines"]) == 6


# --- Creator engine ---


def test_creator_profile_lifecycle():
    org_id = _seed_org("owner_p")
    created = _make_creator(org_id, "owner_p", socialLinks={"website": "https://me.example"})
    assert created["ok"] is True
    assert created["creator"]["verified"] is False
    assert created["profile"]["socialLinks"]["website"] == "https://me.example"
    assert created["profile"]["categories"] == ["ai_art", "video"]

    fetched = _svc().creators.get_profile(actor_id="owner_p", organization_id=org_id)
    assert fetched["creator"]["displayName"] == "Creator owner_p"
    assert fetched["followers"] == 0

    updated = _svc().creators.update_profile(
        {
            "displayName": "Studio Master",
            "bio": "Updated bio",
            "socialLinks": {"youtube": "https://youtube.example/c/me"},
            "categories": ["music"],
        },
        actor_id="owner_p",
        organization_id=org_id,
    )
    assert updated["creator"]["displayName"] == "Studio Master"
    assert updated["profile"]["categories"] == ["music"]

    # Duplicate profile rejected
    try:
        _make_creator(org_id, "owner_p")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_social_link_validation():
    org_id = _seed_org("owner_sl")
    try:
        _make_creator(org_id, "owner_sl", socialLinks={"website": "http://insecure.example"})
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "https" in str(exc).lower()
    try:
        _make_creator(org_id, "owner_sl", socialLinks={"myspace": "https://x.example"})
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_creator_categories_validation():
    org_id = _seed_org("owner_cc")
    try:
        _make_creator(org_id, "owner_cc", categories=["not_real"])
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_followers():
    org_id = _seed_org("owner_f")
    creator_id = _make_creator(org_id, "owner_f")["creator"]["id"]
    followed = _svc().creators.follow(
        creator_id, actor_id="editor_1", organization_id=org_id
    )
    assert followed["followers"] == 1
    # Double-follow rejected
    try:
        _svc().creators.follow(creator_id, actor_id="editor_1", organization_id=org_id)
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass
    # Self-follow rejected
    try:
        _svc().creators.follow(creator_id, actor_id="owner_f", organization_id=org_id)
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass
    unfollowed = _svc().creators.unfollow(
        creator_id, actor_id="editor_1", organization_id=org_id
    )
    assert unfollowed["followers"] == 0


# --- Verification engine ---


def test_verification_workflow():
    org_id = _seed_org("owner_vw")
    _make_creator(org_id, "editor_1")
    creator_id = _svc().creators.get_profile(
        actor_id="editor_1", organization_id=org_id
    )["creator"]["id"]

    requested = _svc().verification.request(
        actor_id="editor_1", organization_id=org_id, note="please verify"
    )
    assert requested["creator"]["verificationStatus"] == "pending"

    # Editor cannot review their own verification (needs org.update)
    try:
        _svc().verification.review(creator_id, actor_id="editor_1", approve=True)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass

    approved = _svc().verification.review(creator_id, actor_id="owner_vw", approve=True)
    assert approved["creator"]["verified"] is True

    # Verified badge awarded
    profile = _svc().creators.get_profile(
        actor_id="editor_1", organization_id=org_id
    )
    badge_keys = {b["badgeKey"] for b in profile["badges"]}
    assert "verified" in badge_keys

    # Re-request rejected once verified
    try:
        _svc().verification.request(actor_id="editor_1", organization_id=org_id)
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_verification_rejection():
    org_id = _seed_org("owner_vr")
    _make_creator(org_id, "editor_1")
    creator_id = _svc().creators.get_profile(
        actor_id="editor_1", organization_id=org_id
    )["creator"]["id"]
    _svc().verification.request(actor_id="editor_1", organization_id=org_id)
    rejected = _svc().verification.review(
        creator_id, actor_id="owner_vr", approve=False, note="need more info"
    )
    assert rejected["creator"]["verificationStatus"] == "rejected"
    assert rejected["creator"]["verified"] is False


# --- Publisher & publishing engines ---


def test_publish_immediately():
    org_id = _seed_org("owner_pub")
    _make_creator(org_id, "owner_pub")
    result = _publish_asset(org_id, "owner_pub")
    asset = result["asset"]
    assert asset["status"] == "published"
    assert asset["publishedAt"]
    assert asset["currentVersion"] == "1.0.0"


def test_publish_requires_creator_profile():
    org_id = _seed_org("owner_nc")
    try:
        _publish_asset(org_id, "owner_nc")
        assert False, "expected NotFoundError"
    except _errors().NotFoundError as exc:
        assert "creator profile" in str(exc).lower()


def test_draft_and_publish_later():
    org_id = _seed_org("owner_dr")
    _make_creator(org_id, "owner_dr")
    draft = _publish_asset(org_id, "owner_dr", draft=True)["asset"]
    assert draft["status"] == "draft"
    published = _svc().publishing.publish(
        {"assetId": draft["id"]}, actor_id="owner_dr"
    )["asset"]
    assert published["status"] == "published"


def test_scheduled_publishing():
    org_id = _seed_org("owner_sc")
    _make_creator(org_id, "owner_sc")
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    result = _publish_asset(org_id, "owner_sc", publishAt=future)
    assert result.get("scheduled") is True
    asset = result["asset"]
    assert asset["status"] == "scheduled"

    # Not due yet
    processed = _svc().publishing.process_due()
    assert processed["count"] == 0

    # Force the schedule into the past, then process
    store = sys.modules["app.services.creator_platform.store"]
    raw = store.get_asset(asset["id"])
    raw.publish_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    store.save_asset(raw)
    processed = _svc().publishing.process_due()
    assert processed["count"] == 1
    assert processed["published"][0]["status"] == "published"


def test_publish_requires_asset_uri():
    org_id = _seed_org("owner_nu")
    _make_creator(org_id, "owner_nu")
    try:
        _publish_asset(org_id, "owner_nu", assetUri="")
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "asseturi" in str(exc).lower()


def test_publisher_update_and_versioning():
    org_id = _seed_org("owner_uv")
    _make_creator(org_id, "owner_uv")
    asset = _publish_asset(org_id, "owner_uv")["asset"]
    updated = _svc().publisher.update(
        asset["id"],
        {
            "name": "Neon City v2",
            "version": "1.1.0",
            "changelog": "New scenes",
            "visibility": "organization",
            "priceCredits": 30.0,
        },
        actor_id="owner_uv",
    )["asset"]
    assert updated["name"] == "Neon City v2"
    assert updated["currentVersion"] == "1.1.0"
    assert updated["visibility"] == "organization"
    assert len(updated["versions"]) == 2

    # Duplicate version rejected
    try:
        _svc().publisher.update(asset["id"], {"version": "1.1.0"}, actor_id="owner_uv")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_publisher_archive_and_delete():
    org_id = _seed_org("owner_ar")
    _make_creator(org_id, "owner_ar")
    asset = _publish_asset(org_id, "owner_ar")["asset"]
    archived = _svc().publisher.update(
        asset["id"], {"status": "archived"}, actor_id="owner_ar"
    )["asset"]
    assert archived["status"] == "archived"
    deleted = _svc().publisher.delete(asset["id"], actor_id="owner_ar")
    assert deleted["status"] == "deleted"
    listed = _svc().publisher.list(actor_id="owner_ar", organization_id=org_id)
    assert listed["count"] == 0


def test_publisher_asset_listing():
    org_id = _seed_org("owner_ls")
    _make_creator(org_id, "owner_ls")
    _publish_asset(org_id, "owner_ls", name="Asset A")
    _publish_asset(org_id, "owner_ls", name="Asset B", draft=True)
    all_assets = _svc().publisher.list(actor_id="owner_ls", organization_id=org_id)
    assert all_assets["count"] == 2
    drafts = _svc().publisher.list(
        actor_id="owner_ls", organization_id=org_id, status="draft"
    )
    assert drafts["count"] == 1


# --- Portfolio engine ---


def test_portfolio_management():
    org_id = _seed_org("owner_pf")
    _make_creator(org_id, "owner_pf")
    asset = _publish_asset(org_id, "owner_pf")["asset"]
    added = _svc().portfolio.add_item(
        {
            "title": "Showcase Reel",
            "description": "Best work of 2026",
            "mediaUri": "https://cdn.rtas.example/reel.mp4",
            "assetId": asset["id"],
        },
        actor_id="owner_pf",
        organization_id=org_id,
    )
    assert added["ok"] is True
    item_id = added["item"]["id"]

    featured = _svc().portfolio.set_featured(
        [asset["id"]], actor_id="owner_pf", organization_id=org_id
    )
    assert featured["featuredAssetIds"] == [asset["id"]]

    fetched = _svc().portfolio.get(actor_id="owner_pf", organization_id=org_id)
    assert len(fetched["portfolio"]) == 1

    removed = _svc().portfolio.remove_item(
        item_id, actor_id="owner_pf", organization_id=org_id
    )
    assert removed["portfolio"] == []


def test_portfolio_cannot_reference_foreign_asset():
    org_id = _seed_org("owner_pa")
    _make_creator(org_id, "owner_pa")
    _make_creator(org_id, "editor_1")
    foreign_asset = _publish_asset(org_id, "editor_1", name="Editor Asset")["asset"]
    try:
        _svc().portfolio.set_featured(
            [foreign_asset["id"]], actor_id="owner_pa", organization_id=org_id
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


# --- Analytics engine ---


def test_creator_analytics_summary():
    org_id = _seed_org("owner_an")
    creator_id = _make_creator(org_id, "owner_an")["creator"]["id"]
    asset = _publish_asset(org_id, "owner_an")["asset"]

    svc = _svc()
    for _ in range(3):
        svc.analytics.record_event(
            {"creatorId": creator_id, "eventType": "download", "assetId": asset["id"]},
        )
    svc.analytics.record_event(
        {
            "creatorId": creator_id,
            "eventType": "purchase",
            "assetId": asset["id"],
            "amountCredits": 25.0,
        },
    )
    svc.analytics.record_event(
        {"creatorId": creator_id, "eventType": "rating", "rating": 5},
    )
    svc.analytics.record_event(
        {"creatorId": creator_id, "eventType": "review"},
    )
    svc.creators.follow(creator_id, actor_id="editor_1", organization_id=org_id)

    summary = svc.analytics.summary(actor_id="owner_an", organization_id=org_id)[
        "analytics"
    ]
    assert summary["totalAssets"] == 1
    assert summary["publishedAssets"] == 1
    assert summary["downloads"] == 3
    assert summary["purchases"] == 1
    assert summary["revenueCredits"] == 25.0
    assert summary["followers"] == 1
    assert summary["avgRating"] == 5.0
    assert summary["reviews"] == 1
    assert summary["engagementScore"] > 0
    assert summary["reputation"] > 0
    badge_keys = {b["badgeKey"] for b in summary["badges"]}
    assert "first_publish" in badge_keys


def test_analytics_rating_validation():
    org_id = _seed_org("owner_rv")
    creator_id = _make_creator(org_id, "owner_rv")["creator"]["id"]
    try:
        _svc().analytics.record_event(
            {"creatorId": creator_id, "eventType": "rating", "rating": 9},
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_badge_milestones():
    org_id = _seed_org("owner_bm")
    creator_id = _make_creator(org_id, "owner_bm")["creator"]["id"]
    catalog = _catalog()
    for i in range(catalog.PROLIFIC_THRESHOLD):
        _publish_asset(org_id, "owner_bm", name=f"Milestone Asset {i}")
    profile = _svc().creators.get_profile(actor_id="owner_bm", organization_id=org_id)
    badge_keys = {b["badgeKey"] for b in profile["badges"]}
    assert "first_publish" in badge_keys
    assert "prolific_creator" in badge_keys
    # Popular badge after 100 downloads
    for _ in range(catalog.POPULAR_DOWNLOADS_THRESHOLD):
        _svc().analytics.record_event(
            {"creatorId": creator_id, "eventType": "download"},
        )
    profile = _svc().creators.get_profile(actor_id="owner_bm", organization_id=org_id)
    badge_keys = {b["badgeKey"] for b in profile["badges"]}
    assert "popular" in badge_keys


# --- Security ---


def test_security_creator_ownership():
    org_id = _seed_org("owner_so")
    _make_creator(org_id, "owner_so")
    # editor_1 has no creator profile; updating another's profile is impossible
    # because update_profile resolves the actor's own profile only.
    try:
        _svc().creators.update_profile(
            {"displayName": "Hijack"}, actor_id="editor_1", organization_id=org_id
        )
        assert False, "expected NotFoundError"
    except _errors().NotFoundError:
        pass


def test_security_publisher_permissions():
    org_id = _seed_org("owner_pp")
    _make_creator(org_id, "owner_pp")
    _make_creator(org_id, "editor_1")
    asset = _publish_asset(org_id, "owner_pp")["asset"]
    # editor cannot update or delete the owner's asset
    try:
        _svc().publisher.update(asset["id"], {"name": "Stolen"}, actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        _svc().publisher.delete(asset["id"], actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


def test_security_organization_isolation():
    org_a = _seed_org("owner_oa")
    org_b = _seed_org("owner_ob")
    _make_creator(org_a, "owner_oa")
    creator_a = _svc().creators.get_profile(
        actor_id="owner_oa", organization_id=org_a
    )["creator"]["id"]
    # Foreign org member cannot read another org's creator profile or assets
    try:
        _svc().creators.get_profile(
            actor_id="owner_ob", organization_id=org_b, creator_id=creator_a
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        _svc().publisher.list(actor_id="owner_ob", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    # Non-member cannot create a profile in a foreign org
    try:
        _make_creator(org_a, "owner_ob")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


def test_security_audit_logging():
    org_id = _seed_org("owner_al")
    audit_store = sys.modules["app.services.enterprise_auth.store"]
    _make_creator(org_id, "owner_al")
    _publish_asset(org_id, "owner_al")
    events = audit_store.list_audits(limit=500)
    actions = {e.event_type for e in events}
    assert "creator_platform.profile_created" in actions
    assert "creator_platform.asset_published" in actions


# --- Integration ---


def test_full_creator_publisher_workflow():
    """Profile -> verify -> publish -> version -> engage -> analytics."""
    org_id = _seed_org("owner_full")
    svc = _svc()
    creator_id = _make_creator(org_id, "editor_1")["creator"]["id"]
    svc.verification.request(actor_id="editor_1", organization_id=org_id)
    svc.verification.review(creator_id, actor_id="owner_full", approve=True)

    asset = _publish_asset(org_id, "editor_1", name="Verified Asset")["asset"]
    svc.publisher.update(
        asset["id"], {"version": "1.1.0", "changelog": "polish"}, actor_id="editor_1"
    )
    svc.analytics.record_event(
        {"creatorId": creator_id, "eventType": "purchase", "amountCredits": 25.0},
    )
    svc.creators.follow(creator_id, actor_id="owner_full", organization_id=org_id)

    summary = svc.analytics.summary(actor_id="editor_1", organization_id=org_id)[
        "analytics"
    ]
    assert summary["verified"] is True
    assert summary["publishedAssets"] == 1
    assert summary["revenueCredits"] == 25.0
    assert summary["followers"] == 1
    badge_keys = {b["badgeKey"] for b in summary["badges"]}
    assert {"verified", "first_publish"} <= badge_keys

    status = svc.status()
    assert status["stats"]["creators"] == 1
    assert status["stats"]["assets"] == 1
