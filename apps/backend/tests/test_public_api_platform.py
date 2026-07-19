"""Phase 9 Sprint 6 — Public API Platform, SDK & Developer Ecosystem tests."""

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
        "public_api_platform",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    pap = sys.modules["app.services.public_api_platform"]
    pap.get_public_api_platform_service = sys.modules[
        "app.services.public_api_platform.service"
    ].get_public_api_platform_service
    pap.reset_engine = sys.modules["app.services.public_api_platform.service"].reset_engine


_bootstrap()


def _pap():
    return sys.modules["app.services.public_api_platform.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.public_api_platform.version"]


def _catalog():
    return sys.modules["app.services.public_api_platform.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    _bootstrap()
    mod = _pap()
    mod._service = None
    sys.modules["app.services.public_api_platform.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"pap-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "API Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    return org_id


def _svc():
    return _pap().get_public_api_platform_service()


def _register_dev(org_id: str, actor: str, **overrides):
    payload = {
        "organizationId": org_id,
        "displayName": "Dev Portal User",
        "email": f"{actor}@example.com",
    }
    payload.update(overrides)
    return _svc().portal.register(payload, actor_id=actor)


# --- Unit ---


def test_version_unit():
    v = _version()
    assert v.PHASE == 9
    assert v.SPRINT == 6
    assert "Public API" in v.ENGINE_NAME


def test_catalog_unit():
    c = _catalog()
    assert "authentication" in c.PUBLIC_API_SURFACES
    assert "ai_generation" in c.PUBLIC_API_SURFACES
    assert "marketplace" in c.PUBLIC_API_SURFACES
    assert "python" in c.SDK_LANGUAGES
    assert "typescript" in c.SDK_LANGUAGES
    assert "go" in c.SDK_LANGUAGES
    assert c.is_semver("1.0.0") is True
    assert c.is_api_version_label("v1") is True
    assert c.is_api_version_label("1.0") is False
    digest = c.hash_secret("secret")
    assert c.verify_secret("secret", digest) is True
    assert c.verify_secret("wrong", digest) is False
    key = c.generate_api_key()
    assert key.startswith("rtas_sk_")
    assert "surfaces" in c.playground_metadata()


def test_engine_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["phase"] == 9
    assert status["sprint"] == 6
    assert len(status["engines"]) == 6
    assert all(v == "ready" for v in status["engines"].values())


# --- Developer Portal ---


def test_developer_register_and_profile():
    org_id = _seed_org("owner_dev")
    created = _register_dev(org_id, "owner_dev")
    assert created["developer"]["organizationId"] == org_id
    profile = _svc().portal.profile(actor_id="owner_dev", organization_id=org_id)
    assert profile["developer"]["id"] == created["developer"]["id"]
    assert "playground" in profile
    # Duplicate registration rejected
    try:
        _register_dev(org_id, "owner_dev")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_api_key_create_list_revoke():
    org_id = _seed_org("owner_key")
    _register_dev(org_id, "owner_key")
    created = _svc().portal.create_api_key(
        {
            "organizationId": org_id,
            "name": "CI Key",
            "scopes": ["org.read", "ai.generate"],
            "workspaceId": "ws_1",
        },
        actor_id="owner_key",
    )
    assert "token" in created["apiKey"]
    assert created["apiKey"]["token"].startswith("rtas_sk_")
    listed = _svc().portal.list_api_keys(actor_id="owner_key", organization_id=org_id)
    assert listed["count"] == 1
    # Plaintext not re-exposed on list
    assert "token" not in listed["apiKeys"][0]
    revoked = _svc().portal.revoke_api_key(
        created["apiKey"]["id"], actor_id="owner_key"
    )
    assert revoked["status"] == "revoked"
    listed_after = _svc().portal.list_api_keys(
        actor_id="owner_key", organization_id=org_id
    )
    assert listed_after["count"] == 0


def test_webhook_registration():
    org_id = _seed_org("owner_wh")
    _register_dev(org_id, "owner_wh")
    created = _svc().portal.register_webhook(
        {
            "organizationId": org_id,
            "targetUrl": "https://hooks.example.com/rtas",
            "events": ["api.request", "billing.invoice"],
        },
        actor_id="owner_wh",
    )
    assert created["webhook"]["targetUrl"].startswith("https://")
    assert "signingSecret" in created
    listed = _svc().portal.list_webhooks(actor_id="owner_wh", organization_id=org_id)
    assert listed["count"] == 1


# --- OAuth ---


def test_oauth_client_create_list_authenticate():
    org_id = _seed_org("owner_oauth")
    _register_dev(org_id, "owner_oauth")
    created = _svc().oauth.create_client(
        {
            "organizationId": org_id,
            "name": "Partner App",
            "redirectUris": ["https://partner.example.com/callback"],
            "scopes": ["openid", "org.read", "ai.generate"],
        },
        actor_id="owner_oauth",
    )
    client = created["client"]
    assert client["clientId"].startswith("rtas_cid_")
    assert "clientSecret" in client
    listed = _svc().oauth.list_clients(actor_id="owner_oauth", organization_id=org_id)
    assert listed["count"] == 1
    assert "clientSecret" not in listed["clients"][0]

    auth = _svc().oauth.authenticate_client(client["clientId"], client["clientSecret"])
    assert auth["authenticated"] is True
    assert "accessToken" in auth
    # Bad secret rejected
    try:
        _svc().oauth.authenticate_client(client["clientId"], "wrong-secret")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_oauth_redirect_validation():
    org_id = _seed_org("owner_redir")
    _register_dev(org_id, "owner_redir")
    # Non-localhost http rejected
    try:
        _svc().oauth.create_client(
            {
                "organizationId": org_id,
                "name": "Bad",
                "redirectUris": ["http://evil.example.com/cb"],
                "grantTypes": ["authorization_code"],
            },
            actor_id="owner_redir",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass
    # authorization_code without redirect rejected
    try:
        _svc().oauth.create_client(
            {
                "organizationId": org_id,
                "name": "No Redirect",
                "grantTypes": ["authorization_code"],
                "redirectUris": [],
            },
            actor_id="owner_redir",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_oauth_redirect_uri_check():
    org_id = _seed_org("owner_ru")
    _register_dev(org_id, "owner_ru")
    created = _svc().oauth.create_client(
        {
            "organizationId": org_id,
            "name": "App",
            "redirectUris": ["https://app.example.com/cb"],
        },
        actor_id="owner_ru",
    )["client"]
    ok = _svc().oauth.validate_redirect(
        created["clientId"], "https://app.example.com/cb"
    )
    assert ok["valid"] is True
    try:
        _svc().oauth.validate_redirect(
            created["clientId"], "https://evil.example.com/cb"
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


# --- Versioning & Docs ---


def test_api_versioning():
    versions = _svc().versioning.list()
    assert versions["default"] == "v1"
    assert any(v["version"] == "v1" for v in versions["versions"])
    registered = _svc().versioning.register(
        {"version": "v2", "changelog": "Next gen"}, actor_id="system"
    )
    assert registered["version"]["version"] == "v2"
    deprecated = _svc().versioning.deprecate("v2", actor_id="system")
    assert deprecated["version"]["status"] == "deprecated"
    resolved = _svc().versioning.resolve("v2")
    assert resolved["deprecated"] is True
    validated = _svc().versioning.validate_request(
        {"version": "v1", "surface": "billing", "method": "GET"}
    )
    assert validated["valid"] is True


def test_api_documentation():
    docs = _svc().docs.openapi("v1")
    assert docs["documentation"]["openapi"] == "3.1.0"
    surfaces = {p.split("/")[-1].replace("-", "_") for p in docs["documentation"]["paths"]}
    assert "ai_generation" in surfaces or "ai-generation" in docs["documentation"]["paths"]
    playground = _svc().docs.playground()
    assert playground["playground"]["rateLimitPerMinute"] == 120
    listed = _svc().docs.surfaces()
    assert len(listed["surfaces"]) >= 10


# --- SDK ---


def test_sdk_releases_and_architecture():
    releases = _svc().sdk.list()
    assert releases["count"] >= len(_catalog().SDK_LANGUAGES)
    langs = {r["language"] for r in releases["releases"]}
    assert {"javascript", "python", "go", "rest"} <= langs
    py = _svc().sdk.list(language="python")
    assert all(r["language"] == "python" for r in py["releases"])
    published = _svc().sdk.publish(
        {
            "language": "python",
            "version": "1.1.0",
            "packageName": "rtas-studio-sdk",
            "changelog": "Gateway helpers",
        },
        actor_id="system",
    )
    assert published["release"]["version"] == "1.1.0"
    arch = _svc().sdk.architecture()
    assert arch["architecture"]["extensible"] is True
    assert arch["architecture"]["transport"] == "REST"


# --- Gateway ---


def test_gateway_api_key_dispatch_and_usage():
    org_id = _seed_org("owner_gw")
    _register_dev(org_id, "owner_gw")
    key = _svc().portal.create_api_key(
        {
            "organizationId": org_id,
            "name": "Gateway Key",
            "scopes": ["org.read", "ai.generate", "analytics.read"],
        },
        actor_id="owner_gw",
    )["apiKey"]["token"]

    for surface in ("organizations", "ai_generation", "analytics"):
        result = _svc().gateway.dispatch(
            {
                "surface": surface,
                "version": "v1",
                "method": "GET",
                "apiKey": key,
                "requiredScope": "org.read" if surface == "organizations" else "",
            },
            actor_id="owner_gw",
        )
        assert result["routed"] is True
        assert result["surface"] == surface

    usage = _svc().portal.usage(actor_id="owner_gw", organization_id=org_id)
    assert usage["count"] >= 3
    assert usage["bySurface"].get("ai_generation", 0) >= 1


def test_gateway_oauth_dispatch():
    org_id = _seed_org("owner_gwo")
    _register_dev(org_id, "owner_gwo")
    client = _svc().oauth.create_client(
        {
            "organizationId": org_id,
            "name": "OAuth Gateway",
            "grantTypes": ["client_credentials"],
            "scopes": ["marketplace.read", "billing.read"],
        },
        actor_id="owner_gwo",
    )["client"]
    result = _svc().gateway.dispatch(
        {
            "surface": "marketplace",
            "clientId": client["clientId"],
            "clientSecret": client["clientSecret"],
            "requiredScope": "marketplace.read",
        },
        actor_id="owner_gwo",
    )
    assert result["authType"] == "oauth2_client_credentials"
    assert result["routed"] is True


def test_gateway_all_public_surfaces():
    org_id = _seed_org("owner_all")
    _register_dev(org_id, "owner_all")
    key = _svc().portal.create_api_key(
        {
            "organizationId": org_id,
            "name": "All Surfaces",
            "scopes": list(_catalog().OAUTH_SCOPES),
        },
        actor_id="owner_all",
    )["apiKey"]["token"]
    for surface in _catalog().PUBLIC_API_SURFACES:
        result = _svc().gateway.dispatch(
            {"surface": surface, "apiKey": key}, actor_id="owner_all"
        )
        assert result["ok"] is True


def test_gateway_rate_limit():
    org_id = _seed_org("owner_rl")
    _register_dev(org_id, "owner_rl")
    key = _svc().portal.create_api_key(
        {
            "organizationId": org_id,
            "name": "Rate Limited",
            "rateLimitPerMinute": 3,
            "scopes": ["org.read"],
        },
        actor_id="owner_rl",
    )["apiKey"]["token"]
    for _ in range(3):
        _svc().gateway.authenticate_api_key(key)
    try:
        _svc().gateway.authenticate_api_key(key)
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "rate limit" in str(exc).lower()


def test_workspace_isolation():
    org_id = _seed_org("owner_ws")
    _register_dev(org_id, "owner_ws")
    key = _svc().portal.create_api_key(
        {
            "organizationId": org_id,
            "name": "WS Key",
            "workspaceId": "ws_a",
            "scopes": ["workspace.read"],
        },
        actor_id="owner_ws",
    )["apiKey"]["token"]
    ok = _svc().gateway.dispatch(
        {"surface": "workspaces", "apiKey": key, "workspaceId": "ws_a"},
        actor_id="owner_ws",
    )
    assert ok["workspaceId"] == "ws_a"
    try:
        _svc().gateway.dispatch(
            {"surface": "workspaces", "apiKey": key, "workspaceId": "ws_b"},
            actor_id="owner_ws",
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


# --- Security ---


def test_security_organization_isolation():
    org_a = _seed_org("owner_oa")
    org_b = _seed_org("owner_ob")
    _register_dev(org_a, "owner_oa")
    _register_dev(org_b, "owner_ob")
    try:
        _svc().portal.profile(actor_id="owner_ob", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        _svc().portal.list_api_keys(actor_id="owner_ob", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


def test_security_api_key_encryption_and_ownership():
    org_id = _seed_org("owner_sec")
    _register_dev(org_id, "owner_sec")
    # editor can register own developer account
    _register_dev(org_id, "editor_1", displayName="Editor Dev")
    key = _svc().portal.create_api_key(
        {"organizationId": org_id, "name": "Owner Key"},
        actor_id="owner_sec",
    )["apiKey"]
    store = sys.modules["app.services.public_api_platform.store"]
    stored = store.get_token(key["id"])
    assert stored is not None
    assert stored.token_hash != key["token"]
    assert _catalog().verify_secret(key["token"], stored.token_hash)
    # Editor cannot revoke owner's key
    try:
        _svc().portal.revoke_api_key(key["id"], actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


def test_security_audit_logging():
    org_id = _seed_org("owner_aud")
    audit_store = sys.modules["app.services.enterprise_auth.store"]
    _register_dev(org_id, "owner_aud")
    _svc().portal.create_api_key(
        {"organizationId": org_id, "name": "Audit Key"}, actor_id="owner_aud"
    )
    _svc().oauth.create_client(
        {
            "organizationId": org_id,
            "name": "Audit Client",
            "grantTypes": ["client_credentials"],
        },
        actor_id="owner_aud",
    )
    events = audit_store.list_audits(limit=500)
    actions = {e.event_type for e in events}
    assert "public_api.developer_registered" in actions
    assert "public_api.api_key_created" in actions
    assert "public_api.oauth_client_created" in actions


# --- Integration ---


def test_full_developer_ecosystem_workflow():
    """Register -> OAuth -> API key -> gateway -> usage -> webhook -> SDK."""
    org_id = _seed_org("owner_full")
    svc = _svc()
    svc.portal.register(
        {"organizationId": org_id, "displayName": "Full Dev"},
        actor_id="owner_full",
    )
    client = svc.oauth.create_client(
        {
            "organizationId": org_id,
            "name": "Full App",
            "redirectUris": ["https://full.example.com/cb"],
            "scopes": ["openid", "ai.generate", "analytics.read"],
        },
        actor_id="owner_full",
    )["client"]
    key = svc.portal.create_api_key(
        {
            "organizationId": org_id,
            "name": "Full Key",
            "scopes": ["ai.generate", "analytics.read"],
        },
        actor_id="owner_full",
    )["apiKey"]["token"]

    svc.gateway.dispatch(
        {"surface": "ai_generation", "apiKey": key, "requiredScope": "ai.generate"},
        actor_id="owner_full",
    )
    svc.gateway.dispatch(
        {
            "surface": "analytics",
            "clientId": client["clientId"],
            "clientSecret": client["clientSecret"],
            "requiredScope": "analytics.read",
        },
        actor_id="owner_full",
    )
    usage = svc.portal.usage(actor_id="owner_full", organization_id=org_id)
    assert usage["count"] >= 2

    svc.portal.register_webhook(
        {
            "organizationId": org_id,
            "targetUrl": "https://full.example.com/hooks",
            "events": ["api.request"],
        },
        actor_id="owner_full",
    )
    releases = svc.sdk.list()
    assert releases["count"] >= 8
    docs = svc.docs.openapi()
    assert "ApiKeyAuth" in docs["documentation"]["components"]["securitySchemes"]
    status = svc.status()
    assert status["stats"]["developers"] == 1
    assert status["stats"]["oauthClients"] == 1
    assert status["stats"]["apiTokens"] == 1


# --- Performance / Load ---


def test_load_gateway_performance():
    org_id = _seed_org("owner_perf")
    _register_dev(org_id, "owner_perf")
    key = _svc().portal.create_api_key(
        {
            "organizationId": org_id,
            "name": "Perf Key",
            "rateLimitPerMinute": 10_000,
            "scopes": ["org.read"],
        },
        actor_id="owner_perf",
    )["apiKey"]["token"]
    start = time.perf_counter()
    for i in range(200):
        _svc().gateway.dispatch(
            {
                "surface": _catalog().PUBLIC_API_SURFACES[i % len(_catalog().PUBLIC_API_SURFACES)],
                "apiKey": key,
            },
            actor_id="owner_perf",
        )
    elapsed = time.perf_counter() - start
    assert elapsed < 10.0
    usage = _svc().portal.usage(
        actor_id="owner_perf", organization_id=org_id, limit=500
    )
    assert usage["count"] == 200
    metrics = _svc().status()["stats"]
    assert metrics["avgLatencyMs"] >= 0
    assert metrics["usageLogs"] >= 200
