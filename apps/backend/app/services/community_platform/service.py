"""Enterprise Community Platform & Social Collaboration Engine — Phase 9 Sprint 3.

Engines:
- UserProfileEngine (public profiles, verified members, reputation)
- FollowSystem (follow/unfollow, followers/following)
- RatingReviewEngine (ratings 1-5, reviews, moderation)
- CommentsEngine (comments, replies, mentions, moderation)
- NotificationEngine (community notifications, read state)
- CommunityEngine (facade + discovery: feed, timeline, trending,
  recommended, featured, popular categories; likes/favorites/bookmarks)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.community_platform import store
from app.services.community_platform.catalog import (
    ENGAGEMENT_KINDS,
    MAX_BIO_LENGTH,
    MAX_COMMENT_LENGTH,
    MAX_REVIEW_LENGTH,
    MODERATION_STATUSES,
    NOTIFICATION_TYPES,
    RATING_MAX,
    RATING_MIN,
    RECOMMENDED_LIMIT,
    SPAM_DUPLICATE_WINDOW_SECONDS,
    SPAM_MAX_POSTS_PER_WINDOW,
    SPAM_WINDOW_SECONDS,
    TRENDING_LIMIT,
    TRENDING_WINDOW_HOURS,
    compute_reputation,
    extract_mentions,
)
from app.services.community_platform.models import (
    ActivityEvent,
    Comment,
    Engagement,
    FollowEdge,
    Notification,
    RatingRecord,
    Review,
    UserProfile,
    new_id,
)
from app.services.community_platform.version import (
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
        action, actor_id=actor_id, success=True, detail=detail or action, metadata=meta
    )


def _require_member(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id, organization_id=organization_id, permission="org.read"
    )


def _require_manager(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id, organization_id=organization_id, permission="org.update"
    )


def _notify(
    *,
    organization_id: str,
    recipient: str,
    notification_type: str,
    actor: str = "",
    subject_id: str = "",
    message: str = "",
) -> None:
    assert notification_type in NOTIFICATION_TYPES
    if recipient == actor or not recipient:
        return
    store.save_notification(
        Notification(
            id=new_id("ntf_"),
            organization_id=organization_id,
            recipient_user_id=recipient,
            notification_type=notification_type,
            actor_user_id=actor,
            subject_id=subject_id,
            message=message,
        )
    )


def _record_activity(
    *, organization_id: str, actor: str, verb: str, subject_id: str = "", detail: str = ""
) -> None:
    store.save_activity(
        ActivityEvent(
            id=new_id("act_"),
            organization_id=organization_id,
            actor_user_id=actor,
            verb=verb,
            subject_id=subject_id,
            detail=detail,
        )
    )


def _spam_guard(organization_id: str, author: str, body: str) -> None:
    """Sliding-window rate limit + duplicate content detection."""
    ValidationError, _ = _validation()
    window_start = _now() - timedelta(seconds=SPAM_WINDOW_SECONDS)
    recent = [
        c
        for c in store.list_comments(
            organization_id=organization_id, author=author, include_hidden=True
        )
        if c.created_at >= window_start
    ] + [
        r
        for r in store.list_reviews(
            organization_id=organization_id, author=author, include_hidden=True
        )
        if r.created_at >= window_start
    ]
    if len(recent) >= SPAM_MAX_POSTS_PER_WINDOW:
        raise ValidationError(
            "rate limit exceeded: too many posts, please slow down"
        )
    dup_start = _now() - timedelta(seconds=SPAM_DUPLICATE_WINDOW_SECONDS)
    normalized = " ".join((body or "").lower().split())
    if normalized:
        for c in store.list_comments(
            organization_id=organization_id, author=author, include_hidden=True
        ):
            if c.created_at >= dup_start and " ".join(c.body.lower().split()) == normalized:
                raise ValidationError("duplicate content detected")
        for r in store.list_reviews(
            organization_id=organization_id, author=author, include_hidden=True
        ):
            if r.created_at >= dup_start and " ".join(r.body.lower().split()) == normalized:
                raise ValidationError("duplicate content detected")


def _mention_targets(
    organization_id: str, body: str, explicit: list[str] | None
) -> list[str]:
    """Resolve @handle mentions to user ids (plus explicit user ids)."""
    targets: set[str] = set(explicit or [])
    for handle in extract_mentions(body):
        profile = store.get_profile_by_handle(organization_id, handle)
        if profile is not None:
            targets.add(profile.user_id)
    return sorted(targets)


class UserProfileEngine:
    """Public profiles, verified members, and user reputation."""

    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            if store.get_profile_by_user(org_id, actor_id) is not None:
                raise ValidationError("profile already exists for this user")
            display_name = str(
                require_non_empty(payload.get("displayName"), "displayName")
            )
            handle = str(
                require_non_empty(payload.get("handle"), "handle")
            ).strip().lower()
            if not handle.replace("_", "").replace("-", "").replace(".", "").isalnum():
                raise ValidationError("handle must be alphanumeric with _-. only")
            if store.get_profile_by_handle(org_id, handle) is not None:
                raise ValidationError(f"handle already taken: {handle}")
            bio = str(payload.get("bio") or "")
            if len(bio) > MAX_BIO_LENGTH:
                raise ValidationError(f"bio exceeds {MAX_BIO_LENGTH} characters")
            profile = UserProfile(
                id=new_id("usp_"),
                user_id=actor_id,
                organization_id=org_id,
                display_name=display_name,
                handle=handle,
                bio=bio,
                avatar_uri=str(payload.get("avatarUri") or ""),
            )
            store.save_profile(profile)
            _record_activity(
                organization_id=org_id, actor=actor_id, verb="joined",
                detail=display_name,
            )
            _audit("community.profile_created", actor_id, display_name)
            return {"ok": True, "profile": profile.to_dict()}

    def get(
        self, *, actor_id: str, organization_id: str, user_id: str | None = None,
        handle: str | None = None,
    ) -> dict[str, Any]:
        with store.timed_op():
            _, NotFoundError = _auth_errors()
            _require_member(actor_id=actor_id, organization_id=organization_id)
            if handle:
                profile = store.get_profile_by_handle(organization_id, handle)
            else:
                profile = store.get_profile_by_user(
                    organization_id, user_id or actor_id
                )
            if profile is None:
                raise NotFoundError("profile not found")
            return {
                "ok": True,
                "profile": profile.to_dict(),
                "stats": self.stats(profile),
            }

    def update(
        self, payload: dict[str, Any], *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _, NotFoundError = _auth_errors()
            _require_member(actor_id=actor_id, organization_id=organization_id)
            profile = store.get_profile_by_user(organization_id, actor_id)
            if profile is None:
                raise NotFoundError("profile not found")
            if "displayName" in payload and payload["displayName"] is not None:
                name = str(payload["displayName"]).strip()
                if not name:
                    raise ValidationError("displayName must not be empty")
                profile.display_name = name
            if "bio" in payload and payload["bio"] is not None:
                bio = str(payload["bio"])
                if len(bio) > MAX_BIO_LENGTH:
                    raise ValidationError(f"bio exceeds {MAX_BIO_LENGTH} characters")
                profile.bio = bio
            if "avatarUri" in payload and payload["avatarUri"] is not None:
                profile.avatar_uri = str(payload["avatarUri"])
            profile.updated_at = _now()
            store.save_profile(profile)
            _audit("community.profile_updated", actor_id, profile.display_name)
            return {"ok": True, "profile": profile.to_dict()}

    def verify_member(
        self, target_user_id: str, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            _, NotFoundError = _auth_errors()
            _require_manager(actor_id=actor_id, organization_id=organization_id)
            profile = store.get_profile_by_user(organization_id, target_user_id)
            if profile is None:
                raise NotFoundError("profile not found")
            profile.verified = True
            profile.verified_at = _now()
            profile.updated_at = _now()
            store.save_profile(profile)
            _audit(
                "community.member_verified", actor_id, profile.display_name,
                target=target_user_id,
            )
            return {"ok": True, "profile": profile.to_dict()}

    def stats(self, profile: UserProfile) -> dict[str, Any]:
        org = profile.organization_id
        uid = profile.user_id
        followers = len(store.list_followers(org, uid))
        following = len(store.list_following(org, uid))
        reviews = len(store.list_reviews(organization_id=org, author=uid))
        comments = len(store.list_comments(organization_id=org, author=uid))
        likes_received = len(
            [
                e
                for e in store.list_engagements(organization_id=org, kind="like")
                if e.asset_owner_user_id == uid
            ]
        )
        reputation = compute_reputation(
            followers=followers,
            reviews_written=reviews,
            comments_written=comments,
            likes_received=likes_received,
            verified=profile.verified,
        )
        return {
            "followers": followers,
            "following": following,
            "reviews": reviews,
            "comments": comments,
            "likesReceived": likes_received,
            "reputation": reputation,
        }


class FollowSystem:
    """Follow / unfollow users and list followers/following."""

    def follow(
        self, target_user_id: str, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _, NotFoundError = _auth_errors()
            _require_member(actor_id=actor_id, organization_id=organization_id)
            if target_user_id == actor_id:
                raise ValidationError("users cannot follow themselves")
            if store.get_profile_by_user(organization_id, target_user_id) is None:
                raise NotFoundError("target profile not found")
            if store.is_following(organization_id, actor_id, target_user_id):
                raise ValidationError("already following this user")
            store.save_follow(
                FollowEdge(
                    id=new_id("flw_"),
                    organization_id=organization_id,
                    follower_user_id=actor_id,
                    target_user_id=target_user_id,
                )
            )
            _notify(
                organization_id=organization_id,
                recipient=target_user_id,
                notification_type="follow",
                actor=actor_id,
                message="started following you",
            )
            _record_activity(
                organization_id=organization_id, actor=actor_id, verb="followed",
                subject_id=target_user_id,
            )
            _audit("community.followed", actor_id, target_user_id)
            return {
                "ok": True,
                "targetUserId": target_user_id,
                "followers": len(store.list_followers(organization_id, target_user_id)),
            }

    def unfollow(
        self, target_user_id: str, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _require_member(actor_id=actor_id, organization_id=organization_id)
            if not store.remove_follow(organization_id, actor_id, target_user_id):
                raise ValidationError("not following this user")
            _audit("community.unfollowed", actor_id, target_user_id)
            return {
                "ok": True,
                "targetUserId": target_user_id,
                "followers": len(store.list_followers(organization_id, target_user_id)),
            }

    def followers(
        self, *, actor_id: str, organization_id: str, user_id: str | None = None
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            uid = user_id or actor_id
            edges = store.list_followers(organization_id, uid)
            return {
                "ok": True,
                "userId": uid,
                "count": len(edges),
                "followers": [e.to_dict() for e in edges],
            }

    def following(
        self, *, actor_id: str, organization_id: str, user_id: str | None = None
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            uid = user_id or actor_id
            edges = store.list_following(organization_id, uid)
            return {
                "ok": True,
                "userId": uid,
                "count": len(edges),
                "following": [e.to_dict() for e in edges],
            }


class RatingReviewEngine:
    """Ratings (1-5), reviews with moderation and spam protection."""

    def rate(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            asset_id = str(require_non_empty(payload.get("assetId"), "assetId"))
            value = int(payload.get("value") or 0)
            if not (RATING_MIN <= value <= RATING_MAX):
                raise ValidationError(
                    f"rating must be between {RATING_MIN} and {RATING_MAX}"
                )
            if store.list_ratings(
                organization_id=org_id, asset_id=asset_id, user_id=actor_id
            ):
                raise ValidationError("asset already rated by this user")
            rating = RatingRecord(
                id=new_id("rtg_"),
                organization_id=org_id,
                asset_id=asset_id,
                user_id=actor_id,
                value=value,
            )
            store.save_rating(rating)
            _record_activity(
                organization_id=org_id, actor=actor_id, verb="rated",
                subject_id=asset_id, detail=str(value),
            )
            owner = str(payload.get("assetOwnerUserId") or "")
            _notify(
                organization_id=org_id, recipient=owner, notification_type="rating",
                actor=actor_id, subject_id=asset_id, message=f"rated your asset {value}/5",
            )
            _audit("community.rated", actor_id, asset_id, value=value)
            return {"ok": True, "rating": rating.to_dict()}

    def review(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            asset_id = str(require_non_empty(payload.get("assetId"), "assetId"))
            rating = int(payload.get("rating") or 0)
            if not (RATING_MIN <= rating <= RATING_MAX):
                raise ValidationError(
                    f"rating must be between {RATING_MIN} and {RATING_MAX}"
                )
            body = str(payload.get("body") or "")
            if len(body) > MAX_REVIEW_LENGTH:
                raise ValidationError(f"review exceeds {MAX_REVIEW_LENGTH} characters")
            if store.list_reviews(
                organization_id=org_id, asset_id=asset_id, author=actor_id,
                include_hidden=True,
            ):
                raise ValidationError("asset already reviewed by this user")
            _spam_guard(org_id, actor_id, body)
            review = Review(
                id=new_id("rvw_"),
                organization_id=org_id,
                asset_id=asset_id,
                author_user_id=actor_id,
                rating=rating,
                title=str(payload.get("title") or ""),
                body=body,
                asset_category=str(payload.get("assetCategory") or ""),
            )
            store.save_review(review)
            if not store.list_ratings(
                organization_id=org_id, asset_id=asset_id, user_id=actor_id
            ):
                store.save_rating(
                    RatingRecord(
                        id=new_id("rtg_"),
                        organization_id=org_id,
                        asset_id=asset_id,
                        user_id=actor_id,
                        value=rating,
                    )
                )
            _record_activity(
                organization_id=org_id, actor=actor_id, verb="reviewed",
                subject_id=asset_id, detail=review.title,
            )
            owner = str(payload.get("assetOwnerUserId") or "")
            _notify(
                organization_id=org_id, recipient=owner, notification_type="review",
                actor=actor_id, subject_id=asset_id, message="reviewed your asset",
            )
            _audit("community.reviewed", actor_id, asset_id, rating=rating)
            return {"ok": True, "review": review.to_dict()}

    def list(
        self, *, actor_id: str, organization_id: str, asset_id: str | None = None
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            reviews = store.list_reviews(
                organization_id=organization_id, asset_id=asset_id
            )
            ratings = store.list_ratings(
                organization_id=organization_id, asset_id=asset_id
            )
            avg = (
                round(sum(r.value for r in ratings) / len(ratings), 2)
                if ratings
                else 0.0
            )
            return {
                "ok": True,
                "count": len(reviews),
                "avgRating": avg,
                "ratings": len(ratings),
                "reviews": [r.to_dict() for r in reviews],
            }

    def moderate(
        self, review_id: str, status: str, *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _, NotFoundError = _auth_errors()
            review = store.get_review(review_id)
            if review is None:
                raise NotFoundError("review not found")
            _require_manager(
                actor_id=actor_id, organization_id=review.organization_id
            )
            if status not in MODERATION_STATUSES:
                raise ValidationError(f"unknown moderation status: {status}")
            review.status = status
            review.updated_at = _now()
            store.save_review(review)
            _audit(
                "community.review_moderated", actor_id, review_id, status=status
            )
            return {"ok": True, "review": review.to_dict()}


class CommentsEngine:
    """Comments, threaded replies, @mentions, and moderation."""

    def create(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            _, NotFoundError = _auth_errors()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            subject_id = str(require_non_empty(payload.get("subjectId"), "subjectId"))
            body = str(require_non_empty(payload.get("body"), "body"))
            if len(body) > MAX_COMMENT_LENGTH:
                raise ValidationError(
                    f"comment exceeds {MAX_COMMENT_LENGTH} characters"
                )
            _spam_guard(org_id, actor_id, body)
            parent_id = payload.get("parentId")
            parent: Comment | None = None
            if parent_id:
                parent = store.get_comment(str(parent_id))
                if parent is None or parent.status == "removed":
                    raise NotFoundError("parent comment not found")
                if parent.organization_id != org_id:
                    ForbiddenError, _ = _auth_errors()
                    raise ForbiddenError(
                        "parent comment belongs to a different organization"
                    )
            mentions = _mention_targets(org_id, body, payload.get("mentions"))
            comment = Comment(
                id=new_id("cmt_"),
                organization_id=org_id,
                subject_id=subject_id,
                author_user_id=actor_id,
                body=body,
                parent_id=str(parent_id) if parent_id else None,
                mentions=mentions,
            )
            store.save_comment(comment)
            verb = "replied" if parent is not None else "commented"
            _record_activity(
                organization_id=org_id, actor=actor_id, verb=verb,
                subject_id=subject_id,
            )
            if parent is not None:
                _notify(
                    organization_id=org_id,
                    recipient=parent.author_user_id,
                    notification_type="reply",
                    actor=actor_id,
                    subject_id=comment.id,
                    message="replied to your comment",
                )
            for target in mentions:
                _notify(
                    organization_id=org_id,
                    recipient=target,
                    notification_type="mention",
                    actor=actor_id,
                    subject_id=comment.id,
                    message="mentioned you in a comment",
                )
            _audit("community.commented", actor_id, subject_id)
            return {"ok": True, "comment": comment.to_dict()}

    def list(
        self,
        *,
        actor_id: str,
        organization_id: str,
        subject_id: str | None = None,
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            comments = store.list_comments(
                organization_id=organization_id,
                subject_id=subject_id,
                parent_id=parent_id,
            )
            comments.sort(key=lambda c: c.created_at)
            return {
                "ok": True,
                "count": len(comments),
                "comments": [c.to_dict() for c in comments],
            }

    def moderate(
        self, comment_id: str, status: str, *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _, NotFoundError = _auth_errors()
            comment = store.get_comment(comment_id)
            if comment is None:
                raise NotFoundError("comment not found")
            _require_manager(
                actor_id=actor_id, organization_id=comment.organization_id
            )
            if status not in MODERATION_STATUSES:
                raise ValidationError(f"unknown moderation status: {status}")
            comment.status = status
            comment.updated_at = _now()
            store.save_comment(comment)
            _audit(
                "community.comment_moderated", actor_id, comment_id, status=status
            )
            return {"ok": True, "comment": comment.to_dict()}


class NotificationEngine:
    """Community notifications with read state."""

    def list(
        self,
        *,
        actor_id: str,
        organization_id: str,
        unread_only: bool = False,
        limit: int = 100,
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            items = store.list_notifications(
                organization_id, actor_id, unread_only=unread_only
            )
            unread = sum(1 for n in items if not n.read) if not unread_only else len(items)
            return {
                "ok": True,
                "count": len(items[:limit]),
                "unread": unread,
                "notifications": [n.to_dict() for n in items[:limit]],
            }

    def mark_read(self, notification_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ForbiddenError, NotFoundError = _auth_errors()
            notification = store.get_notification(notification_id)
            if notification is None:
                raise NotFoundError("notification not found")
            if notification.recipient_user_id != actor_id:
                raise ForbiddenError("notification belongs to a different user")
            notification.read = True
            notification.read_at = _now()
            store.save_notification(notification)
            return {"ok": True, "notification": notification.to_dict()}

    def mark_all_read(
        self, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            items = store.list_notifications(
                organization_id, actor_id, unread_only=True
            )
            for n in items:
                n.read = True
                n.read_at = _now()
                store.save_notification(n)
            return {"ok": True, "marked": len(items)}


class CommunityEngine:
    """Facade + engagement (likes/favorites/bookmarks), feed, and discovery."""

    def __init__(self) -> None:
        self.profiles = UserProfileEngine()
        self.follows = FollowSystem()
        self.reviews = RatingReviewEngine()
        self.comments = CommentsEngine()
        self.notifications = NotificationEngine()

    # --- Engagement ---

    def engage(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            asset_id = str(require_non_empty(payload.get("assetId"), "assetId"))
            kind = str(payload.get("kind") or "like")
            if kind not in ENGAGEMENT_KINDS:
                raise ValidationError(f"unknown engagement kind: {kind}")
            if store.has_engagement(asset_id, actor_id, kind):
                raise ValidationError(f"asset already {kind}d by this user")
            engagement = Engagement(
                id=new_id("eng_"),
                organization_id=org_id,
                asset_id=asset_id,
                user_id=actor_id,
                kind=kind,
                asset_category=str(payload.get("assetCategory") or ""),
                asset_owner_user_id=str(payload.get("assetOwnerUserId") or ""),
            )
            store.save_engagement(engagement)
            verb = {"like": "liked", "favorite": "favorited", "bookmark": "bookmarked"}[kind]
            _record_activity(
                organization_id=org_id, actor=actor_id, verb=verb, subject_id=asset_id
            )
            if kind == "like":
                _notify(
                    organization_id=org_id,
                    recipient=engagement.asset_owner_user_id,
                    notification_type="like",
                    actor=actor_id,
                    subject_id=asset_id,
                    message="liked your asset",
                )
            _audit(f"community.{verb}", actor_id, asset_id)
            return {"ok": True, "engagement": engagement.to_dict()}

    def unengage(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            asset_id = str(require_non_empty(payload.get("assetId"), "assetId"))
            kind = str(payload.get("kind") or "like")
            if not store.remove_engagement(asset_id, actor_id, kind):
                raise ValidationError(f"asset not {kind}d by this user")
            _audit(f"community.un{kind}", actor_id, asset_id)
            return {"ok": True, "assetId": asset_id, "kind": kind}

    def list_engagements(
        self, *, actor_id: str, organization_id: str, kind: str | None = None
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            items = store.list_engagements(
                organization_id=organization_id, user_id=actor_id, kind=kind
            )
            return {
                "ok": True,
                "count": len(items),
                "engagements": [e.to_dict() for e in items],
            }

    # --- Feed & timeline ---

    def feed(
        self, *, actor_id: str, organization_id: str, limit: int = 50
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            following = {
                e.target_user_id
                for e in store.list_following(organization_id, actor_id)
            }
            events = store.list_activity(organization_id=organization_id)
            # Prioritize activity from followed users, then the rest of the org
            followed_events = [e for e in events if e.actor_user_id in following]
            other_events = [
                e
                for e in events
                if e.actor_user_id not in following and e.actor_user_id != actor_id
            ]
            combined = (followed_events + other_events)[: max(1, min(limit, 200))]
            return {
                "ok": True,
                "count": len(combined),
                "feed": [e.to_dict() for e in combined],
            }

    def timeline(
        self, *, actor_id: str, organization_id: str, user_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            uid = user_id or actor_id
            events = store.list_activity(
                organization_id=organization_id, actor=uid
            )[: max(1, min(limit, 200))]
            return {
                "ok": True,
                "userId": uid,
                "count": len(events),
                "timeline": [e.to_dict() for e in events],
            }

    # --- Discovery ---

    def trending(
        self, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            since = _now() - timedelta(hours=TRENDING_WINDOW_HOURS)

            # Trending creators: recent follows + likes received
            creator_scores: dict[str, float] = {}
            for edge in store.list_follows(organization_id):
                if edge.created_at >= since:
                    creator_scores[edge.target_user_id] = (
                        creator_scores.get(edge.target_user_id, 0.0) + 2.0
                    )
            engagements = store.list_engagements(organization_id=organization_id)
            asset_scores: dict[str, float] = {}
            category_counts: dict[str, int] = {}
            for e in engagements:
                if e.created_at < since:
                    continue
                weight = {"like": 1.0, "favorite": 2.0, "bookmark": 1.5}[e.kind]
                asset_scores[e.asset_id] = asset_scores.get(e.asset_id, 0.0) + weight
                if e.asset_owner_user_id:
                    creator_scores[e.asset_owner_user_id] = (
                        creator_scores.get(e.asset_owner_user_id, 0.0) + weight * 0.5
                    )
                if e.asset_category:
                    category_counts[e.asset_category] = (
                        category_counts.get(e.asset_category, 0) + 1
                    )
            for r in store.list_ratings(organization_id=organization_id):
                if r.created_at >= since:
                    asset_scores[r.asset_id] = asset_scores.get(r.asset_id, 0.0) + 1.0

            trending_creators = sorted(
                creator_scores.items(), key=lambda kv: kv[1], reverse=True
            )[:TRENDING_LIMIT]
            trending_assets = sorted(
                asset_scores.items(), key=lambda kv: kv[1], reverse=True
            )[:TRENDING_LIMIT]
            popular_categories = sorted(
                category_counts.items(), key=lambda kv: kv[1], reverse=True
            )[:TRENDING_LIMIT]
            return {
                "ok": True,
                "windowHours": TRENDING_WINDOW_HOURS,
                "trendingCreators": [
                    {"userId": uid, "score": round(s, 2)} for uid, s in trending_creators
                ],
                "trendingAssets": [
                    {"assetId": aid, "score": round(s, 2)} for aid, s in trending_assets
                ],
                "popularCategories": [
                    {"category": c, "count": n} for c, n in popular_categories
                ],
            }

    def discovery(
        self, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            following = {
                e.target_user_id
                for e in store.list_following(organization_id, actor_id)
            }
            candidates = []
            for profile in store.list_profiles(organization_id):
                if profile.user_id == actor_id or profile.user_id in following:
                    continue
                stats = self.profiles.stats(profile)
                candidates.append(
                    {
                        "userId": profile.user_id,
                        "displayName": profile.display_name,
                        "handle": profile.handle,
                        "verified": profile.verified,
                        "reputation": stats["reputation"],
                        "followers": stats["followers"],
                    }
                )
            candidates.sort(key=lambda c: c["reputation"], reverse=True)
            featured = store.get_featured(organization_id)
            return {
                "ok": True,
                "recommendedCreators": candidates[:RECOMMENDED_LIMIT],
                "featuredCreators": featured["creators"],
                "featuredAssets": featured["assets"],
            }

    def set_featured(
        self, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            _, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_manager(actor_id=actor_id, organization_id=org_id)
            creators = [str(c) for c in (payload.get("creators") or [])]
            assets = [str(a) for a in (payload.get("assets") or [])]
            store.set_featured(org_id, creators, assets)
            for uid in creators:
                _notify(
                    organization_id=org_id, recipient=uid,
                    notification_type="featured", actor=actor_id,
                    message="you were featured in the community",
                )
            _audit(
                "community.featured_updated", actor_id,
                f"{len(creators)} creators / {len(assets)} assets",
            )
            return {"ok": True, "featured": store.get_featured(org_id)}

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "community": "ready",
                "userProfile": "ready",
                "followSystem": "ready",
                "ratingReview": "ready",
                "comments": "ready",
                "notifications": "ready",
            },
            "engagementKinds": list(ENGAGEMENT_KINDS),
            "notificationTypes": list(NOTIFICATION_TYPES),
            "spamPolicy": {
                "windowSeconds": SPAM_WINDOW_SECONDS,
                "maxPostsPerWindow": SPAM_MAX_POSTS_PER_WINDOW,
                "duplicateWindowSeconds": SPAM_DUPLICATE_WINDOW_SECONDS,
            },
            "stats": store.metrics(),
        }


_service: CommunityEngine | None = None


def get_community_platform_service() -> CommunityEngine:
    global _service
    if _service is None:
        _service = CommunityEngine()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    _service = None


get_engine = get_community_platform_service
