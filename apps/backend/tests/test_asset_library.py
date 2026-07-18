"""Phase 7 Sprint 5 — Asset Management & Digital Library Engine tests."""

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
    mt.get_multi_tenant_service = sys.modules["app.services.multi_tenant.service"].get_multi_tenant_service
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
        "asset_library",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    al = sys.modules["app.services.asset_library"]
    al.get_asset_library_service = sys.modules[
        "app.services.asset_library.service"
    ].get_asset_library_service
    al.reset_engine = sys.modules["app.services.asset_library.service"].reset_engine
    al.get_engine = sys.modules["app.services.asset_library.service"].get_engine


_bootstrap()

version = sys.modules["app.services.asset_library.version"]
catalog = sys.modules["app.services.asset_library.catalog"]
service_mod = sys.modules["app.services.asset_library.service"]
errors = sys.modules["app.services.enterprise_auth.errors"]
mt_service = sys.modules["app.services.multi_tenant.service"]
validation = sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    service_mod.reset_engine()


def _seed_org():
    mt = mt_service.get_multi_tenant_service()
    slug = f"asset-org-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Asset Org", "ownerId": "owner_1", "slug": slug}
    )
    org_id = created["organization"]["id"]
    ws_id = created["defaultWorkspace"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    mt.add_member({"organizationId": org_id, "userId": "viewer_1", "role": "viewer"})
    return org_id, ws_id


def _upload(svc, org_id, ws_id=None, **extra):
    payload = {
        "organizationId": org_id,
        "workspaceId": ws_id,
        "name": extra.pop("name", "Hero Logo"),
        "assetType": extra.pop("assetType", "logo"),
        "category": extra.pop("category", "brand"),
        "tags": extra.pop("tags", ["brand", "logo"]),
        "content": extra.pop("content", "binary-logo-data"),
        "metadata": extra.pop("metadata", {"description": "Primary brand mark"}),
        **extra,
    }
    return svc.assets.upload(payload, actor_id="owner_1")


# --- Unit ---


def test_version_unit():
    assert version.PHASE == 7
    assert version.SPRINT == 5
    assert "Digital Library" in version.ENGINE_NAME


def test_catalog_unit():
    assert "image" in catalog.ASSET_TYPES
    assert "ai_model" in catalog.ASSET_TYPES
    assert catalog.normalize_asset_type("logos") == "logo"
    assert catalog.role_at_least("owner", "edit")
    assert not catalog.role_at_least("read", "edit")


def test_status_unit():
    svc = service_mod.get_asset_library_service()
    status = svc.status()
    assert status["ok"] is True
    assert status["phase"] == 7
    assert status["sprint"] == 5
    assert status["engines"]["asset"] == "ready"
    assert status["engines"]["library"] == "ready"
    assert status["engines"]["search"] == "ready"


# --- Upload / lifecycle ---


def test_upload_download_lifecycle():
    svc = service_mod.get_asset_library_service()
    org_id, ws_id = _seed_org()
    created = _upload(svc, org_id, ws_id, name="Launch Thumbnail", assetType="thumbnail")
    asset = created["asset"]
    assert asset["assetType"] == "thumbnail"
    assert asset["currentVersion"] == 1
    got = svc.assets.get(asset["id"], actor_id="owner_1")
    assert got["asset"]["id"] == asset["id"]
    dl = svc.assets.download(asset["id"], actor_id="owner_1")
    assert dl["ok"] is True
    assert "token=" in dl["downloadUrl"]
    token = dl["downloadUrl"].split("token=")[1]
    assert svc.signed_urls.verify(asset["id"], token, actor_id="owner_1") is True


def test_rename_move_copy_archive_restore_delete():
    svc = service_mod.get_asset_library_service()
    org_id, ws_id = _seed_org()
    created = _upload(svc, org_id, ws_id)
    aid = created["asset"]["id"]
    renamed = svc.assets.rename(aid, "Renamed Asset", actor_id="owner_1")
    assert renamed["asset"]["name"] == "Renamed Asset"
    moved = svc.assets.move(aid, actor_id="owner_1", category="production")
    assert moved["asset"]["category"] == "production"
    copied = svc.assets.copy(aid, actor_id="owner_1")
    assert "Copy" in copied["asset"]["name"]
    dup = svc.assets.duplicate(aid, actor_id="owner_1")
    assert dup["ok"] is True
    archived = svc.assets.archive(aid, actor_id="owner_1")
    assert archived["asset"]["status"] == "archived"
    restored = svc.assets.restore(aid, actor_id="owner_1")
    assert restored["asset"]["status"] == "active"
    fav = svc.assets.favorite(aid, actor_id="owner_1")
    assert fav["asset"]["isFavorite"] is True
    deleted = svc.assets.delete(aid, actor_id="owner_1")
    assert deleted["deleted"] is True


def test_versions_tags_metadata_preview():
    svc = service_mod.get_asset_library_service()
    org_id, _ = _seed_org()
    created = _upload(svc, org_id, name="Voice Line", assetType="voice")
    aid = created["asset"]["id"]
    ver = svc.versions.add_version(
        aid, {"content": "v2-audio", "note": "louder take"}, actor_id="owner_1"
    )
    assert ver["version"]["version"] == 2
    hist = svc.versions.history(aid, actor_id="owner_1")
    assert hist["count"] == 2
    tagged = svc.tagging.tag(aid, ["voiceover", "en"], actor_id="owner_1")
    assert "voiceover" in tagged["asset"]["tags"]
    cat = svc.tagging.categorize(aid, "audio", actor_id="owner_1")
    assert cat["asset"]["category"] == "audio"
    meta = svc.metadata.update(aid, {"title": "Hero VO"}, actor_id="owner_1")
    assert meta["asset"]["metadata"]["title"] == "Hero VO"
    preview = svc.metadata.preview(aid, actor_id="owner_1")
    assert preview["assetType"] == "voice"


# --- Search ---


def test_search_modes():
    svc = service_mod.get_asset_library_service()
    org_id, _ = _seed_org()
    _upload(
        svc,
        org_id,
        name="Brand Kit Logo",
        assetType="logo",
        tags=["brand", "primary"],
        metadata={"description": "corporate identity mark", "campaign": "q1"},
    )
    _upload(
        svc,
        org_id,
        name="Scene Prompt",
        assetType="prompt",
        category="ai",
        tags=["prompt"],
        content="cinematic neon alley",
        metadata={"description": "night city prompt"},
    )
    full = svc.search.search({"organizationId": org_id, "q": "brand kit"}, actor_id="owner_1")
    assert full["count"] >= 1
    tag = svc.search.search({"organizationId": org_id, "tag": "prompt"}, actor_id="owner_1")
    assert tag["count"] >= 1
    cat = svc.search.search({"organizationId": org_id, "category": "ai"}, actor_id="owner_1")
    assert cat["count"] >= 1
    meta = svc.search.search(
        {"organizationId": org_id, "metadataKey": "campaign", "metadataValue": "q1"},
        actor_id="owner_1",
    )
    assert meta["count"] >= 1
    semantic = svc.search.search(
        {"organizationId": org_id, "q": "corporate identity", "semantic": True},
        actor_id="owner_1",
    )
    assert semantic["semantic"] is True
    assert semantic["count"] >= 1
    recent = svc.search.recent(organization_id=org_id, actor_id="owner_1")
    assert recent["count"] >= 2
    svc.assets.favorite(
        full["assets"][0]["id"] if full["assets"] else tag["assets"][0]["id"],
        actor_id="owner_1",
    )
    favs = svc.search.favorites(organization_id=org_id, actor_id="owner_1")
    assert favs["count"] >= 1
    used = svc.search.most_used(organization_id=org_id, actor_id="owner_1")
    assert used["ok"] is True


# --- Sharing / library ---


def test_sharing_and_digital_library():
    svc = service_mod.get_asset_library_service()
    org_id, ws_id = _seed_org()
    created = _upload(svc, org_id, ws_id, name="Shared Template", assetType="template")
    aid = created["asset"]["id"]
    shared = svc.sharing.share(
        {"assetId": aid, "subjectType": "user", "subjectId": "editor_1", "role": "edit"},
        actor_id="owner_1",
    )
    assert shared["permission"]["role"] == "edit"
    got = svc.assets.get(aid, actor_id="editor_1")
    assert got["role"] == "edit"
    org_share = svc.sharing.share(
        {"assetId": aid, "subjectType": "organization", "role": "read"},
        actor_id="owner_1",
    )
    assert org_share["asset"]["isShared"] is True
    libs = svc.library.list_libraries(org_id, actor_id="owner_1")
    assert libs["organizationLibrary"] is True
    col = svc.library.create_collection(
        {"organizationId": org_id, "name": "Brand Pack", "libraryScope": "organization"},
        actor_id="owner_1",
    )
    added = svc.library.add_to_collection(col["collection"]["id"], aid, actor_id="owner_1")
    assert aid in added["collection"]["assetIds"]


# --- Permission / Security ---


def test_permission_and_isolation_security():
    svc = service_mod.get_asset_library_service()
    org_id, ws_id = _seed_org()
    created = _upload(svc, org_id, ws_id)
    aid = created["asset"]["id"]
    # viewer cannot edit without share
    try:
        svc.assets.update(aid, {"name": "Hack"}, actor_id="viewer_1")
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # outsider cannot upload into org
    try:
        svc.assets.upload(
            {"organizationId": org_id, "name": "Nope", "content": "x"},
            actor_id="outsider",
        )
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # org isolation on get
    other = mt_service.get_multi_tenant_service().create_organization(
        {"name": "Other", "ownerId": "other_o", "slug": f"other-{uuid.uuid4().hex[:6]}"}
    )
    other_asset = svc.assets.upload(
        {
            "organizationId": other["organization"]["id"],
            "name": "Other Asset",
            "content": "y",
        },
        actor_id="other_o",
    )
    try:
        svc.assets.get(other_asset["asset"]["id"], actor_id="owner_1")
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # workspace isolation on upload
    try:
        svc.assets.upload(
            {
                "organizationId": org_id,
                "workspaceId": "ws_fake_not_in_org",
                "name": "Bad WS",
                "content": "z",
            },
            actor_id="owner_1",
        )
        assert False, "expected access denial"
    except (errors.ForbiddenError, errors.NotFoundError):
        pass
    # ownership required for delete
    svc.sharing.share(
        {"assetId": aid, "subjectType": "user", "userId": "editor_1", "role": "edit"},
        actor_id="owner_1",
    )
    try:
        svc.assets.delete(aid, actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except errors.ForbiddenError:
        pass
    # signed URL verify rejects garbage
    assert svc.signed_urls.verify(aid, "not-a-valid-token") is False


def test_list_and_observability_performance():
    svc = service_mod.get_asset_library_service()
    org_id, _ = _seed_org()
    start = time.perf_counter()
    for i in range(8):
        _upload(
            svc,
            org_id,
            name=f"Perf Asset {i}",
            assetType="document",
            content=f"doc-{i}",
            tags=[f"t{i}"],
        )
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0
    listed = svc.assets.list({"organizationId": org_id}, actor_id="owner_1")
    assert listed["count"] >= 8
    search = svc.search.search({"organizationId": org_id, "q": "perf"}, actor_id="owner_1")
    assert search["count"] >= 1
    assert search["latencyMs"] < 500
    obs = svc.observability()
    assert obs["totalAssets"] >= 8
    assert obs["uploadSuccess"] >= 8
    assert obs["errors"] == 0
