"""Phase 9 Sprint 1 — AI Marketplace Ecosystem Foundation tests."""

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
        "marketplace_ecosystem",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    eco = sys.modules["app.services.marketplace_ecosystem"]
    eco.get_marketplace_ecosystem_service = sys.modules[
        "app.services.marketplace_ecosystem.service"
    ].get_marketplace_ecosystem_service
    eco.reset_engine = sys.modules["app.services.marketplace_ecosystem.service"].reset_engine


_bootstrap()


def _eco():
    return sys.modules["app.services.marketplace_ecosystem.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.marketplace_ecosystem.version"]


def _catalog():
    return sys.modules["app.services.marketplace_ecosystem.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    _bootstrap()
    mod = _eco()
    mod._service = None
    sys.modules["app.services.marketplace_ecosystem.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"eco-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Ecosystem Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _svc():
    return _eco().get_marketplace_ecosystem_service()


def _create_asset(org_id: str, actor: str, **overrides):
    payload = {
        "organizationId": org_id,
        "name": "Cinematic Prompt Pack",
        "assetType": "prompt_pack",
        "description": "Professional cinematic prompt engineering pack",
        "category": "prompts",
        "tags": ["cinematic", "prompts", "video"],
        "assetUri": "https://cdn.rtas.example/assets/prompt-pack.zip",
    }
    payload.update(overrides)
    return _svc().registry.create(payload, actor_id=actor)["asset"]


# --- Unit ---


def test_version_unit():
    v = _version()
    assert v.PHASE == 9
    assert v.SPRINT == 1
    assert "Marketplace Ecosystem" in v.ENGINE_NAME


def test_catalog_unit():
    c = _catalog()
    assert "prompt_pack" in c.ASSET_TYPES
    assert "voice_model" in c.ASSET_TYPES
    assert "automation_pack" in c.ASSET_TYPES
    assert "custom" in c.ASSET_TYPES  # future AI assets
    assert set(c.ASSET_STATUSES) == {"draft", "published", "archived", "deleted"}
    assert c.is_semver("1.2.3") is True
    assert c.is_semver("1.2") is False
    assert c.slugify("My Great Asset!") == "my-great-asset"
    handle = c.generate_creator_handle("Jane Creator")
    assert handle.startswith("jane-creator-")


def test_engine_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["phase"] == 9
    assert status["sprint"] == 1
    assert all(v == "ready" for v in status["engines"].values())
    assert status["security"]["assetOwnership"] == "enforced"
    assert status["security"]["auditLogging"] == "enabled"


# --- Creator platform ---


def test_creator_register_and_profile():
    org_id = _seed_org("owner_cr")
    created = _svc().creators.register(
        {
            "organizationId": org_id,
            "displayName": "RTAS Studio Creator",
            "creatorType": "publisher",
            "bio": "AI asset publisher",
            "website": "https://rtas.example",
        },
        actor_id="owner_cr",
    )
    assert created["ok"] is True
    creator = created["creator"]
    assert creator["creatorType"] == "publisher"
    assert creator["handle"].startswith("rtas-studio-creator-")

    profile = _svc().creators.profile(actor_id="owner_cr", organization_id=org_id)
    assert profile["creator"]["id"] == creator["id"]
    assert profile["assets"]["total"] == 0

    # Duplicate registration rejected
    try:
        _svc().creators.register(
            {"organizationId": org_id, "displayName": "Again"}, actor_id="owner_cr"
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_creator_profile_update():
    org_id = _seed_org("owner_up")
    _svc().creators.register(
        {"organizationId": org_id, "displayName": "Original"}, actor_id="owner_up"
    )
    updated = _svc().creators.update_profile(
        {"displayName": "Updated Name", "bio": "New bio", "creatorType": "publisher"},
        actor_id="owner_up",
        organization_id=org_id,
    )
    assert updated["creator"]["displayName"] == "Updated Name"
    assert updated["creator"]["bio"] == "New bio"
    assert updated["creator"]["creatorType"] == "publisher"


# --- Digital asset registry ---


def test_asset_create_draft_and_publish():
    org_id = _seed_org("owner_a")
    asset = _create_asset(org_id, "owner_a")
    assert asset["status"] == "draft"
    assert asset["slug"] == "cinematic-prompt-pack"
    assert asset["currentVersion"] == "1.0.0"

    published = _svc().registry.update(
        asset["id"], {"status": "published"}, actor_id="owner_a"
    )["asset"]
    assert published["status"] == "published"
    assert published["publishedAt"]

    # Creator stats updated
    profile = _svc().creators.profile(actor_id="owner_a", organization_id=org_id)
    assert profile["assets"]["published"] == 1
    assert profile["creator"]["stats"]["publishedAssets"] == 1


def test_asset_publish_on_create():
    org_id = _seed_org("owner_pc")
    asset = _create_asset(org_id, "owner_pc", publish=True)
    assert asset["status"] == "published"


def test_asset_publish_requires_uri():
    org_id = _seed_org("owner_nu")
    asset = _create_asset(org_id, "owner_nu", assetUri="")
    try:
        _svc().registry.update(asset["id"], {"status": "published"}, actor_id="owner_nu")
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "asseturi" in str(exc).lower()


def test_asset_versioning():
    org_id = _seed_org("owner_v")
    asset = _create_asset(org_id, "owner_v")
    updated = _svc().registry.update(
        asset["id"],
        {"version": "1.1.0", "changelog": "Added 20 new prompts"},
        actor_id="owner_v",
    )["asset"]
    assert updated["currentVersion"] == "1.1.0"

    versions = _svc().registry.versions(asset["id"], actor_id="owner_v")
    assert versions["count"] == 2
    assert versions["versions"][0]["version"] == "1.1.0"
    assert versions["versions"][0]["changelog"] == "Added 20 new prompts"

    # Duplicate version rejected
    try:
        _svc().registry.update(asset["id"], {"version": "1.1.0"}, actor_id="owner_v")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass

    # Bad semver rejected
    try:
        _svc().registry.update(asset["id"], {"version": "2.0"}, actor_id="owner_v")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_asset_archive_and_delete():
    org_id = _seed_org("owner_ad")
    asset = _create_asset(org_id, "owner_ad", publish=True)
    archived = _svc().registry.update(
        asset["id"], {"status": "archived"}, actor_id="owner_ad"
    )["asset"]
    assert archived["status"] == "archived"
    assert archived["archivedAt"]

    deleted = _svc().registry.delete(asset["id"], actor_id="owner_ad")
    assert deleted["status"] == "deleted"

    NotFoundError = _errors().NotFoundError
    try:
        _svc().registry.get(asset["id"], actor_id="owner_ad")
        assert False, "expected NotFoundError"
    except NotFoundError:
        pass


def test_asset_update_fields():
    org_id = _seed_org("owner_uf")
    asset = _create_asset(org_id, "owner_uf")
    updated = _svc().registry.update(
        asset["id"],
        {
            "name": "Renamed Pack",
            "description": "Updated description",
            "category": "workflows",
            "tags": ["new", "tags"],
            "visibility": "organization",
        },
        actor_id="owner_uf",
    )["asset"]
    assert updated["name"] == "Renamed Pack"
    assert updated["slug"] == "renamed-pack"
    assert updated["category"] == "workflows"
    assert updated["tags"] == ["new", "tags"]
    assert updated["visibility"] == "organization"


def test_all_supported_asset_types():
    org_id = _seed_org("owner_types")
    for asset_type in _catalog().ASSET_TYPES:
        asset = _create_asset(
            org_id, "owner_types",
            name=f"Asset {asset_type}", assetType=asset_type,
        )
        assert asset["assetType"] == asset_type
    # Unknown type rejected
    try:
        _create_asset(org_id, "owner_types", assetType="not_a_type")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


# --- Catalog & search ---


def test_catalog_public_listing_hides_drafts():
    org_id = _seed_org("owner_cat")
    _create_asset(org_id, "owner_cat", name="Draft Asset")
    _create_asset(org_id, "owner_cat", name="Live Asset", publish=True)
    public = _svc().catalog.list()
    names = [a["name"] for a in public["assets"]]
    assert "Live Asset" in names
    assert "Draft Asset" not in names

    # Org-scoped listing shows drafts to members
    scoped = _svc().catalog.list(actor_id="owner_cat", organization_id=org_id)
    assert scoped["count"] == 2


def test_catalog_categories_and_tags():
    org_id = _seed_org("owner_ct")
    _create_asset(org_id, "owner_ct", publish=True)
    categories = _svc().catalog.categories()
    assert categories["ok"] is True
    by_key = {c["key"]: c["assetCount"] for c in categories["categories"]}
    assert by_key["prompts"] == 1

    tags = _svc().catalog.tags()
    tag_names = [t["tag"] for t in tags["tags"]]
    assert "cinematic" in tag_names


def test_collections():
    org_id = _seed_org("owner_col")
    _svc().creators.register(
        {"organizationId": org_id, "displayName": "Collector"}, actor_id="owner_col"
    )
    a1 = _create_asset(org_id, "owner_col", name="Asset One", publish=True)
    a2 = _create_asset(org_id, "owner_col", name="Asset Two", publish=True)
    collection = _svc().catalog.create_collection(
        {
            "organizationId": org_id,
            "name": "Starter Bundle",
            "assetIds": [a1["id"], a2["id"]],
        },
        actor_id="owner_col",
    )["collection"]
    assert collection["assetCount"] == 2
    listed = _svc().catalog.list_collections(
        actor_id="owner_col", organization_id=org_id
    )
    assert listed["count"] == 1


def test_search_foundation():
    org_id = _seed_org("owner_s")
    _create_asset(
        org_id, "owner_s",
        name="Epic Voice Model", assetType="voice_model", category="voice",
        tags=["narration", "epic"], publish=True,
    )
    _create_asset(
        org_id, "owner_s",
        name="Chill Music Pack", assetType="music_pack", category="music",
        tags=["lofi", "chill"], publish=True,
    )
    # Full-text
    result = _svc().search.search("voice")
    assert result["count"] == 1
    assert result["results"][0]["name"] == "Epic Voice Model"
    # Type filter
    result = _svc().search.search("", asset_type="music_pack")
    assert result["count"] == 1
    # Tag filter
    result = _svc().search.search("", tag="lofi")
    assert result["count"] == 1
    # Category filter
    result = _svc().search.search("", category="voice")
    assert result["count"] == 1
    # No match
    result = _svc().search.search("nonexistent-asset-term")
    assert result["count"] == 0


def test_search_excludes_drafts_and_private():
    org_id = _seed_org("owner_sp")
    _create_asset(org_id, "owner_sp", name="Hidden Draft")
    _create_asset(
        org_id, "owner_sp", name="Private Gem",
        visibility="private", publish=True,
    )
    result = _svc().search.search("")
    names = [a["name"] for a in result["results"]]
    assert "Hidden Draft" not in names
    assert "Private Gem" not in names


# --- Security ---


def test_security_asset_ownership():
    org_id = _seed_org("owner_own")
    asset = _create_asset(org_id, "owner_own")
    ForbiddenError = _errors().ForbiddenError
    # editor_1 is a member but not the owner nor an org manager
    try:
        _svc().registry.update(
            asset["id"], {"name": "Hijacked"}, actor_id="editor_1"
        )
        assert False, "expected ForbiddenError"
    except ForbiddenError:
        pass
    try:
        _svc().registry.delete(asset["id"], actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except ForbiddenError:
        pass


def test_security_organization_isolation():
    org_a = _seed_org("owner_ia")
    org_b = _seed_org("owner_ib")
    asset = _create_asset(org_a, "owner_ia")  # draft: only org_a members may read
    ForbiddenError = _errors().ForbiddenError
    try:
        _svc().registry.get(asset["id"], actor_id="owner_ib")
        assert False, "expected ForbiddenError"
    except ForbiddenError:
        pass
    # Org-scoped catalog is isolated too
    try:
        _svc().catalog.list(actor_id="owner_ib", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except ForbiddenError:
        pass


def test_security_non_member_cannot_create():
    org_id = _seed_org("owner_nm")
    ForbiddenError = _errors().ForbiddenError
    try:
        _create_asset(org_id, "total_stranger")
        assert False, "expected ForbiddenError"
    except ForbiddenError:
        pass


def test_security_audit_logging():
    org_id = _seed_org("owner_log")
    audit_store = sys.modules["app.services.enterprise_auth.store"]
    before = len(audit_store.list_audits(limit=500))
    _create_asset(org_id, "owner_log", publish=True)
    events = audit_store.list_audits(limit=500)
    assert len(events) > before
    actions = {e.event_type for e in events}
    assert "marketplace_ecosystem.asset_created" in actions
    assert "marketplace_ecosystem.asset_published" in actions


# --- Integration & performance ---


def test_full_creator_workflow_integration():
    """Register creator -> draft -> publish -> version -> archive -> collection."""
    org_id = _seed_org("owner_flow")
    svc = _svc()
    svc.creators.register(
        {"organizationId": org_id, "displayName": "Flow Creator"},
        actor_id="owner_flow",
    )
    asset = _create_asset(org_id, "owner_flow", name="Workflow Template X",
                          assetType="workflow_template", category="workflows")
    svc.registry.update(asset["id"], {"status": "published"}, actor_id="owner_flow")
    svc.registry.update(
        asset["id"], {"version": "1.1.0", "changelog": "Improvements"},
        actor_id="owner_flow",
    )
    svc.catalog.create_collection(
        {"organizationId": org_id, "name": "Flow Bundle", "assetIds": [asset["id"]]},
        actor_id="owner_flow",
    )
    profile = svc.creators.profile(actor_id="owner_flow", organization_id=org_id)
    assert profile["assets"]["published"] == 1
    assert profile["creator"]["stats"]["totalVersions"] == 2
    found = svc.search.search("workflow template")
    assert found["count"] == 1
    status = svc.status()
    assert status["stats"]["assets"] == 1
    assert status["stats"]["creators"] == 1
    assert status["stats"]["collections"] == 1


def test_bulk_registry_performance():
    org_id = _seed_org("owner_perf")
    start = time.perf_counter()
    for i in range(300):
        _create_asset(
            org_id, "owner_perf",
            name=f"Perf Asset {i}",
            assetType=_catalog().ASSET_TYPES[i % len(_catalog().ASSET_TYPES)],
            tags=[f"tag{i % 10}", "perf"],
            publish=True,
        )
    listed = _svc().catalog.list(limit=200)
    searched = _svc().search.search("perf", limit=200)
    elapsed = time.perf_counter() - start
    assert elapsed < 15.0
    assert listed["count"] == 200
    assert searched["count"] == 200
