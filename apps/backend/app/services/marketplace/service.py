"""Enterprise Marketplace, Template Store & Digital Commerce — Phase 8 Sprint 9."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.marketplace import store
from app.services.marketplace.catalog import (
    DEFAULT_CATEGORIES,
    DOWNLOAD_LINK_TTL_MINUTES,
    LICENSE_TYPES,
    MAX_TAGS_PER_PRODUCT,
    PRICING_MODELS,
    PRODUCT_STATUSES,
    PRODUCT_TYPES,
    RATING_MAX,
    RATING_MIN,
    TRENDING_WINDOW_DAYS,
    generate_download_token,
    generate_license_key,
)
from app.services.marketplace.models import (
    AnalyticsEvent,
    DownloadGrant,
    MarketplaceProduct,
    ProductLicense,
    ProductReview,
    ProductVersion,
    Purchase,
    new_id,
)
from app.services.marketplace.version import (
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
        user_id=actor_id,
        organization_id=organization_id,
        permission="org.read",
    )


def _require_manage(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id,
        organization_id=organization_id,
        permission="org.update",
    )


def _record_event(
    product_id: str,
    event_type: str,
    *,
    user_id: str | None = None,
    organization_id: str | None = None,
    amount_credits: float = 0.0,
) -> None:
    store.save_event(
        AnalyticsEvent(
            id=new_id("mev_"),
            product_id=product_id,
            event_type=event_type,
            user_id=user_id,
            organization_id=organization_id,
            amount_credits=amount_credits,
        )
    )


class TemplateStoreEngine:
    """Product lifecycle: publish, update, version, archive, delete."""

    def publish(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            name = str(require_non_empty(payload.get("name"), "name"))
            product_type = str(payload.get("productType") or "custom")
            if product_type not in PRODUCT_TYPES:
                raise ValidationError(f"unknown product type: {product_type}")
            category = str(payload.get("category") or "other")
            if category not in DEFAULT_CATEGORIES:
                raise ValidationError(f"unknown category: {category}")
            pricing_model = str(payload.get("pricingModel") or "free")
            if pricing_model not in PRICING_MODELS:
                raise ValidationError(f"unknown pricing model: {pricing_model}")
            price = float(payload.get("priceCredits") or 0.0)
            if pricing_model == "premium" and price <= 0:
                raise ValidationError("premium products require priceCredits > 0")
            if pricing_model == "free":
                price = 0.0
            license_type = str(payload.get("licenseType") or "personal")
            if license_type not in LICENSE_TYPES:
                raise ValidationError(f"unknown license type: {license_type}")
            tags = [str(t).strip().lower() for t in (payload.get("tags") or []) if str(t).strip()]
            if len(tags) > MAX_TAGS_PER_PRODUCT:
                raise ValidationError(f"maximum {MAX_TAGS_PER_PRODUCT} tags per product")

            product = MarketplaceProduct(
                id=new_id("mkp_"),
                organization_id=org_id,
                seller_user_id=actor_id,
                name=name,
                product_type=product_type,
                description=str(payload.get("description") or ""),
                category=category,
                tags=tags,
                status="published",
                pricing_model=pricing_model,
                price_credits=price,
                license_type=license_type,
                featured=bool(payload.get("featured") or False),
                workspace_id=str(payload["workspaceId"]) if payload.get("workspaceId") else None,
                asset_uri=str(payload.get("assetUri") or f"assets://marketplace/{name}"),
                published_at=_now(),
            )
            store.save_product(product)
            store.save_version(
                ProductVersion(
                    id=new_id("mkv_"),
                    product_id=product.id,
                    version=product.current_version,
                    changelog="initial release",
                    asset_uri=product.asset_uri,
                )
            )
            _audit(
                "marketplace.product.published",
                actor_id,
                name,
                organizationId=org_id,
                productType=product_type,
            )
            return {"ok": True, "product": product.to_dict()}

    def _get_owned(self, product_id: str, actor_id: str) -> MarketplaceProduct:
        ForbiddenError, NotFoundError = _auth_errors()
        product = store.get_product(product_id)
        if product is None or product.status == "deleted":
            raise NotFoundError("product not found")
        if product.seller_user_id != actor_id:
            # Org managers can also manage products of their organization
            _require_manage(actor_id=actor_id, organization_id=product.organization_id)
        else:
            _require_member(actor_id=actor_id, organization_id=product.organization_id)
        return product

    def update(
        self, product_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            product = self._get_owned(product_id, actor_id)
            if product.status == "archived" and payload.get("status") != "published":
                raise ValidationError("unarchive the product before editing")
            if "name" in payload and str(payload["name"]).strip():
                product.name = str(payload["name"]).strip()
            if "description" in payload:
                product.description = str(payload["description"])
            if "category" in payload:
                category = str(payload["category"])
                if category not in DEFAULT_CATEGORIES:
                    raise ValidationError(f"unknown category: {category}")
                product.category = category
            if "tags" in payload:
                tags = [str(t).strip().lower() for t in (payload["tags"] or []) if str(t).strip()]
                if len(tags) > MAX_TAGS_PER_PRODUCT:
                    raise ValidationError(f"maximum {MAX_TAGS_PER_PRODUCT} tags per product")
                product.tags = tags
            if "featured" in payload:
                product.featured = bool(payload["featured"])
            if "pricingModel" in payload:
                pricing_model = str(payload["pricingModel"])
                if pricing_model not in PRICING_MODELS:
                    raise ValidationError(f"unknown pricing model: {pricing_model}")
                product.pricing_model = pricing_model
                if pricing_model == "free":
                    product.price_credits = 0.0
            if "priceCredits" in payload:
                price = float(payload["priceCredits"])
                if product.pricing_model == "premium" and price <= 0:
                    raise ValidationError("premium products require priceCredits > 0")
                product.price_credits = price if product.pricing_model == "premium" else 0.0
            if "status" in payload:
                status = str(payload["status"])
                if status not in ("published", "archived", "draft"):
                    raise ValidationError(f"cannot set status: {status}")
                product.status = status
                product.archived_at = _now() if status == "archived" else None
            if "version" in payload and str(payload["version"]).strip():
                version = str(payload["version"]).strip()
                if version == product.current_version:
                    raise ValidationError("version already exists")
                product.current_version = version
                if "assetUri" in payload and str(payload["assetUri"]).strip():
                    product.asset_uri = str(payload["assetUri"]).strip()
                store.save_version(
                    ProductVersion(
                        id=new_id("mkv_"),
                        product_id=product.id,
                        version=version,
                        changelog=str(payload.get("changelog") or ""),
                        asset_uri=product.asset_uri,
                    )
                )
            product.updated_at = _now()
            store.save_product(product)
            _audit("marketplace.product.updated", actor_id, product.name, productId=product.id)
            return {"ok": True, "product": product.to_dict()}

    def archive(self, product_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            product = self._get_owned(product_id, actor_id)
            product.status = "archived"
            product.archived_at = _now()
            product.updated_at = _now()
            store.save_product(product)
            _audit("marketplace.product.archived", actor_id, product.name, productId=product.id)
            return {"ok": True, "product": product.to_dict()}

    def delete(self, product_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            product = self._get_owned(product_id, actor_id)
            product.status = "deleted"
            product.deleted_at = _now()
            product.updated_at = _now()
            store.save_product(product)
            _audit("marketplace.product.deleted", actor_id, product.name, productId=product.id)
            return {"ok": True, "deleted": True, "productId": product.id}

    def versions(self, product_id: str) -> dict[str, Any]:
        with store.timed_op():
            _, NotFoundError = _auth_errors()
            product = store.get_product(product_id)
            if product is None or product.status == "deleted":
                raise NotFoundError("product not found")
            items = store.list_versions(product_id)
            return {"ok": True, "count": len(items), "versions": [v.to_dict() for v in items]}


class ProductCatalogEngine:
    """Product listing, categories, tags, and detail views."""

    def get(self, product_id: str, *, viewer_id: str | None = None) -> dict[str, Any]:
        with store.timed_op():
            _, NotFoundError = _auth_errors()
            product = store.get_product(product_id)
            if product is None or product.status == "deleted":
                raise NotFoundError("product not found")
            if product.status == "published":
                product.views += 1
                store.save_product(product)
                _record_event(product.id, "view", user_id=viewer_id)
            reviews = store.list_reviews(product_id, limit=10)
            return {
                "ok": True,
                "product": product.to_dict(),
                "recentReviews": [r.to_dict() for r in reviews],
            }

    def list(
        self,
        *,
        organization_id: str | None = None,
        category: str | None = None,
        product_type: str | None = None,
        pricing_model: str | None = None,
        status: str = "published",
        limit: int = 100,
    ) -> dict[str, Any]:
        with store.timed_op():
            items = store.list_products(organization_id=organization_id, status=status)
            if category:
                items = [p for p in items if p.category == category]
            if product_type:
                items = [p for p in items if p.product_type == product_type]
            if pricing_model:
                items = [p for p in items if p.pricing_model == pricing_model]
            items = items[:limit]
            return {
                "ok": True,
                "count": len(items),
                "products": [p.to_dict() for p in items],
            }

    def categories(self) -> dict[str, Any]:
        with store.timed_op():
            published = store.list_products(status="published")
            counts = {c: 0 for c in DEFAULT_CATEGORIES}
            for p in published:
                counts[p.category] = counts.get(p.category, 0) + 1
            return {"ok": True, "categories": counts}

    def tags(self) -> dict[str, Any]:
        with store.timed_op():
            published = store.list_products(status="published")
            counts: dict[str, int] = {}
            for p in published:
                for tag in p.tags:
                    counts[tag] = counts.get(tag, 0) + 1
            return {"ok": True, "tags": counts}


class MarketplaceSearchEngine:
    """Full text, category, tag, and semantic-style scored search + discovery."""

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {t for t in re.split(r"[^a-z0-9]+", text.lower()) if len(t) > 1}

    def search(
        self,
        query: str = "",
        *,
        category: str | None = None,
        tag: str | None = None,
        product_type: str | None = None,
        semantic: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        with store.timed_op():
            published = store.list_products(status="published")
            if category:
                published = [p for p in published if p.category == category]
            if tag:
                published = [p for p in published if tag.lower() in p.tags]
            if product_type:
                published = [p for p in published if p.product_type == product_type]

            query = (query or "").strip()
            if not query:
                ranked = sorted(published, key=lambda p: p.created_at, reverse=True)
                results = [
                    {"score": 0.0, "product": p.to_dict()} for p in ranked[:limit]
                ]
                return {"ok": True, "count": len(results), "results": results}

            q_tokens = self._tokens(query)
            q_lower = query.lower()
            scored: list[tuple[float, MarketplaceProduct]] = []
            for p in published:
                score = 0.0
                name_lower = p.name.lower()
                if q_lower in name_lower:
                    score += 10.0
                name_tokens = self._tokens(p.name)
                desc_tokens = self._tokens(p.description)
                tag_tokens = set(p.tags)
                score += 5.0 * len(q_tokens & name_tokens)
                score += 3.0 * len(q_tokens & tag_tokens)
                score += 1.0 * len(q_tokens & desc_tokens)
                if semantic:
                    # Lightweight semantic proxy: reward popularity and quality
                    # so contextually relevant, proven assets rank higher.
                    if score > 0:
                        score += min(p.purchases, 20) * 0.2
                        score += p.avg_rating * 0.5
                if score > 0:
                    scored.append((score, p))
            scored.sort(key=lambda s: (s[0], s[1].created_at.timestamp()), reverse=True)
            results = [
                {"score": round(score, 3), "product": p.to_dict()}
                for score, p in scored[:limit]
            ]
            return {"ok": True, "count": len(results), "results": results}

    def featured(self, *, limit: int = 20) -> list[dict[str, Any]]:
        published = store.list_products(status="published")
        items = [p for p in published if p.featured]
        items.sort(key=lambda p: p.created_at, reverse=True)
        return [p.to_dict() for p in items[:limit]]

    def trending(self, *, limit: int = 20) -> list[dict[str, Any]]:
        cutoff = _now() - timedelta(days=TRENDING_WINDOW_DAYS)
        recent = [e for e in store.list_events() if e.created_at >= cutoff]
        weights = {"purchase": 5.0, "download": 2.0, "view": 1.0}
        scores: dict[str, float] = {}
        for e in recent:
            w = weights.get(e.event_type, 0.0)
            if w:
                scores[e.product_id] = scores.get(e.product_id, 0.0) + w
        ranked = sorted(scores.items(), key=lambda s: s[1], reverse=True)
        results = []
        for product_id, score in ranked:
            product = store.get_product(product_id)
            if product and product.status == "published":
                data = product.to_dict()
                data["trendScore"] = round(score, 2)
                results.append(data)
            if len(results) >= limit:
                break
        return results

    def new_releases(self, *, limit: int = 20) -> list[dict[str, Any]]:
        published = store.list_products(status="published")
        published.sort(key=lambda p: p.published_at or p.created_at, reverse=True)
        return [p.to_dict() for p in published[:limit]]

    def recommended(self, user_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
        """Recommend published products in categories the user bought from."""
        purchases = store.list_purchases(buyer_user_id=user_id)
        owned_ids = {p.product_id for p in purchases}
        preferred_categories: dict[str, int] = {}
        for purchase in purchases:
            product = store.get_product(purchase.product_id)
            if product:
                preferred_categories[product.category] = (
                    preferred_categories.get(product.category, 0) + 1
                )
        published = [
            p for p in store.list_products(status="published") if p.id not in owned_ids
        ]

        def rank(p: MarketplaceProduct) -> tuple[float, float, float]:
            return (
                float(preferred_categories.get(p.category, 0)),
                p.avg_rating,
                float(p.purchases),
            )

        published.sort(key=rank, reverse=True)
        return [p.to_dict() for p in published[:limit]]

    def discovery(self, user_id: str | None = None) -> dict[str, Any]:
        with store.timed_op():
            return {
                "ok": True,
                "featured": self.featured(),
                "trending": self.trending(),
                "newReleases": self.new_releases(),
                "recommended": self.recommended(user_id) if user_id else [],
            }


class DigitalProductEngine:
    """Purchases, licenses, secure digital delivery, refunds."""

    def purchase(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            ForbiddenError, NotFoundError = _auth_errors()
            product_id = str(require_non_empty(payload.get("productId"), "productId"))
            org_id = require_non_empty(
                payload.get("organizationId") or payload.get("organization_id"),
                "organizationId",
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            product = store.get_product(product_id)
            if product is None or product.status == "deleted":
                raise NotFoundError("product not found")
            if product.status != "published":
                raise ValidationError("product is not available for purchase")
            existing = [
                p
                for p in store.list_purchases(
                    buyer_user_id=actor_id, product_id=product_id
                )
                if p.status == "completed"
            ]
            if existing:
                raise ValidationError("product already purchased")

            license_ = ProductLicense(
                id=new_id("mkl_"),
                product_id=product.id,
                purchase_id="",
                organization_id=org_id,
                holder_user_id=actor_id,
                license_key=generate_license_key(),
                license_type=product.license_type,
                workspace_id=str(payload["workspaceId"]) if payload.get("workspaceId") else None,
            )
            purchase = Purchase(
                id=new_id("mko_"),
                product_id=product.id,
                product_name=product.name,
                buyer_user_id=actor_id,
                organization_id=org_id,
                workspace_id=license_.workspace_id,
                price_credits=product.price_credits,
                license_id=license_.id,
            )
            license_.purchase_id = purchase.id
            store.save_license(license_)
            store.save_purchase(purchase)

            product.purchases += 1
            product.revenue_credits += product.price_credits
            store.save_product(product)
            _record_event(
                product.id,
                "purchase",
                user_id=actor_id,
                organization_id=org_id,
                amount_credits=product.price_credits,
            )
            _audit(
                "marketplace.purchase",
                actor_id,
                product.name,
                organizationId=org_id,
                productId=product.id,
                priceCredits=product.price_credits,
            )
            return {
                "ok": True,
                "purchase": purchase.to_dict(),
                "license": license_.to_dict(),
            }

    def purchases(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            items = store.list_purchases(organization_id=organization_id)
            visible = [
                p
                for p in items
                if p.buyer_user_id == actor_id or self._is_manager(actor_id, organization_id)
            ]
            return {
                "ok": True,
                "count": len(visible),
                "purchases": [p.to_dict() for p in visible],
            }

    @staticmethod
    def _is_manager(actor_id: str, organization_id: str) -> bool:
        try:
            _require_manage(actor_id=actor_id, organization_id=organization_id)
            return True
        except Exception:
            return False

    def validate_license(self, license_key: str) -> dict[str, Any]:
        with store.timed_op():
            license_ = store.get_license_by_key(license_key)
            if license_ is None:
                return {"ok": True, "valid": False, "reason": "license not found"}
            product = store.get_product(license_.product_id)
            valid = (
                license_.status == "active"
                and product is not None
                and product.status != "deleted"
            )
            return {
                "ok": True,
                "valid": valid,
                "reason": "" if valid else f"license is {license_.status}",
                "license": license_.to_dict(),
            }

    def request_download(self, product_id: str, *, actor_id: str) -> dict[str, Any]:
        """Issue a short-lived signed download grant for a licensed buyer."""
        with store.timed_op():
            ForbiddenError, NotFoundError = _auth_errors()
            product = store.get_product(product_id)
            if product is None or product.status == "deleted":
                raise NotFoundError("product not found")
            licenses = [
                l
                for l in store.list_licenses(
                    holder_user_id=actor_id, product_id=product_id
                )
                if l.status == "active"
            ]
            if not licenses and product.seller_user_id != actor_id:
                raise ForbiddenError("no active license for this product")
            license_id = licenses[0].id if licenses else "seller"
            grant = DownloadGrant(
                token=generate_download_token(),
                product_id=product_id,
                license_id=license_id,
                user_id=actor_id,
                expires_at=_now() + timedelta(minutes=DOWNLOAD_LINK_TTL_MINUTES),
            )
            store.save_grant(grant)
            _audit("marketplace.download.requested", actor_id, product.name, productId=product_id)
            return {
                "ok": True,
                "download": {
                    "token": grant.token,
                    "url": f"downloads://marketplace/{product_id}?token={grant.token}",
                    "expiresAt": grant.to_dict()["expiresAt"],
                },
            }

    def redeem_download(self, token: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ForbiddenError, NotFoundError = _auth_errors()
            ValidationError, _ = _validation()
            grant = store.get_grant(token)
            if grant is None:
                raise NotFoundError("download grant not found")
            if grant.user_id != actor_id:
                raise ForbiddenError("download grant belongs to another user")
            if grant.used:
                raise ValidationError("download grant already used")
            if grant.expires_at <= _now():
                raise ValidationError("download grant expired")
            product = store.get_product(grant.product_id)
            if product is None or product.status == "deleted":
                raise NotFoundError("product not found")
            grant.used = True
            store.save_grant(grant)
            product.downloads += 1
            store.save_product(product)
            _record_event(product.id, "download", user_id=actor_id)
            return {
                "ok": True,
                "assetUri": product.asset_uri,
                "version": product.current_version,
                "productId": product.id,
            }

    def refund(self, purchase_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ForbiddenError, NotFoundError = _auth_errors()
            ValidationError, _ = _validation()
            purchase = store.get_purchase(purchase_id)
            if purchase is None:
                raise NotFoundError("purchase not found")
            if purchase.buyer_user_id != actor_id:
                _require_manage(
                    actor_id=actor_id, organization_id=purchase.organization_id
                )
            if purchase.status == "refunded":
                raise ValidationError("purchase already refunded")
            purchase.status = "refunded"
            purchase.refunded_at = _now()
            store.save_purchase(purchase)
            license_ = store.get_license(purchase.license_id)
            if license_ is not None:
                license_.status = "revoked"
                license_.revoked_at = _now()
                store.save_license(license_)
            product = store.get_product(purchase.product_id)
            if product is not None:
                product.refunds += 1
                product.revenue_credits = max(
                    0.0, product.revenue_credits - purchase.price_credits
                )
                store.save_product(product)
                _record_event(
                    product.id,
                    "refund",
                    user_id=actor_id,
                    amount_credits=purchase.price_credits,
                )
            _audit("marketplace.refund", actor_id, purchase.product_name, purchaseId=purchase_id)
            return {
                "ok": True,
                "purchase": purchase.to_dict(),
                "licenseRevoked": license_ is not None,
            }

    def review(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            ForbiddenError, NotFoundError = _auth_errors()
            product_id = str(require_non_empty(payload.get("productId"), "productId"))
            product = store.get_product(product_id)
            if product is None or product.status == "deleted":
                raise NotFoundError("product not found")
            rating = int(payload.get("rating") or 0)
            if not (RATING_MIN <= rating <= RATING_MAX):
                raise ValidationError(
                    f"rating must be between {RATING_MIN} and {RATING_MAX}"
                )
            purchased = [
                p
                for p in store.list_purchases(
                    buyer_user_id=actor_id, product_id=product_id
                )
                if p.status == "completed"
            ]
            if not purchased:
                raise ForbiddenError("only buyers can review a product")
            if store.has_reviewed(product_id, actor_id):
                raise ValidationError("product already reviewed by this user")
            review = ProductReview(
                id=new_id("mkr_"),
                product_id=product_id,
                reviewer_user_id=actor_id,
                organization_id=purchased[0].organization_id,
                rating=rating,
                title=str(payload.get("title") or ""),
                body=str(payload.get("body") or ""),
            )
            store.save_review(review)
            product.rating_sum += rating
            product.rating_count += 1
            store.save_product(product)
            _audit("marketplace.review", actor_id, product.name, rating=rating)
            return {"ok": True, "review": review.to_dict()}


class MarketplaceAnalyticsEngine:
    """Marketplace-wide and per-seller analytics."""

    def analytics(self, *, actor_id: str, organization_id: str) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            products = store.list_products(organization_id=organization_id)
            purchases = store.list_purchases(organization_id=organization_id)
            total_views = sum(p.views for p in products)
            total_downloads = sum(p.downloads for p in products)
            total_purchases = sum(p.purchases for p in products)
            total_refunds = sum(p.refunds for p in products)
            revenue = sum(p.revenue_credits for p in products)
            rated = [p for p in products if p.rating_count > 0]
            avg_rating = (
                sum(p.avg_rating for p in rated) / len(rated) if rated else 0.0
            )
            best_selling = sorted(products, key=lambda p: p.purchases, reverse=True)[:10]
            review_count = sum(p.rating_count for p in products)
            return {
                "ok": True,
                "analytics": {
                    "products": len(products),
                    "views": total_views,
                    "downloads": total_downloads,
                    "purchases": total_purchases,
                    "refunds": total_refunds,
                    "revenueCredits": round(revenue, 2),
                    "spentCredits": round(
                        sum(
                            p.price_credits
                            for p in purchases
                            if p.status == "completed"
                        ),
                        2,
                    ),
                    "avgRating": round(avg_rating, 2),
                    "reviews": review_count,
                },
                "bestSelling": [p.to_dict() for p in best_selling],
            }


class MarketplaceEngine:
    """Facade combining store, catalog, search, commerce, and analytics."""

    def __init__(self) -> None:
        self.templates = TemplateStoreEngine()
        self.catalog = ProductCatalogEngine()
        self.search = MarketplaceSearchEngine()
        self.commerce = DigitalProductEngine()
        self.analytics = MarketplaceAnalyticsEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "marketplace": "ready",
                "templateStore": "ready",
                "digitalProduct": "ready",
                "productCatalog": "ready",
                "marketplaceSearch": "ready",
                "marketplaceAnalytics": "ready",
            },
            "productTypes": list(PRODUCT_TYPES),
            "categories": list(DEFAULT_CATEGORIES),
            "licenseTypes": list(LICENSE_TYPES),
            "stats": store.metrics(),
        }


_service: MarketplaceEngine | None = None


def get_marketplace_service() -> MarketplaceEngine:
    global _service
    if _service is None:
        _service = MarketplaceEngine()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    _service = None


get_engine = get_marketplace_service
