"""Phase 9 Sprint 4 — Template Store, Versioning & Asset Management tests."""

from __future__ import annotations

import importlib.util
import sys
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
        "template_store",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    ts = sys.modules["app.services.template_store"]
    ts.get_template_store_service = sys.modules[
        "app.services.template_store.service"
    ].get_template_store_service
    ts.reset_engine = sys.modules["app.services.template_store.service"].reset_engine


_bootstrap()


def _ts():
    return sys.modules["app.services.template_store.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.template_store.version"]


def _catalog():
    return sys.modules["app.services.template_store.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    _bootstrap()
    mod = _ts()
    mod._service = None
    sys.modules["app.services.template_store.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"ts-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Template Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _svc():
    return _ts().get_template_store_service()


def _upload(org_id: str, actor: str, **overrides):
    payload = {
        "organizationId": org_id,
        "name": "Cinematic Intro",
        "templateType": "video_template",
        "description": "Epic cinematic intro template",
        "category": "video",
        "tags": ["cinematic", "intro"],
        "assetUri": "https://cdn.rtas.example/templates/cinematic-intro.zip",
    }
    payload.update(overrides)
    return _svc().templates.upload(payload, actor_id=actor)


# --- Unit ---


def test_version_unit():
    v = _version()
    assert v.PHASE == 9
    assert v.SPRINT == 4
    assert "Template Store" in v.ENGINE_NAME


def test_catalog_unit():
    c = _catalog()
    assert "video_template" in c.TEMPLATE_TYPES
    assert c.is_semver("1.2.3") is True
    assert c.is_semver("1.2") is False
    assert c.slugify("My Great Template!") == "my-great-template"
    tokens = c.tokenize("Epic Cinematic Intro", "video")
    assert {"epic", "cinematic", "intro", "video"} <= tokens
    checksum = c.version_checksum("t1", "1.0.0", "https://x/a.zip", "Name")
    assert len(checksum) == 64
    assert checksum == c.version_checksum("t1", "1.0.0", "https://x/a.zip", "Name")
    assert checksum != c.version_checksum("t1", "1.0.1", "https://x/a.zip", "Name")


def test_engine_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["phase"] == 9
    assert status["sprint"] == 4
    assert len(status["engines"]) == 6
    assert all(v == "ready" for v in status["engines"].values())


# --- Template store engine ---


def test_upload_and_get_template():
    org_id = _seed_org("owner_u")
    created = _upload(org_id, "owner_u")
    template = created["template"]
    assert template["status"] == "active"
    assert template["currentVersion"] == "1.0.0"
    assert template["slug"] == "cinematic-intro"

    fetched = _svc().templates.get(template["id"], actor_id="owner_u")
    assert fetched["template"]["name"] == "Cinematic Intro"
    assert len(fetched["versions"]) == 1
    assert fetched["versions"][0]["checksum"]


def test_upload_validation():
    org_id = _seed_org("owner_v")
    try:
        _upload(org_id, "owner_v", templateType="hologram_template")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass
    try:
        _upload(org_id, "owner_v", category="not_a_category")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass
    try:
        _upload(org_id, "owner_v", assetUri="")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_update_template():
    org_id = _seed_org("owner_up")
    template = _upload(org_id, "owner_up")["template"]
    updated = _svc().templates.update(
        template["id"],
        {
            "name": "Cinematic Intro Pro",
            "tags": ["cinematic", "pro"],
            "featured": True,
            "category": "video",
        },
        actor_id="owner_up",
    )["template"]
    assert updated["name"] == "Cinematic Intro Pro"
    assert updated["featured"] is True
    assert updated["tags"] == ["cinematic", "pro"]
    # Tag registry updated: 'intro' released, 'pro' added
    tags = {t["slug"] for t in _svc().tags.list()["tags"]}
    assert "pro" in tags
    assert "intro" not in tags


def test_archive_restore_delete():
    org_id = _seed_org("owner_ar")
    template = _upload(org_id, "owner_ar")["template"]
    tid = template["id"]

    archived = _svc().templates.archive(tid, actor_id="owner_ar")
    assert archived["template"]["status"] == "archived"

    restored = _svc().templates.restore(tid, actor_id="owner_ar")
    assert restored["template"]["status"] == "active"

    deleted = _svc().templates.delete(tid, actor_id="owner_ar")
    assert deleted["status"] == "deleted"
    try:
        _svc().templates.get(tid, actor_id="owner_ar")
        assert False, "expected NotFoundError"
    except _errors().NotFoundError:
        pass
    # Deleted templates disappear from listings and search
    listed = _svc().templates.list(actor_id="owner_ar", organization_id=org_id)
    assert listed["count"] == 0


def test_duplicate_template():
    org_id = _seed_org("owner_dp")
    original = _upload(org_id, "owner_dp")["template"]
    copy = _svc().templates.duplicate(original["id"], actor_id="editor_1")["template"]
    assert copy["id"] != original["id"]
    assert copy["name"] == "Cinematic Intro (Copy)"
    assert copy["ownerUserId"] == "editor_1"
    assert copy["tags"] == original["tags"]
    versions = _svc().versioning.history(copy["id"], actor_id="editor_1")
    assert versions["count"] == 1
    assert "Duplicated from" in versions["versions"][0]["changelog"]


def test_rating_and_downloads():
    org_id = _seed_org("owner_rd")
    template = _upload(org_id, "owner_rd")["template"]
    tid = template["id"]

    rated = _svc().templates.rate(tid, 5, actor_id="editor_1")
    assert rated["avgRating"] == 5.0
    # Duplicate rating rejected
    try:
        _svc().templates.rate(tid, 3, actor_id="editor_1")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass
    # Out-of-range rejected
    try:
        _svc().templates.rate(tid, 7, actor_id="owner_rd")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass

    downloaded = _svc().templates.record_download(tid, actor_id="editor_1")
    assert downloaded["downloads"] == 1
    assert downloaded["assetUri"]


# --- Versioning engine ---


def test_version_publish_and_history():
    org_id = _seed_org("owner_vp")
    template = _upload(org_id, "owner_vp")["template"]
    tid = template["id"]

    published = _svc().versioning.publish_version(
        tid,
        {
            "version": "1.1.0",
            "changelog": "Added transitions",
            "assetUri": "https://cdn.rtas.example/templates/cinematic-intro-1.1.zip",
        },
        actor_id="owner_vp",
    )["version"]
    assert published["version"] == "1.1.0"

    history = _svc().versioning.history(tid, actor_id="owner_vp")
    assert history["count"] == 2
    assert history["currentVersion"] == "1.1.0"

    # Invalid + duplicate versions rejected
    try:
        _svc().versioning.publish_version(
            tid, {"version": "not-semver"}, actor_id="owner_vp"
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass
    try:
        _svc().versioning.publish_version(
            tid, {"version": "1.1.0"}, actor_id="owner_vp"
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_version_integrity():
    org_id = _seed_org("owner_vi")
    template = _upload(org_id, "owner_vi")["template"]
    tid = template["id"]
    result = _svc().versioning.verify_integrity(tid, "1.0.0", actor_id="owner_vi")
    assert result["valid"] is True

    # Tampering with the stored version breaks integrity
    raw_store = sys.modules["app.services.template_store.store"]
    record = raw_store.get_version(tid, "1.0.0")
    record.asset_uri = "https://evil.example/swapped.zip"
    raw_store.save_version(record)
    result = _svc().versioning.verify_integrity(tid, "1.0.0", actor_id="owner_vi")
    assert result["valid"] is False


def test_rollback():
    org_id = _seed_org("owner_rb")
    template = _upload(org_id, "owner_rb")["template"]
    tid = template["id"]
    _svc().versioning.publish_version(
        tid,
        {"version": "2.0.0", "assetUri": "https://cdn.rtas.example/v2.zip"},
        actor_id="owner_rb",
    )
    rolled = _svc().versioning.rollback(tid, "1.0.0", actor_id="owner_rb")
    assert rolled["rolledBackTo"] == "1.0.0"
    assert rolled["template"]["currentVersion"] == "1.0.0"
    assert rolled["template"]["assetUri"].endswith("cinematic-intro.zip")
    # Rollback to current version rejected
    try:
        _svc().versioning.rollback(tid, "1.0.0", actor_id="owner_rb")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass
    # Rollback to unknown version rejected
    try:
        _svc().versioning.rollback(tid, "9.9.9", actor_id="owner_rb")
        assert False, "expected NotFoundError"
    except _errors().NotFoundError:
        pass


# --- Libraries & collections ---


def test_libraries():
    org_id = _seed_org("owner_lb")
    library = _svc().libraries.create_library(
        {"organizationId": org_id, "name": "Brand Kit Library"},
        actor_id="owner_lb",
    )["library"]
    _upload(org_id, "owner_lb", libraryId=library["id"])
    listed = _svc().libraries.list_libraries(
        actor_id="owner_lb", organization_id=org_id
    )
    assert listed["count"] == 1
    assert listed["libraries"][0]["templates"] == 1
    # Unknown library rejected on upload
    try:
        _upload(org_id, "owner_lb", name="Another", libraryId="lib_missing")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_collections():
    org_id = _seed_org("owner_cl")
    t1 = _upload(org_id, "owner_cl", name="Template A")["template"]
    t2 = _upload(org_id, "owner_cl", name="Template B")["template"]
    collection = _svc().libraries.create_collection(
        {
            "organizationId": org_id,
            "name": "Starter Pack",
            "templateIds": [t1["id"], t2["id"]],
        },
        actor_id="owner_cl",
    )["collection"]
    assert len(collection["templateIds"]) == 2
    listed = _svc().libraries.list_collections(
        actor_id="owner_cl", organization_id=org_id
    )
    assert listed["count"] == 1
    # Foreign/unknown template rejected
    try:
        _svc().libraries.create_collection(
            {"organizationId": org_id, "name": "Bad", "templateIds": ["tpl_missing"]},
            actor_id="owner_cl",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


# --- Categories & tags ---


def test_categories():
    org_id = _seed_org("owner_ct")
    listed = _svc().categories.list()
    slugs = {c["slug"] for c in listed["categories"]}
    assert {"video", "image", "prompt", "workflow"} <= slugs

    upserted = _svc().categories.upsert(
        {"organizationId": org_id, "slug": "3D Motion", "label": "3D Motion"},
        actor_id="owner_ct",
    )
    assert upserted["category"]["slug"] == "3d-motion"
    # Non-manager cannot manage categories
    try:
        _svc().categories.upsert(
            {"organizationId": org_id, "slug": "hack"}, actor_id="editor_1"
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


def test_tags_registry():
    org_id = _seed_org("owner_tg")
    _upload(org_id, "owner_tg", tags=["neon", "retro"])
    _upload(org_id, "owner_tg", name="Second", tags=["neon"])
    tags = {t["slug"]: t["usageCount"] for t in _svc().tags.list()["tags"]}
    assert tags["neon"] == 2
    assert tags["retro"] == 1
    # Tag cap enforced
    try:
        _upload(
            org_id, "owner_tg", name="Overtagged",
            tags=[f"tag{i}" for i in range(25)],
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


# --- Search & filtering ---


def test_full_text_search():
    org_id = _seed_org("owner_s")
    _upload(
        org_id, "owner_s", name="Neon City Nights",
        description="Cyberpunk neon video", tags=["neon"],
    )
    _upload(
        org_id, "owner_s", name="Forest Ambience",
        description="Calm nature soundscape", templateType="music_template",
        category="music",
    )
    results = _svc().search.search(
        actor_id="owner_s", organization_id=org_id, query="neon cyberpunk"
    )
    assert results["count"] == 1
    assert results["results"][0]["name"] == "Neon City Nights"
    # No match
    results = _svc().search.search(
        actor_id="owner_s", organization_id=org_id, query="underwater"
    )
    assert results["count"] == 0


def test_search_filters():
    org_id = _seed_org("owner_sf")
    svc = _svc()
    a = _upload(
        org_id, "owner_sf", name="Video One", category="video", tags=["intro"],
    )["template"]
    b = _upload(
        org_id, "editor_1", name="Music One", templateType="music_template",
        category="music", tags=["chill"], featured=True,
    )["template"]
    svc.templates.rate(a["id"], 5, actor_id="editor_1")
    for _ in range(3):
        svc.templates.record_download(b["id"], actor_id="owner_sf")

    by_category = svc.search.search(
        actor_id="owner_sf", organization_id=org_id, category="music"
    )
    assert by_category["count"] == 1

    by_tag = svc.search.search(
        actor_id="owner_sf", organization_id=org_id, tag="intro"
    )
    assert by_tag["results"][0]["id"] == a["id"]

    by_creator = svc.search.search(
        actor_id="owner_sf", organization_id=org_id, creator="editor_1"
    )
    assert by_creator["count"] == 1

    by_rating = svc.search.search(
        actor_id="owner_sf", organization_id=org_id, min_rating=4.0
    )
    assert by_rating["count"] == 1
    assert by_rating["results"][0]["id"] == a["id"]

    popular = svc.search.search(
        actor_id="owner_sf", organization_id=org_id, sort="popular"
    )
    assert popular["results"][0]["id"] == b["id"]

    featured = svc.search.search(
        actor_id="owner_sf", organization_id=org_id, featured_only=True
    )
    assert featured["count"] == 1
    assert featured["results"][0]["id"] == b["id"]

    # Unknown sort mode rejected
    try:
        svc.search.search(
            actor_id="owner_sf", organization_id=org_id, sort="random"
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


# --- Security ---


def test_security_asset_ownership():
    org_id = _seed_org("owner_so")
    template = _upload(org_id, "owner_so")["template"]
    # Non-owner editor cannot update, delete, or publish versions
    try:
        _svc().templates.update(
            template["id"], {"name": "Stolen"}, actor_id="editor_1"
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        _svc().templates.delete(template["id"], actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        _svc().versioning.publish_version(
            template["id"], {"version": "1.1.0"}, actor_id="editor_1"
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


def test_security_organization_isolation():
    org_a = _seed_org("owner_oa")
    org_b = _seed_org("owner_ob")
    template = _upload(org_a, "owner_oa")["template"]
    # Foreign org member cannot read, list, or search another org's templates
    try:
        _svc().templates.get(template["id"], actor_id="owner_ob")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        _svc().templates.list(actor_id="owner_ob", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    # Search is org-scoped: no cross-org leakage
    results = _svc().search.search(
        actor_id="owner_ob", organization_id=org_b, query="cinematic"
    )
    assert results["count"] == 0


def test_security_audit_logging():
    org_id = _seed_org("owner_al")
    audit_store = sys.modules["app.services.enterprise_auth.store"]
    template = _upload(org_id, "owner_al")["template"]
    _svc().versioning.publish_version(
        template["id"], {"version": "1.0.1"}, actor_id="owner_al"
    )
    _svc().versioning.rollback(template["id"], "1.0.0", actor_id="owner_al")
    events = audit_store.list_audits(limit=500)
    actions = {e.event_type for e in events}
    assert "template_store.uploaded" in actions
    assert "template_store.version_published" in actions
    assert "template_store.rolled_back" in actions


# --- Integration ---


def test_full_template_store_workflow():
    """Upload -> library -> version -> search -> rate -> archive -> restore -> rollback."""
    org_id = _seed_org("owner_full")
    svc = _svc()
    library = svc.libraries.create_library(
        {"organizationId": org_id, "name": "Main Library"}, actor_id="owner_full"
    )["library"]
    template = _upload(
        org_id, "owner_full", name="Flagship Template", libraryId=library["id"],
        tags=["flagship", "hero"],
    )["template"]
    tid = template["id"]

    svc.versioning.publish_version(
        tid,
        {"version": "1.1.0", "changelog": "Improvements",
         "assetUri": "https://cdn.rtas.example/flagship-1.1.zip"},
        actor_id="owner_full",
    )
    svc.templates.rate(tid, 5, actor_id="editor_1")
    svc.templates.record_download(tid, actor_id="editor_1")

    results = svc.search.search(
        actor_id="editor_1", organization_id=org_id, query="flagship",
        sort="popular",
    )
    assert results["count"] == 1
    assert results["results"][0]["downloads"] == 1
    assert results["results"][0]["avgRating"] == 5.0

    svc.templates.archive(tid, actor_id="owner_full")
    assert (
        svc.search.search(
            actor_id="owner_full", organization_id=org_id, query="flagship"
        )["count"]
        == 0
    )
    svc.templates.restore(tid, actor_id="owner_full")

    rolled = svc.versioning.rollback(tid, "1.0.0", actor_id="owner_full")
    assert rolled["template"]["currentVersion"] == "1.0.0"
    integrity = svc.versioning.verify_integrity(
        tid, "1.0.0", actor_id="owner_full"
    )
    assert integrity["valid"] is True

    status = svc.status()
    assert status["stats"]["templates"] == 1
    assert status["stats"]["versions"] == 2
    assert status["stats"]["libraries"] == 1
