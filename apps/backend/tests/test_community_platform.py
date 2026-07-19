"""Phase 9 Sprint 3 — Community Platform & Social Collaboration Engine tests."""

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
        "community_platform",
        ("version", "catalog", "models", "store", "service", "engine"),
    )
    cm = sys.modules["app.services.community_platform"]
    cm.get_community_platform_service = sys.modules[
        "app.services.community_platform.service"
    ].get_community_platform_service
    cm.reset_engine = sys.modules["app.services.community_platform.service"].reset_engine


_bootstrap()


def _cm():
    return sys.modules["app.services.community_platform.service"]


def _mt():
    return sys.modules["app.services.multi_tenant.service"]


def _version():
    return sys.modules["app.services.community_platform.version"]


def _catalog():
    return sys.modules["app.services.community_platform.catalog"]


def _errors():
    return sys.modules["app.services.enterprise_auth.errors"]


def _validation():
    return sys.modules["app.services.multi_tenant.validation"]


def setup_function():
    _bootstrap()
    mod = _cm()
    mod._service = None
    sys.modules["app.services.community_platform.store"].reset_store()


def _seed_org(owner: str = "owner_1"):
    mt = _mt().get_multi_tenant_service()
    slug = f"cm-{uuid.uuid4().hex[:8]}"
    created = mt.create_organization(
        {"name": "Community Org", "ownerId": owner, "slug": slug}
    )
    org_id = created["organization"]["id"]
    mt.add_member({"organizationId": org_id, "userId": "editor_1", "role": "editor"})
    mt.add_member({"organizationId": org_id, "userId": "viewer_1", "role": "viewer"})
    return org_id


def _svc():
    return _cm().get_community_platform_service()


def _make_profile(org_id: str, actor: str, **overrides):
    payload = {
        "organizationId": org_id,
        "displayName": f"User {actor}",
        "handle": actor,
        "bio": "community member",
    }
    payload.update(overrides)
    return _svc().profiles.create(payload, actor_id=actor)


# --- Unit ---


def test_version_unit():
    v = _version()
    assert v.PHASE == 9
    assert v.SPRINT == 3
    assert "Community Platform" in v.ENGINE_NAME


def test_catalog_unit():
    c = _catalog()
    assert "like" in c.ENGAGEMENT_KINDS
    assert "mention" in c.NOTIFICATION_TYPES
    assert c.extract_mentions("hey @alice and @bob_2!") == ["alice", "bob_2"]
    rep = c.compute_reputation(
        followers=10, reviews_written=5, comments_written=10,
        likes_received=20, verified=True,
    )
    assert 0 < rep <= 100


def test_engine_status_unit():
    status = _svc().status()
    assert status["ok"] is True
    assert status["phase"] == 9
    assert status["sprint"] == 3
    assert len(status["engines"]) == 6
    assert all(v == "ready" for v in status["engines"].values())


# --- Profiles ---


def test_profile_lifecycle():
    org_id = _seed_org("owner_p")
    created = _make_profile(org_id, "owner_p")
    assert created["ok"] is True
    assert created["profile"]["handle"] == "owner_p"
    assert created["profile"]["verified"] is False

    fetched = _svc().profiles.get(actor_id="owner_p", organization_id=org_id)
    assert fetched["profile"]["displayName"] == "User owner_p"
    assert fetched["stats"]["reputation"] == 0.0

    updated = _svc().profiles.update(
        {"displayName": "Community Star", "bio": "hello"},
        actor_id="owner_p",
        organization_id=org_id,
    )
    assert updated["profile"]["displayName"] == "Community Star"

    # Duplicate profile and duplicate handle rejected
    try:
        _make_profile(org_id, "owner_p")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass
    try:
        _make_profile(org_id, "editor_1", handle="owner_p")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_profile_lookup_by_handle():
    org_id = _seed_org("owner_h")
    _make_profile(org_id, "owner_h", handle="starmaker")
    fetched = _svc().profiles.get(
        actor_id="owner_h", organization_id=org_id, handle="starmaker"
    )
    assert fetched["profile"]["userId"] == "owner_h"


def test_verified_member():
    org_id = _seed_org("owner_v")
    _make_profile(org_id, "editor_1")
    verified = _svc().profiles.verify_member(
        "editor_1", actor_id="owner_v", organization_id=org_id
    )
    assert verified["profile"]["verified"] is True
    # Non-manager cannot verify members
    _make_profile(org_id, "viewer_1")
    try:
        _svc().profiles.verify_member(
            "viewer_1", actor_id="viewer_1", organization_id=org_id
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


# --- Follow system ---


def test_follow_unfollow():
    org_id = _seed_org("owner_f")
    _make_profile(org_id, "owner_f")
    _make_profile(org_id, "editor_1")

    followed = _svc().follows.follow(
        "owner_f", actor_id="editor_1", organization_id=org_id
    )
    assert followed["followers"] == 1

    followers = _svc().follows.followers(
        actor_id="owner_f", organization_id=org_id
    )
    assert followers["count"] == 1
    following = _svc().follows.following(
        actor_id="editor_1", organization_id=org_id
    )
    assert following["count"] == 1

    # Follow notification delivered
    notifications = _svc().notifications.list(
        actor_id="owner_f", organization_id=org_id
    )
    assert notifications["unread"] == 1
    assert notifications["notifications"][0]["type"] == "follow"

    unfollowed = _svc().follows.unfollow(
        "owner_f", actor_id="editor_1", organization_id=org_id
    )
    assert unfollowed["followers"] == 0


def test_follow_validation():
    org_id = _seed_org("owner_fv")
    _make_profile(org_id, "owner_fv")
    # Self-follow rejected
    try:
        _svc().follows.follow("owner_fv", actor_id="owner_fv", organization_id=org_id)
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass
    # Cannot follow user without a profile
    try:
        _svc().follows.follow("ghost_user", actor_id="owner_fv", organization_id=org_id)
        assert False, "expected NotFoundError"
    except _errors().NotFoundError:
        pass
    # Double follow rejected
    _make_profile(org_id, "editor_1")
    _svc().follows.follow("editor_1", actor_id="owner_fv", organization_id=org_id)
    try:
        _svc().follows.follow("editor_1", actor_id="owner_fv", organization_id=org_id)
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


# --- Ratings & reviews ---


def test_rating_and_review():
    org_id = _seed_org("owner_r")
    _make_profile(org_id, "owner_r")
    _make_profile(org_id, "editor_1")

    rated = _svc().reviews.rate(
        {
            "organizationId": org_id,
            "assetId": "asset_1",
            "value": 4,
            "assetOwnerUserId": "owner_r",
        },
        actor_id="editor_1",
    )
    assert rated["rating"]["value"] == 4

    reviewed = _svc().reviews.review(
        {
            "organizationId": org_id,
            "assetId": "asset_2",
            "rating": 5,
            "title": "Amazing",
            "body": "Great asset, highly recommended.",
            "assetOwnerUserId": "owner_r",
        },
        actor_id="editor_1",
    )
    assert reviewed["review"]["rating"] == 5

    listed = _svc().reviews.list(
        actor_id="owner_r", organization_id=org_id, asset_id="asset_2"
    )
    assert listed["count"] == 1
    assert listed["avgRating"] == 5.0

    # Owner got rating + review notifications
    notifications = _svc().notifications.list(
        actor_id="owner_r", organization_id=org_id
    )
    types = {n["type"] for n in notifications["notifications"]}
    assert {"rating", "review"} <= types


def test_rating_validation():
    org_id = _seed_org("owner_rv")
    _make_profile(org_id, "owner_rv")
    try:
        _svc().reviews.rate(
            {"organizationId": org_id, "assetId": "a1", "value": 6},
            actor_id="owner_rv",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass
    # Duplicate rating rejected
    _svc().reviews.rate(
        {"organizationId": org_id, "assetId": "a1", "value": 3}, actor_id="owner_rv"
    )
    try:
        _svc().reviews.rate(
            {"organizationId": org_id, "assetId": "a1", "value": 4},
            actor_id="owner_rv",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_duplicate_review_rejected():
    org_id = _seed_org("owner_dd")
    _make_profile(org_id, "owner_dd")
    payload = {
        "organizationId": org_id,
        "assetId": "asset_x",
        "rating": 4,
        "body": "Solid quality.",
    }
    _svc().reviews.review(dict(payload), actor_id="owner_dd")
    try:
        _svc().reviews.review(dict(payload), actor_id="owner_dd")
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass


def test_review_moderation():
    org_id = _seed_org("owner_rm")
    _make_profile(org_id, "editor_1")
    review = _svc().reviews.review(
        {
            "organizationId": org_id,
            "assetId": "asset_m",
            "rating": 1,
            "body": "spammy content here",
        },
        actor_id="editor_1",
    )["review"]
    removed = _svc().reviews.moderate(review["id"], "removed", actor_id="owner_rm")
    assert removed["review"]["status"] == "removed"
    listed = _svc().reviews.list(
        actor_id="owner_rm", organization_id=org_id, asset_id="asset_m"
    )
    assert listed["count"] == 0
    # Non-manager cannot moderate
    try:
        _svc().reviews.moderate(review["id"], "visible", actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


# --- Comments ---


def test_comments_replies_and_mentions():
    org_id = _seed_org("owner_c")
    _make_profile(org_id, "owner_c", handle="bigowner")
    _make_profile(org_id, "editor_1", handle="ed")

    comment = _svc().comments.create(
        {
            "organizationId": org_id,
            "subjectId": "asset_c",
            "body": "Nice work @bigowner, love it!",
        },
        actor_id="editor_1",
    )["comment"]
    assert comment["mentions"] == ["owner_c"]

    reply = _svc().comments.create(
        {
            "organizationId": org_id,
            "subjectId": "asset_c",
            "body": "Thanks a lot!",
            "parentId": comment["id"],
        },
        actor_id="owner_c",
    )["comment"]
    assert reply["parentId"] == comment["id"]

    listed = _svc().comments.list(
        actor_id="owner_c", organization_id=org_id, subject_id="asset_c"
    )
    assert listed["count"] == 2

    # Mention + reply notifications
    owner_notifications = _svc().notifications.list(
        actor_id="owner_c", organization_id=org_id
    )
    assert "mention" in {n["type"] for n in owner_notifications["notifications"]}
    editor_notifications = _svc().notifications.list(
        actor_id="editor_1", organization_id=org_id
    )
    assert "reply" in {n["type"] for n in editor_notifications["notifications"]}


def test_comment_moderation():
    org_id = _seed_org("owner_cm")
    _make_profile(org_id, "editor_1")
    comment = _svc().comments.create(
        {"organizationId": org_id, "subjectId": "s1", "body": "bad content"},
        actor_id="editor_1",
    )["comment"]
    moderated = _svc().comments.moderate(
        comment["id"], "removed", actor_id="owner_cm"
    )
    assert moderated["comment"]["status"] == "removed"
    assert moderated["comment"]["body"] == "[removed]"


def test_spam_protection_rate_limit():
    org_id = _seed_org("owner_sp")
    _make_profile(org_id, "owner_sp")
    catalog = _catalog()
    for i in range(catalog.SPAM_MAX_POSTS_PER_WINDOW):
        _svc().comments.create(
            {"organizationId": org_id, "subjectId": "s1", "body": f"comment {i}"},
            actor_id="owner_sp",
        )
    try:
        _svc().comments.create(
            {"organizationId": org_id, "subjectId": "s1", "body": "one too many"},
            actor_id="owner_sp",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "rate limit" in str(exc).lower()


def test_spam_protection_duplicate_content():
    org_id = _seed_org("owner_dc")
    _make_profile(org_id, "owner_dc")
    _svc().comments.create(
        {"organizationId": org_id, "subjectId": "s1", "body": "Hello World"},
        actor_id="owner_dc",
    )
    try:
        _svc().comments.create(
            {"organizationId": org_id, "subjectId": "s2", "body": "hello   world"},
            actor_id="owner_dc",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError as exc:
        assert "duplicate" in str(exc).lower()


# --- Engagement ---


def test_likes_favorites_bookmarks():
    org_id = _seed_org("owner_e")
    _make_profile(org_id, "owner_e")
    _make_profile(org_id, "editor_1")
    svc = _svc()

    liked = svc.engage(
        {
            "organizationId": org_id,
            "assetId": "asset_e",
            "kind": "like",
            "assetOwnerUserId": "owner_e",
        },
        actor_id="editor_1",
    )
    assert liked["engagement"]["kind"] == "like"

    svc.engage(
        {"organizationId": org_id, "assetId": "asset_e", "kind": "favorite"},
        actor_id="editor_1",
    )
    svc.engage(
        {"organizationId": org_id, "assetId": "asset_e", "kind": "bookmark"},
        actor_id="editor_1",
    )
    mine = svc.list_engagements(actor_id="editor_1", organization_id=org_id)
    assert mine["count"] == 3

    # Duplicate like rejected
    try:
        svc.engage(
            {"organizationId": org_id, "assetId": "asset_e", "kind": "like"},
            actor_id="editor_1",
        )
        assert False, "expected ValidationError"
    except _validation().ValidationError:
        pass

    # Like notification to owner
    notifications = svc.notifications.list(
        actor_id="owner_e", organization_id=org_id
    )
    assert "like" in {n["type"] for n in notifications["notifications"]}

    # Unlike
    svc.unengage(
        {"organizationId": org_id, "assetId": "asset_e", "kind": "like"},
        actor_id="editor_1",
    )
    mine = svc.list_engagements(
        actor_id="editor_1", organization_id=org_id, kind="like"
    )
    assert mine["count"] == 0


# --- Feed, timeline, discovery ---


def test_activity_feed_and_timeline():
    org_id = _seed_org("owner_af")
    _make_profile(org_id, "owner_af")
    _make_profile(org_id, "editor_1")
    svc = _svc()
    svc.follows.follow("owner_af", actor_id="editor_1", organization_id=org_id)
    svc.engage(
        {"organizationId": org_id, "assetId": "a1", "kind": "like"},
        actor_id="owner_af",
    )
    svc.comments.create(
        {"organizationId": org_id, "subjectId": "a1", "body": "great stuff"},
        actor_id="owner_af",
    )

    feed = svc.feed(actor_id="editor_1", organization_id=org_id)
    assert feed["count"] >= 3
    # Followed user's events come first
    assert feed["feed"][0]["actorUserId"] == "owner_af"

    timeline = svc.timeline(
        actor_id="editor_1", organization_id=org_id, user_id="owner_af"
    )
    verbs = {e["verb"] for e in timeline["timeline"]}
    assert {"liked", "commented", "joined"} <= verbs


def test_trending_and_popular_categories():
    org_id = _seed_org("owner_t")
    _make_profile(org_id, "owner_t")
    _make_profile(org_id, "editor_1")
    _make_profile(org_id, "viewer_1")
    svc = _svc()

    svc.follows.follow("owner_t", actor_id="editor_1", organization_id=org_id)
    svc.follows.follow("owner_t", actor_id="viewer_1", organization_id=org_id)
    for actor in ("editor_1", "viewer_1"):
        svc.engage(
            {
                "organizationId": org_id,
                "assetId": "hot_asset",
                "kind": "like",
                "assetCategory": "video",
                "assetOwnerUserId": "owner_t",
            },
            actor_id=actor,
        )
    svc.engage(
        {
            "organizationId": org_id,
            "assetId": "cold_asset",
            "kind": "like",
            "assetCategory": "music",
        },
        actor_id="editor_1",
    )

    trending = svc.trending(actor_id="owner_t", organization_id=org_id)
    assert trending["trendingCreators"][0]["userId"] == "owner_t"
    assert trending["trendingAssets"][0]["assetId"] == "hot_asset"
    assert trending["popularCategories"][0]["category"] == "video"


def test_discovery_recommended_and_featured():
    org_id = _seed_org("owner_d")
    _make_profile(org_id, "owner_d")
    _make_profile(org_id, "editor_1")
    _make_profile(org_id, "viewer_1")
    svc = _svc()
    svc.profiles.verify_member(
        "editor_1", actor_id="owner_d", organization_id=org_id
    )
    svc.follows.follow("editor_1", actor_id="viewer_1", organization_id=org_id)

    discovery = svc.discovery(actor_id="owner_d", organization_id=org_id)
    recommended = discovery["recommendedCreators"]
    assert recommended[0]["userId"] == "editor_1"
    assert recommended[0]["verified"] is True

    svc.set_featured(
        {
            "organizationId": org_id,
            "creators": ["editor_1"],
            "assets": ["asset_ft"],
        },
        actor_id="owner_d",
    )
    discovery = svc.discovery(actor_id="viewer_1", organization_id=org_id)
    assert discovery["featuredCreators"] == ["editor_1"]
    assert discovery["featuredAssets"] == ["asset_ft"]

    # Featured notification delivered
    notifications = svc.notifications.list(
        actor_id="editor_1", organization_id=org_id
    )
    assert "featured" in {n["type"] for n in notifications["notifications"]}

    # Non-manager cannot set featured
    try:
        svc.set_featured(
            {"organizationId": org_id, "creators": ["viewer_1"]},
            actor_id="viewer_1",
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass


# --- Notifications ---


def test_notification_read_state():
    org_id = _seed_org("owner_n")
    _make_profile(org_id, "owner_n")
    _make_profile(org_id, "editor_1")
    svc = _svc()
    svc.follows.follow("owner_n", actor_id="editor_1", organization_id=org_id)

    listed = svc.notifications.list(actor_id="owner_n", organization_id=org_id)
    assert listed["unread"] == 1
    nid = listed["notifications"][0]["id"]

    # Another user cannot read someone else's notification
    try:
        svc.notifications.mark_read(nid, actor_id="editor_1")
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass

    marked = svc.notifications.mark_read(nid, actor_id="owner_n")
    assert marked["notification"]["read"] is True

    svc.engage(
        {
            "organizationId": org_id,
            "assetId": "a9",
            "kind": "like",
            "assetOwnerUserId": "owner_n",
        },
        actor_id="editor_1",
    )
    result = svc.notifications.mark_all_read(
        actor_id="owner_n", organization_id=org_id
    )
    assert result["marked"] == 1
    listed = svc.notifications.list(
        actor_id="owner_n", organization_id=org_id, unread_only=True
    )
    assert listed["count"] == 0


# --- Security ---


def test_security_organization_isolation():
    org_a = _seed_org("owner_oa")
    org_b = _seed_org("owner_ob")
    _make_profile(org_a, "owner_oa")
    svc = _svc()
    # Foreign org member cannot read profiles, feed, or notifications
    try:
        svc.profiles.get(
            actor_id="owner_ob", organization_id=org_a, user_id="owner_oa"
        )
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    try:
        svc.feed(actor_id="owner_ob", organization_id=org_a)
        assert False, "expected ForbiddenError"
    except _errors().ForbiddenError:
        pass
    # Profiles are org-scoped: same handle can exist in another org
    _make_profile(org_b, "owner_ob", handle="owner_oa")
    fetched = svc.profiles.get(
        actor_id="owner_ob", organization_id=org_b, handle="owner_oa"
    )
    assert fetched["profile"]["userId"] == "owner_ob"


def test_security_user_ownership():
    org_id = _seed_org("owner_uo")
    _make_profile(org_id, "owner_uo")
    # editor_1 has no profile; update targets own profile only
    try:
        _svc().profiles.update(
            {"displayName": "Hijack"}, actor_id="editor_1", organization_id=org_id
        )
        assert False, "expected NotFoundError"
    except _errors().NotFoundError:
        pass


def test_security_audit_logging():
    org_id = _seed_org("owner_au")
    audit_store = sys.modules["app.services.enterprise_auth.store"]
    _make_profile(org_id, "owner_au")
    _make_profile(org_id, "editor_1")
    _svc().follows.follow("owner_au", actor_id="editor_1", organization_id=org_id)
    _svc().comments.create(
        {"organizationId": org_id, "subjectId": "s1", "body": "audited comment"},
        actor_id="editor_1",
    )
    events = audit_store.list_audits(limit=500)
    actions = {e.event_type for e in events}
    assert "community.profile_created" in actions
    assert "community.followed" in actions
    assert "community.commented" in actions


# --- Integration ---


def test_full_community_workflow():
    """Profiles -> follow -> engage -> review -> comment -> trending -> notifications."""
    org_id = _seed_org("owner_full")
    svc = _svc()
    _make_profile(org_id, "owner_full", handle="theowner")
    _make_profile(org_id, "editor_1", handle="theeditor")
    _make_profile(org_id, "viewer_1", handle="theviewer")

    svc.profiles.verify_member(
        "owner_full", actor_id="owner_full", organization_id=org_id
    )
    svc.follows.follow("owner_full", actor_id="editor_1", organization_id=org_id)
    svc.follows.follow("owner_full", actor_id="viewer_1", organization_id=org_id)

    svc.engage(
        {
            "organizationId": org_id,
            "assetId": "flagship",
            "kind": "like",
            "assetCategory": "ai_art",
            "assetOwnerUserId": "owner_full",
        },
        actor_id="editor_1",
    )
    svc.reviews.review(
        {
            "organizationId": org_id,
            "assetId": "flagship",
            "rating": 5,
            "title": "Best asset",
            "body": "Absolutely brilliant work by @theowner",
            "assetOwnerUserId": "owner_full",
        },
        actor_id="viewer_1",
    )
    svc.comments.create(
        {
            "organizationId": org_id,
            "subjectId": "flagship",
            "body": "Congrats @theowner on the launch!",
        },
        actor_id="editor_1",
    )

    profile = svc.profiles.get(actor_id="owner_full", organization_id=org_id)
    assert profile["stats"]["followers"] == 2
    assert profile["stats"]["likesReceived"] == 1
    assert profile["stats"]["reputation"] > 10

    trending = svc.trending(actor_id="owner_full", organization_id=org_id)
    assert trending["trendingCreators"][0]["userId"] == "owner_full"
    assert trending["trendingAssets"][0]["assetId"] == "flagship"

    notifications = svc.notifications.list(
        actor_id="owner_full", organization_id=org_id
    )
    types = {n["type"] for n in notifications["notifications"]}
    assert {"follow", "like", "review", "mention"} <= types

    status = svc.status()
    assert status["stats"]["profiles"] == 3
    assert status["stats"]["follows"] == 2
