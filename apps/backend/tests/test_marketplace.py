"""Phase 8 Sprint 9 — Marketplace, Template Store & Digital Commerce tests."""

from __future__ import annotations

import importlib.util
import sys
import time
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
        "marketplace",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    mk = sys.modules["app.services.marketplace"]
    mk.get_marketplace_service = sys.modules[
        "app.services.marketplace.service"
    ].get_marketplace_service
    mk.reset_engine = sys.modules["app.services.marketplace.service"].reset_engine


_bootstrap()


def _mk():
    return sys.modules["app.services.marketplace.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.marketplace.version"]


def _catalog():
    return sys.modules["app.services.marketplace.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    _bootstrap()
    mod = _mk()
    mod._service = None
    sys.modules["app.services.marketplace.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"mk-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Marketplace Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _svc():
    return _mk().get_marketplace_service()


def _publish(org_id: str, actor: str, **overrides):
    payload = {
        "organizationId": org_id,
        "name": "Cinematic LUT Pack",
        "productType": "lut_pack",
        "description": "Professional cinematic color grading LUTs",
        "category": "effects",
        "tags": ["cinematic", "color", "video"],
        "pricingModel": "premium",
        "priceCredits": 50.0,
        "licenseType": "commercial",
    }
    payload.update(overrides)
    return _svc().templates.publish(payload, actor_id=actor)["product"]


# --- Unit ---


def test_version_unit():
    v = _version()
    assert v.PHASE == 8
    assert v.SPRINT == 9
    assert "Marketplace" in v.ENGINE_NAME
    assert "Digital Commerce" in v.ENGINE_NAME


def test_catalog_unit():
    c = _catalog()
    for pt in (
        "prompt_template", "ai_workflow", "character", "avatar", "voice_pack",
        "music_pack", "video_template", "image_template", "brand_kit",
        "logo_pack", "lut_pack", "preset", "custom",
    ):
        assert pt in c.PRODUCT_TYPES
    key = c.generate_license_key()
    assert key.startswith("RTASMKT-")
    assert len(c.generate_download_token()) > 20
    assert c.RATING_MIN == 1 and c.RATING_MAX == 5


def test_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["sprint"] == 9
    for engine in (
        "marketplace",
        "templateStore",
        "digitalProduct",
        "productCatalog",
        "marketplaceSearch",
        "marketplaceAnalytics",
    ):
        assert status["engines"][engine] == "ready"


# --- Template store / product lifecycle ---


def test_publish_update_archive_delete():
    org_id = _seed_org("owner_pl")
    svc = _svc()
    product = _publish(org_id, "owner_pl")
    assert product["status"] == "published"
    assert product["priceCredits"] == 50.0
    assert product["tags"] == ["cinematic", "color", "video"]

    updated = svc.templates.update(
        product["id"],
        {"description": "Updated description", "featured": True},
        actor_id="owner_pl",
    )["product"]
    assert updated["description"] == "Updated description"
    assert updated["featured"] is True

    # New version
    versioned = svc.templates.update(
        product["id"],
        {"version": "1.1.0", "changelog": "added 10 new LUTs"},
        actor_id="owner_pl",
    )["product"]
    assert versioned["currentVersion"] == "1.1.0"
    versions = svc.templates.versions(product["id"])
    assert versions["count"] == 2
    assert versions["versions"][0]["version"] == "1.1.0"

    archived = svc.templates.archive(product["id"], actor_id="owner_pl")["product"]
    assert archived["status"] == "archived"
    try:
        svc.templates.update(product["id"], {"name": "x"}, actor_id="owner_pl")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass

    deleted = svc.templates.delete(product["id"], actor_id="owner_pl")
    assert deleted["deleted"] is True
    try:
        svc.catalog.get(product["id"])
        assert False, "expected NotFoundError"
    except _errors().NotFoundError:
        pass


def test_publish_validation():
    org_id = _seed_org("owner_pv")
    svc = _svc()
    ValidationError = _validation().ValidationError
    try:
        _publish(org_id, "owner_pv", productType="nft")
        assert False
    except ValidationError as exc:
        assert "unknown product type" in str(exc)
    try:
        _publish(org_id, "owner_pv", pricingModel="premium", priceCredits=0)
        assert False
    except ValidationError as exc:
        assert "priceCredits" in str(exc)
    # Free products are always 0 credits
    free = _publish(
        org_id, "owner_pv", name="Free Preset", pricingModel="free", priceCredits=99
    )
    assert free["priceCredits"] == 0.0


# --- Catalog ---


def test_catalog_listing_and_views():
    org_id = _seed_org("owner_cl")
    svc = _svc()
    _publish(org_id, "owner_cl", name="LUT Pack A", category="effects")
    _publish(
        org_id, "owner_cl", name="Avatar Bundle", productType="avatar",
        category="characters", pricingModel="free", priceCredits=0,
    )
    all_products = svc.catalog.list()
    assert all_products["count"] == 2
    effects = svc.catalog.list(category="effects")
    assert effects["count"] == 1
    free = svc.catalog.list(pricing_model="free")
    assert free["count"] == 1
    assert free["products"][0]["name"] == "Avatar Bundle"

    detail = svc.catalog.get(all_products["products"][0]["id"], viewer_id="user_x")
    assert detail["product"]["stats"]["views"] == 1
    categories = svc.catalog.categories()
    assert categories["categories"]["effects"] == 1
    tags = svc.catalog.tags()
    assert tags["tags"]["cinematic"] == 2


# --- Search & discovery ---


def test_search_full_text_category_tag():
    org_id = _seed_org("owner_se")
    svc = _svc()
    _publish(org_id, "owner_se", name="Cinematic LUT Pack", tags=["cinematic", "film"])
    _publish(
        org_id, "owner_se", name="Podcast Voice Pack", productType="voice_pack",
        category="audio", tags=["voice", "podcast"],
    )
    _publish(
        org_id, "owner_se", name="Neon Logo Pack", productType="logo_pack",
        category="branding", tags=["logo", "neon"],
    )

    results = svc.search.search("cinematic lut")
    assert results["count"] >= 1
    assert results["results"][0]["product"]["name"] == "Cinematic LUT Pack"

    by_category = svc.search.search("", category="audio")
    assert by_category["count"] == 1
    assert by_category["results"][0]["product"]["name"] == "Podcast Voice Pack"

    by_tag = svc.search.search("", tag="neon")
    assert by_tag["count"] == 1

    no_match = svc.search.search("quantum blockchain")
    assert no_match["count"] == 0


def test_semantic_search_and_discovery():
    org_id = _seed_org("owner_ds")
    svc = _svc()
    popular = _publish(
        org_id, "owner_ds", name="Pro Video Template", productType="video_template",
        category="video", tags=["video", "intro"], featured=True,
    )
    fresh = _publish(
        org_id, "owner_ds", name="Video Intro Template", productType="video_template",
        category="video", tags=["video", "intro"],
    )
    # Buyer purchases + reviews the popular product
    buyer_org = _seed_org("buyer_ds")
    svc.commerce.purchase(
        {"productId": popular["id"], "organizationId": buyer_org}, actor_id="buyer_ds"
    )
    svc.commerce.review(
        {"productId": popular["id"], "rating": 5, "title": "great"}, actor_id="buyer_ds"
    )

    semantic = svc.search.search("video template", semantic=True)
    assert semantic["results"][0]["product"]["id"] == popular["id"]

    discovery = svc.search.discovery("buyer_ds")
    assert any(p["id"] == popular["id"] for p in discovery["featured"])
    assert discovery["trending"][0]["id"] == popular["id"]
    assert len(discovery["newReleases"]) == 2
    # Recommended excludes owned products, prefers bought category
    rec_ids = [p["id"] for p in discovery["recommended"]]
    assert popular["id"] not in rec_ids
    assert fresh["id"] in rec_ids


# --- Purchases, licenses, downloads ---


def test_purchase_license_and_history():
    org_id = _seed_org("owner_pu")
    buyer_org = _seed_org("buyer_1")
    svc = _svc()
    product = _publish(org_id, "owner_pu")

    result = svc.commerce.purchase(
        {"productId": product["id"], "organizationId": buyer_org}, actor_id="buyer_1"
    )
    purchase = result["purchase"]
    license_ = result["license"]
    assert purchase["priceCredits"] == 50.0
    assert purchase["status"] == "completed"
    assert license_["licenseKey"].startswith("RTASMKT-")
    assert license_["licenseType"] == "commercial"
    assert license_["status"] == "active"

    # Double purchase blocked
    try:
        svc.commerce.purchase(
            {"productId": product["id"], "organizationId": buyer_org}, actor_id="buyer_1"
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "already purchased" in str(exc)

    history = svc.commerce.purchases(actor_id="buyer_1", organization_id=buyer_org)
    assert history["count"] == 1

    validated = svc.commerce.validate_license(license_["licenseKey"])
    assert validated["valid"] is True
    assert svc.commerce.validate_license("RTASMKT-XXXX")["valid"] is False


def test_secure_download_flow():
    org_id = _seed_org("owner_dl")
    buyer_org = _seed_org("buyer_dl")
    svc = _svc()
    product = _publish(org_id, "owner_dl")

    # Unlicensed user cannot request a download
    try:
        svc.commerce.request_download(product["id"], actor_id="buyer_dl")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass

    svc.commerce.purchase(
        {"productId": product["id"], "organizationId": buyer_org}, actor_id="buyer_dl"
    )
    grant = svc.commerce.request_download(product["id"], actor_id="buyer_dl")["download"]
    assert grant["token"]
    assert "token=" in grant["url"]

    # Another user cannot redeem the grant
    try:
        svc.commerce.redeem_download(grant["token"], actor_id="someone_else")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass

    redeemed = svc.commerce.redeem_download(grant["token"], actor_id="buyer_dl")
    assert redeemed["productId"] == product["id"]
    assert redeemed["assetUri"]

    # Single-use token
    try:
        svc.commerce.redeem_download(grant["token"], actor_id="buyer_dl")
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "already used" in str(exc)

    # Expired grants rejected
    grant2 = svc.commerce.request_download(product["id"], actor_id="buyer_dl")["download"]
    store = sys.modules["app.services.marketplace.store"]
    raw = store.get_grant(grant2["token"])
    raw.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    store.save_grant(raw)
    try:
        svc.commerce.redeem_download(grant2["token"], actor_id="buyer_dl")
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "expired" in str(exc)

    # Seller can always download own product
    seller_grant = svc.commerce.request_download(product["id"], actor_id="owner_dl")
    assert seller_grant["ok"] is True


def test_refund_revokes_license():
    org_id = _seed_org("owner_rf")
    buyer_org = _seed_org("buyer_rf")
    svc = _svc()
    product = _publish(org_id, "owner_rf")
    result = svc.commerce.purchase(
        {"productId": product["id"], "organizationId": buyer_org}, actor_id="buyer_rf"
    )
    refunded = svc.commerce.refund(result["purchase"]["id"], actor_id="buyer_rf")
    assert refunded["purchase"]["status"] == "refunded"
    assert refunded["licenseRevoked"] is True
    assert (
        svc.commerce.validate_license(result["license"]["licenseKey"])["valid"] is False
    )
    # Product stats updated
    detail = sys.modules["app.services.marketplace.store"].get_product(product["id"])
    assert detail.refunds == 1
    assert detail.revenue_credits == 0.0
    # Double refund blocked
    try:
        svc.commerce.refund(result["purchase"]["id"], actor_id="buyer_rf")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


# --- Reviews & ratings ---


def test_reviews_and_ratings():
    org_id = _seed_org("owner_rv")
    buyer_org = _seed_org("buyer_rv")
    svc = _svc()
    product = _publish(org_id, "owner_rv")

    # Non-buyer cannot review
    try:
        svc.commerce.review(
            {"productId": product["id"], "rating": 5}, actor_id="rando"
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass

    svc.commerce.purchase(
        {"productId": product["id"], "organizationId": buyer_org}, actor_id="buyer_rv"
    )
    review = svc.commerce.review(
        {"productId": product["id"], "rating": 4, "title": "solid", "body": "good LUTs"},
        actor_id="buyer_rv",
    )["review"]
    assert review["rating"] == 4

    # Duplicate review blocked
    try:
        svc.commerce.review({"productId": product["id"], "rating": 5}, actor_id="buyer_rv")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass

    # Out-of-range rating blocked
    try:
        svc.commerce.review({"productId": product["id"], "rating": 9}, actor_id="buyer_rv")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass

    detail = svc.catalog.get(product["id"])
    assert detail["product"]["stats"]["avgRating"] == 4.0
    assert detail["product"]["stats"]["ratingCount"] == 1
    assert len(detail["recentReviews"]) == 1


# --- Analytics ---


def test_marketplace_analytics():
    org_id = _seed_org("owner_an")
    buyer_org = _seed_org("buyer_an")
    svc = _svc()
    hit = _publish(org_id, "owner_an", name="Best Seller", priceCredits=100.0)
    _publish(org_id, "owner_an", name="Slow Seller", priceCredits=10.0)

    svc.catalog.get(hit["id"], viewer_id="buyer_an")
    svc.commerce.purchase(
        {"productId": hit["id"], "organizationId": buyer_org}, actor_id="buyer_an"
    )
    grant = svc.commerce.request_download(hit["id"], actor_id="buyer_an")["download"]
    svc.commerce.redeem_download(grant["token"], actor_id="buyer_an")
    svc.commerce.review({"productId": hit["id"], "rating": 5}, actor_id="buyer_an")

    analytics = svc.analytics.analytics(actor_id="owner_an", organization_id=org_id)
    stats = analytics["analytics"]
    assert stats["products"] == 2
    assert stats["views"] == 1
    assert stats["downloads"] == 1
    assert stats["purchases"] == 1
    assert stats["revenueCredits"] == 100.0
    assert stats["avgRating"] == 5.0
    assert stats["reviews"] == 1
    assert analytics["bestSelling"][0]["name"] == "Best Seller"


# --- Security ---


def test_ownership_and_isolation():
    org_a = _seed_org("owner_sa")
    org_b = _seed_org("owner_sb")
    svc = _svc()
    product = _publish(org_a, "owner_sa")

    # Foreign user cannot update/archive/delete another org's product
    for call in (
        lambda: svc.templates.update(product["id"], {"name": "hacked"}, actor_id="owner_sb"),
        lambda: svc.templates.archive(product["id"], actor_id="owner_sb"),
        lambda: svc.templates.delete(product["id"], actor_id="owner_sb"),
    ):
        try:
            call()
            assert False, "expected ForbiddenError"
        except _errors().ForbiddenError:
            pass

    # Org manager (not seller) CAN manage the product
    editor_product = _publish(org_a, "editor_1", name="Editor Product", pricingModel="free", priceCredits=0)
    managed = svc.templates.update(
        editor_product["id"], {"featured": True}, actor_id="owner_sa"
    )
    assert managed["product"]["featured"] is True
    # But plain editor cannot manage the owner's product
    try:
        svc.templates.update(product["id"], {"name": "nope"}, actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass

    # Analytics are org-isolated
    try:
        svc.analytics.analytics(actor_id="owner_sb", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    isolated = svc.analytics.analytics(actor_id="owner_sb", organization_id=org_b)
    assert isolated["analytics"]["products"] == 0

    # Purchase history is org-isolated
    try:
        svc.commerce.purchases(actor_id="owner_sb", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


# --- Performance ---


def test_performance_bulk_catalog_and_search():
    org_id = _seed_org("owner_perf")
    svc = _svc()
    types = ["lut_pack", "preset", "avatar", "voice_pack", "video_template"]
    cats = ["effects", "other", "characters", "audio", "video"]
    start = time.perf_counter()
    for i in range(200):
        _publish(
            org_id,
            "owner_perf",
            name=f"Asset {i} cinematic pack",
            productType=types[i % 5],
            category=cats[i % 5],
            tags=[f"tag{i % 10}", "cinematic"],
            pricingModel="free",
            priceCredits=0,
        )
    results = svc.search.search("cinematic", limit=50)
    listing = svc.catalog.list(limit=500)
    elapsed = time.perf_counter() - start
    assert elapsed < 10.0
    assert results["count"] == 50
    assert listing["count"] == 200
    metrics = sys.modules["app.services.marketplace.store"].metrics()
    assert metrics["errorCount"] == 0
