"""Enterprise Creator Platform & Publisher Ecosystem — Phase 9 Sprint 2.

Engines:
- CreatorEngine (profiles, social links, categories, followers)
- CreatorVerificationEngine (verification requests and review)
- CreatorPortfolioEngine (portfolio showcase and featured assets)
- PublisherEngine (asset drafts, updates, visibility, archive, listing)
- AssetPublishingEngine (immediate + scheduled publishing, versioning)
- CreatorAnalyticsEngine (assets, downloads, purchases, revenue, followers,
  ratings, reviews, engagement, reputation, badges)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.creator_platform import store
from app.services.creator_platform.catalog import (
    ASSET_STATUSES,
    ASSET_TYPES,
    BADGE_DEFINITIONS,
    CREATOR_CATEGORIES,
    ENGAGEMENT_EVENT_TYPES,
    MAX_CATEGORIES_PER_CREATOR,
    MAX_PORTFOLIO_ITEMS,
    POPULAR_DOWNLOADS_THRESHOLD,
    PROLIFIC_THRESHOLD,
    RATING_MAX,
    RATING_MIN,
    RISING_STAR_FOLLOWERS,
    TOP_RATED_MIN_AVG,
    TOP_RATED_MIN_COUNT,
    VISIBILITY_LEVELS,
    compute_engagement,
    compute_reputation,
    is_semver,
    validate_social_links,
)
from app.services.creator_platform.models import (
    CreatorAccount,
    CreatorBadge,
    CreatorFollower,
    CreatorProfile,
    EngagementEvent,
    PublisherAsset,
    new_id,
)
from app.services.creator_platform.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validation():
    from app.services.multi_tenant.validation import ValidationError, require_non_empty

    return ValidationError, require_non_empty


def _auth_errors():
    from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError

    return ForbiddenError, NotFoundError


def _require_access(**kwargs: Any) -> None:
    from app.services.enterprise_auth.middleware import require_access

    require_access(**kwargs)


def _audit(action: str, actor_id: str, detail: str | None = None, **meta: Any) -> None:
    from app.services.enterprise_auth.audit import log_auth_event

    log_auth_event(
        action,
        actor_id=actor_id,
        success=True,
        detail=detail or action,
        metadata=meta,
    )


def _require_member(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id, organization_id=organization_id, permission="org.read"
    )


def _require_manager(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id, organization_id=organization_id, permission="org.update"
    )


def _get_creator_or_404(creator_id: str) -> CreatorAccount:
    _, NotFoundError = _auth_errors()
    creator = store.get_creator(creator_id)
    if creator is None:
        raise NotFoundError("creator not found")
    return creator


def _get_own_creator(organization_id: str, actor_id: str) -> CreatorAccount:
    _, NotFoundError = _auth_errors()
    _require_member(actor_id=actor_id, organization_id=organization_id)
    creator = store.get_creator_by_user(organization_id, actor_id)
    if creator is None:
        raise NotFoundError("creator profile not found")
    return creator


def _award_badge(creator_id: str, badge_key: str) -> bool:
    if store.has_badge(creator_id, badge_key):
        return False
    label, description = BADGE_DEFINITIONS[badge_key]
    store.save_badge(
        CreatorBadge(
            id=new_id("cbg_"),
            creator_id=creator_id,
            badge_key=badge_key,
            label=label,
            description=description,
        )
    )
    return True


def _check_milestone_badges(creator_id: str) -> None:
    published = store.list_assets(creator_id=creator_id, status="published")
    if published:
        _award_badge(creator_id, "first_publish")
    if len(published) >= PROLIFIC_THRESHOLD:
        _award_badge(creator_id, "prolific_creator")
    downloads = len(store.list_events(creator_id=creator_id, event_type="download"))
    if downloads >= POPULAR_DOWNLOADS_THRESHOLD:
        _award_badge(creator_id, "popular")
    ratings = [
        e.rating
        for e in store.list_events(creator_id=creator_id, event_type="rating")
        if e.rating
    ]
    if (
        len(ratings) >= TOP_RATED_MIN_COUNT
        and sum(ratings) / len(ratings) >= TOP_RATED_MIN_AVG
    ):
        _award_badge(creator_id, "top_rated")
    if store.count_followers(creator_id) >= RISING_STAR_FOLLOWERS:
        _award_badge(creator_id, "rising_star")


class CreatorEngine:
    """Creator profile lifecycle, social links, categories, and followers."""

    def create_profile(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(
                    payload.get("organizationId") or payload.get("organization_id"),
                    "organizationId",
                )
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            if store.get_creator_by_user(org_id, actor_id) is not None:
                raise ValidationError("creator profile already exists for this user")
            display_name = str(
                require_non_empty(payload.get("displayName"), "displayName")
            )
            categories = self._validate_categories(payload.get("categories") or [])
            creator = CreatorAccount(
                id=new_id("crt_"),
                user_id=actor_id,
                organization_id=org_id,
                display_name=display_name,
            )
            store.save_creator(creator)
            profile = CreatorProfile(
                id=new_id("cpf_"),
                creator_id=creator.id,
                bio=str(payload.get("bio") or ""),
                avatar_uri=str(payload.get("avatarUri") or ""),
                social_links=validate_social_links(payload.get("socialLinks") or {}),
                categories=categories,
                metadata=dict(payload.get("metadata") or {}),
            )
            store.save_profile(profile)
            _audit("creator_platform.profile_created", actor_id, display_name)
            return {"ok": True, "creator": creator.to_dict(), "profile": profile.to_dict()}

    def get_profile(
        self, *, actor_id: str, organization_id: str, creator_id: str | None = None
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            if creator_id:
                creator = _get_creator_or_404(creator_id)
                ForbiddenError, _ = _auth_errors()
                if creator.organization_id != organization_id:
                    raise ForbiddenError("creator belongs to a different organization")
            else:
                creator = _get_own_creator(organization_id, actor_id)
            profile = store.get_profile(creator.id)
            badges = store.list_badges(creator.id)
            return {
                "ok": True,
                "creator": creator.to_dict(),
                "profile": profile.to_dict() if profile else None,
                "badges": [b.to_dict() for b in badges],
                "followers": store.count_followers(creator.id),
            }

    def update_profile(
        self, payload: dict[str, Any], *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            creator = _get_own_creator(organization_id, actor_id)
            profile = store.get_profile(creator.id)
            assert profile is not None
            if "displayName" in payload and payload["displayName"] is not None:
                name = str(payload["displayName"]).strip()
                if not name:
                    raise ValidationError("displayName must not be empty")
                creator.display_name = name
            if "bio" in payload and payload["bio"] is not None:
                profile.bio = str(payload["bio"])
            if "avatarUri" in payload and payload["avatarUri"] is not None:
                profile.avatar_uri = str(payload["avatarUri"])
            if "socialLinks" in payload and payload["socialLinks"] is not None:
                profile.social_links = validate_social_links(payload["socialLinks"])
            if "categories" in payload and payload["categories"] is not None:
                profile.categories = self._validate_categories(payload["categories"])
            creator.updated_at = _now()
            profile.updated_at = _now()
            store.save_creator(creator)
            store.save_profile(profile)
            _audit("creator_platform.profile_updated", actor_id, creator.display_name)
            return {"ok": True, "creator": creator.to_dict(), "profile": profile.to_dict()}

    def follow(
        self, creator_id: str, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _require_member(actor_id=actor_id, organization_id=organization_id)
            creator = _get_creator_or_404(creator_id)
            if creator.user_id == actor_id:
                raise ValidationError("creators cannot follow themselves")
            if store.is_following(creator_id, actor_id):
                raise ValidationError("already following this creator")
            store.save_follower(
                CreatorFollower(
                    id=new_id("cfl_"),
                    creator_id=creator_id,
                    follower_user_id=actor_id,
                )
            )
            _check_milestone_badges(creator_id)
            _audit("creator_platform.followed", actor_id, creator.display_name)
            return {
                "ok": True,
                "creatorId": creator_id,
                "followers": store.count_followers(creator_id),
            }

    def unfollow(
        self, creator_id: str, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _require_member(actor_id=actor_id, organization_id=organization_id)
            _get_creator_or_404(creator_id)
            if not store.remove_follower(creator_id, actor_id):
                raise ValidationError("not following this creator")
            _audit("creator_platform.unfollowed", actor_id, creator_id)
            return {
                "ok": True,
                "creatorId": creator_id,
                "followers": store.count_followers(creator_id),
            }

    @staticmethod
    def _validate_categories(raw: list[Any]) -> list[str]:
        ValidationError, _ = _validation()
        categories = [str(c).strip().lower() for c in raw if str(c).strip()]
        for c in categories:
            if c not in CREATOR_CATEGORIES:
                raise ValidationError(f"unknown creator category: {c}")
        if len(categories) > MAX_CATEGORIES_PER_CREATOR:
            raise ValidationError(
                f"maximum {MAX_CATEGORIES_PER_CREATOR} categories per creator"
            )
        return sorted(set(categories))


class CreatorVerificationEngine:
    """Verification request and review workflow."""

    def request(
        self, *, actor_id: str, organization_id: str, note: str = ""
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            creator = _get_own_creator(organization_id, actor_id)
            if creator.verification_status == "verified":
                raise ValidationError("creator is already verified")
            if creator.verification_status == "pending":
                raise ValidationError("verification request already pending")
            creator.verification_status = "pending"
            creator.verification_note = str(note or "")
            creator.updated_at = _now()
            store.save_creator(creator)
            _audit(
                "creator_platform.verification_requested",
                actor_id,
                creator.display_name,
            )
            return {"ok": True, "creator": creator.to_dict()}

    def review(
        self,
        creator_id: str,
        *,
        actor_id: str,
        approve: bool,
        note: str = "",
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            creator = _get_creator_or_404(creator_id)
            # Only organization managers may review verification requests
            _require_manager(
                actor_id=actor_id, organization_id=creator.organization_id
            )
            if creator.verification_status != "pending":
                raise ValidationError("no pending verification request")
            if approve:
                creator.verification_status = "verified"
                creator.verified_at = _now()
                _award_badge(creator.id, "verified")
            else:
                creator.verification_status = "rejected"
            creator.verification_note = str(note or "")
            creator.updated_at = _now()
            store.save_creator(creator)
            _audit(
                "creator_platform.verification_reviewed",
                actor_id,
                creator.display_name,
                approved=approve,
            )
            return {"ok": True, "creator": creator.to_dict()}


class CreatorPortfolioEngine:
    """Portfolio showcase items and featured assets."""

    def add_item(
        self, payload: dict[str, Any], *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            creator = _get_own_creator(organization_id, actor_id)
            profile = store.get_profile(creator.id)
            assert profile is not None
            if len(profile.portfolio) >= MAX_PORTFOLIO_ITEMS:
                raise ValidationError(
                    f"maximum {MAX_PORTFOLIO_ITEMS} portfolio items"
                )
            title = str(require_non_empty(payload.get("title"), "title"))
            item = {
                "id": new_id("cpi_"),
                "title": title,
                "description": str(payload.get("description") or ""),
                "mediaUri": str(payload.get("mediaUri") or ""),
                "assetId": payload.get("assetId"),
            }
            asset_id = payload.get("assetId")
            if asset_id:
                asset = store.get_asset(str(asset_id))
                if asset is None or asset.status == "deleted":
                    raise ValidationError(f"asset not found: {asset_id}")
                if asset.creator_id != creator.id:
                    raise ValidationError(
                        "portfolio items may only reference the creator's own assets"
                    )
            profile.portfolio.append(item)
            profile.updated_at = _now()
            store.save_profile(profile)
            _audit("creator_platform.portfolio_item_added", actor_id, title)
            return {"ok": True, "item": item, "portfolio": [dict(p) for p in profile.portfolio]}

    def remove_item(
        self, item_id: str, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            _, NotFoundError = _auth_errors()
            creator = _get_own_creator(organization_id, actor_id)
            profile = store.get_profile(creator.id)
            assert profile is not None
            before = len(profile.portfolio)
            profile.portfolio = [p for p in profile.portfolio if p.get("id") != item_id]
            if len(profile.portfolio) == before:
                raise NotFoundError("portfolio item not found")
            profile.updated_at = _now()
            store.save_profile(profile)
            _audit("creator_platform.portfolio_item_removed", actor_id, item_id)
            return {"ok": True, "portfolio": [dict(p) for p in profile.portfolio]}

    def set_featured(
        self, asset_ids: list[str], *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            creator = _get_own_creator(organization_id, actor_id)
            profile = store.get_profile(creator.id)
            assert profile is not None
            cleaned: list[str] = []
            for aid in asset_ids:
                asset = store.get_asset(str(aid))
                if asset is None or asset.status == "deleted":
                    raise ValidationError(f"asset not found: {aid}")
                if asset.creator_id != creator.id:
                    raise ValidationError(
                        "only the creator's own assets can be featured"
                    )
                cleaned.append(str(aid))
            profile.featured_asset_ids = cleaned
            profile.updated_at = _now()
            store.save_profile(profile)
            _audit("creator_platform.featured_updated", actor_id, str(len(cleaned)))
            return {"ok": True, "featuredAssetIds": cleaned}

    def get(
        self, *, actor_id: str, organization_id: str, creator_id: str | None = None
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            ForbiddenError, _ = _auth_errors()
            if creator_id:
                creator = _get_creator_or_404(creator_id)
                if creator.organization_id != organization_id:
                    raise ForbiddenError("creator belongs to a different organization")
            else:
                creator = _get_own_creator(organization_id, actor_id)
            profile = store.get_profile(creator.id)
            assert profile is not None
            return {
                "ok": True,
                "creatorId": creator.id,
                "portfolio": [dict(p) for p in profile.portfolio],
                "featuredAssetIds": list(profile.featured_asset_ids),
            }


class PublisherEngine:
    """Publisher asset records: drafts, updates, visibility, archive, listing."""

    def _get_asset_for_write(self, asset_id: str, *, actor_id: str) -> PublisherAsset:
        ForbiddenError, NotFoundError = _auth_errors()
        asset = store.get_asset(asset_id)
        if asset is None or asset.status == "deleted":
            raise NotFoundError("asset not found")
        if asset.owner_user_id != actor_id:
            try:
                _require_manager(
                    actor_id=actor_id, organization_id=asset.organization_id
                )
            except Exception:
                raise ForbiddenError("only the asset owner can perform this action")
        return asset

    def create_draft(self, payload: dict[str, Any], *, actor_id: str) -> PublisherAsset:
        ValidationError, require_non_empty = _validation()
        _, NotFoundError = _auth_errors()
        org_id = str(
            require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
        )
        _require_member(actor_id=actor_id, organization_id=org_id)
        creator = store.get_creator_by_user(org_id, actor_id)
        if creator is None:
            raise NotFoundError(
                "creator profile required before publishing assets"
            )
        name = str(require_non_empty(payload.get("name"), "name"))
        asset_type = str(payload.get("assetType") or "custom")
        if asset_type not in ASSET_TYPES:
            raise ValidationError(f"unknown asset type: {asset_type}")
        visibility = str(payload.get("visibility") or "public")
        if visibility not in VISIBILITY_LEVELS:
            raise ValidationError(f"unknown visibility: {visibility}")
        tags = [
            str(t).strip().lower()
            for t in (payload.get("tags") or [])
            if str(t).strip()
        ]
        asset = PublisherAsset(
            id=new_id("pba_"),
            organization_id=org_id,
            creator_id=creator.id,
            owner_user_id=actor_id,
            name=name,
            asset_type=asset_type,
            description=str(payload.get("description") or ""),
            category=str(payload.get("category") or "other"),
            tags=sorted(set(tags)),
            visibility=visibility,
            asset_uri=str(payload.get("assetUri") or ""),
            price_credits=float(payload.get("priceCredits") or 0.0),
            metadata=dict(payload.get("metadata") or {}),
        )
        asset.versions.append(
            {
                "version": asset.current_version,
                "changelog": "Initial version",
                "createdAt": _now().isoformat(),
            }
        )
        store.save_asset(asset)
        return asset

    def update(
        self, asset_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            asset = self._get_asset_for_write(asset_id, actor_id=actor_id)
            if "name" in payload and payload["name"] is not None:
                name = str(payload["name"]).strip()
                if not name:
                    raise ValidationError("name must not be empty")
                asset.name = name
            if "description" in payload and payload["description"] is not None:
                asset.description = str(payload["description"])
            if "category" in payload and payload["category"] is not None:
                asset.category = str(payload["category"])
            if "tags" in payload and payload["tags"] is not None:
                asset.tags = sorted(
                    {str(t).strip().lower() for t in payload["tags"] if str(t).strip()}
                )
            if "visibility" in payload and payload["visibility"] is not None:
                visibility = str(payload["visibility"])
                if visibility not in VISIBILITY_LEVELS:
                    raise ValidationError(f"unknown visibility: {visibility}")
                asset.visibility = visibility
            if "assetUri" in payload and payload["assetUri"] is not None:
                asset.asset_uri = str(payload["assetUri"])
            if "priceCredits" in payload and payload["priceCredits"] is not None:
                asset.price_credits = float(payload["priceCredits"])
            if payload.get("version"):
                version = str(payload["version"])
                if not is_semver(version):
                    raise ValidationError("version must be semver (e.g. 1.2.0)")
                if any(v.get("version") == version for v in asset.versions):
                    raise ValidationError(f"version {version} already exists")
                asset.versions.append(
                    {
                        "version": version,
                        "changelog": str(payload.get("changelog") or ""),
                        "createdAt": _now().isoformat(),
                    }
                )
                asset.current_version = version
            if payload.get("status"):
                target = str(payload["status"])
                if target not in ASSET_STATUSES or target in ("deleted", "scheduled"):
                    raise ValidationError(f"invalid status transition: {target}")
                if target == "published":
                    ValidationError_, _ = _validation()
                    if not asset.asset_uri:
                        raise ValidationError_(
                            "assets require an assetUri before publishing"
                        )
                    asset.status = "published"
                    asset.published_at = _now()
                    asset.archived_at = None
                    _check_milestone_badges(asset.creator_id)
                    _audit(
                        "creator_platform.asset_published", actor_id, asset.name
                    )
                elif target == "archived":
                    asset.status = "archived"
                    asset.archived_at = _now()
                    _audit(
                        "creator_platform.asset_archived", actor_id, asset.name
                    )
                elif target == "draft":
                    asset.status = "draft"
                    asset.published_at = None
                    asset.archived_at = None
                    asset.publish_at = None
            asset.updated_at = _now()
            store.save_asset(asset)
            _audit("creator_platform.asset_updated", actor_id, asset.name)
            return {"ok": True, "asset": asset.to_dict(include_asset_uri=True)}

    def delete(self, asset_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            asset = self._get_asset_for_write(asset_id, actor_id=actor_id)
            asset.status = "deleted"
            asset.deleted_at = _now()
            asset.updated_at = _now()
            store.save_asset(asset)
            _audit("creator_platform.asset_deleted", actor_id, asset.name)
            return {"ok": True, "assetId": asset_id, "status": "deleted"}

    def list(
        self,
        *,
        actor_id: str,
        organization_id: str,
        status: str | None = None,
        creator_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            items = store.list_assets(
                organization_id=organization_id,
                creator_id=creator_id,
                status=status,
                limit=max(1, min(limit, 500)),
            )
            return {
                "ok": True,
                "count": len(items),
                "assets": [a.to_dict() for a in items],
            }


class AssetPublishingEngine:
    """Immediate and scheduled publishing on top of the publisher engine."""

    def __init__(self, publisher: PublisherEngine) -> None:
        self._publisher = publisher

    def publish(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            asset_id = payload.get("assetId")
            if asset_id:
                asset = self._publisher._get_asset_for_write(
                    str(asset_id), actor_id=actor_id
                )
            else:
                asset = self._publisher.create_draft(payload, actor_id=actor_id)
            draft_only = bool(payload.get("draft"))
            publish_at_raw = payload.get("publishAt")
            if draft_only:
                _audit("creator_platform.asset_drafted", actor_id, asset.name)
                return {"ok": True, "asset": asset.to_dict(include_asset_uri=True)}
            if not asset.asset_uri:
                raise ValidationError("assets require an assetUri before publishing")
            if publish_at_raw:
                publish_at = self._parse_dt(str(publish_at_raw))
                if publish_at > _now():
                    asset.status = "scheduled"
                    asset.publish_at = publish_at
                    asset.updated_at = _now()
                    store.save_asset(asset)
                    _audit(
                        "creator_platform.asset_scheduled", actor_id, asset.name,
                        publishAt=publish_at.isoformat(),
                    )
                    return {
                        "ok": True,
                        "asset": asset.to_dict(include_asset_uri=True),
                        "scheduled": True,
                    }
            asset.status = "published"
            asset.published_at = _now()
            asset.publish_at = None
            asset.updated_at = _now()
            store.save_asset(asset)
            _check_milestone_badges(asset.creator_id)
            _audit("creator_platform.asset_published", actor_id, asset.name)
            return {"ok": True, "asset": asset.to_dict(include_asset_uri=True)}

    def process_due(self) -> dict[str, Any]:
        """Publish all scheduled assets whose publish time has arrived."""
        with store.timed_op():
            due = store.list_due_scheduled(_now())
            published = []
            for asset in due:
                asset.status = "published"
                asset.published_at = _now()
                asset.publish_at = None
                asset.updated_at = _now()
                store.save_asset(asset)
                _check_milestone_badges(asset.creator_id)
                _audit(
                    "creator_platform.asset_published",
                    asset.owner_user_id,
                    asset.name,
                    scheduled=True,
                )
                published.append(asset.to_dict())
            return {"ok": True, "published": published, "count": len(published)}

    @staticmethod
    def _parse_dt(value: str) -> datetime:
        ValidationError, _ = _validation()
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationError("publishAt must be an ISO-8601 timestamp")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt


class CreatorAnalyticsEngine:
    """Creator analytics: assets, engagement, revenue, followers, reputation."""

    def record_event(
        self,
        payload: dict[str, Any],
        *,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            creator_id = str(
                require_non_empty(payload.get("creatorId"), "creatorId")
            )
            _get_creator_or_404(creator_id)
            event_type = str(payload.get("eventType") or "")
            if event_type not in ENGAGEMENT_EVENT_TYPES:
                raise ValidationError(f"unknown event type: {event_type}")
            rating = int(payload.get("rating") or 0)
            if event_type == "rating" and not (RATING_MIN <= rating <= RATING_MAX):
                raise ValidationError(
                    f"rating must be between {RATING_MIN} and {RATING_MAX}"
                )
            event = EngagementEvent(
                id=new_id("cev_"),
                creator_id=creator_id,
                event_type=event_type,
                asset_id=payload.get("assetId"),
                user_id=actor_id,
                amount_credits=float(payload.get("amountCredits") or 0.0),
                rating=rating,
            )
            store.save_event(event)
            _check_milestone_badges(creator_id)
            return {"ok": True, "event": event.to_dict()}

    def summary(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            creator = _get_own_creator(organization_id, actor_id)
            return {"ok": True, "analytics": self._summary_for(creator)}

    def _summary_for(self, creator: CreatorAccount) -> dict[str, Any]:
        assets = store.list_assets(creator_id=creator.id)
        events = store.list_events(creator_id=creator.id)
        counts: dict[str, int] = {}
        revenue = 0.0
        ratings: list[int] = []
        for e in events:
            counts[e.event_type] = counts.get(e.event_type, 0) + 1
            revenue += e.amount_credits
            if e.event_type == "rating" and e.rating:
                ratings.append(e.rating)
        followers = store.count_followers(creator.id)
        counts["follower"] = followers
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        badges = store.list_badges(creator.id)
        reputation = compute_reputation(
            badges=len(badges),
            downloads=counts.get("download", 0),
            purchases=counts.get("purchase", 0),
            avg_rating=avg_rating,
            followers=followers,
            verified=creator.verified,
        )
        return {
            "creatorId": creator.id,
            "totalAssets": len(assets),
            "publishedAssets": sum(1 for a in assets if a.status == "published"),
            "draftAssets": sum(1 for a in assets if a.status == "draft"),
            "scheduledAssets": sum(1 for a in assets if a.status == "scheduled"),
            "archivedAssets": sum(1 for a in assets if a.status == "archived"),
            "views": counts.get("view", 0),
            "downloads": counts.get("download", 0),
            "purchases": counts.get("purchase", 0),
            "revenueCredits": round(revenue, 2),
            "followers": followers,
            "avgRating": round(avg_rating, 2),
            "ratings": len(ratings),
            "reviews": counts.get("review", 0),
            "engagementScore": compute_engagement(counts),
            "reputation": reputation,
            "badges": [b.to_dict() for b in badges],
            "verified": creator.verified,
        }


class CreatorPlatformEngine:
    """Facade combining creator, verification, portfolio, publisher & analytics."""

    def __init__(self) -> None:
        self.creators = CreatorEngine()
        self.verification = CreatorVerificationEngine()
        self.portfolio = CreatorPortfolioEngine()
        self.publisher = PublisherEngine()
        self.publishing = AssetPublishingEngine(self.publisher)
        self.analytics = CreatorAnalyticsEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "creator": "ready",
                "publisher": "ready",
                "creatorVerification": "ready",
                "creatorPortfolio": "ready",
                "assetPublishing": "ready",
                "creatorAnalytics": "ready",
            },
            "creatorCategories": list(CREATOR_CATEGORIES),
            "assetTypes": list(ASSET_TYPES),
            "badges": sorted(BADGE_DEFINITIONS.keys()),
            "stats": store.metrics(),
        }


_service: CreatorPlatformEngine | None = None


def get_creator_platform_service() -> CreatorPlatformEngine:
    global _service
    if _service is None:
        _service = CreatorPlatformEngine()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    _service = None


get_engine = get_creator_platform_service
