"""Thread-safe in-memory store for marketplace products, purchases, and reviews."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.marketplace.models import (
        AnalyticsEvent,
        DownloadGrant,
        MarketplaceProduct,
        ProductLicense,
        ProductReview,
        ProductVersion,
        Purchase,
    )

_lock = threading.RLock()

_products: OrderedDict[str, "MarketplaceProduct"] = OrderedDict()
_versions: OrderedDict[str, "ProductVersion"] = OrderedDict()
_purchases: OrderedDict[str, "Purchase"] = OrderedDict()
_licenses: OrderedDict[str, "ProductLicense"] = OrderedDict()
_license_by_key: dict[str, str] = {}
_download_grants: dict[str, "DownloadGrant"] = {}
_reviews: OrderedDict[str, "ProductReview"] = OrderedDict()
_events: OrderedDict[str, "AnalyticsEvent"] = OrderedDict()

_op_timings: list[float] = []
_op_count = 0
_error_count = 0


def reset_store() -> None:
    global _op_count, _error_count
    with _lock:
        _products.clear()
        _versions.clear()
        _purchases.clear()
        _licenses.clear()
        _license_by_key.clear()
        _download_grants.clear()
        _reviews.clear()
        _events.clear()
        _op_timings.clear()
        _op_count = 0
        _error_count = 0


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


@contextmanager
def timed_op() -> Iterator[None]:
    global _op_count
    start = time.perf_counter()
    try:
        yield
    except Exception:
        record_error()
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        with _lock:
            _op_timings.append(ms)
            if len(_op_timings) > 500:
                del _op_timings[: len(_op_timings) - 500]
            _op_count += 1


def metrics() -> dict[str, Any]:
    with _lock:
        timings = list(_op_timings)
        avg = sum(timings) / len(timings) if timings else 0.0
        return {
            "opCount": _op_count,
            "errorCount": _error_count,
            "avgLatencyMs": round(avg, 3),
            "products": len(_products),
            "versions": len(_versions),
            "purchases": len(_purchases),
            "licenses": len(_licenses),
            "downloadGrants": len(_download_grants),
            "reviews": len(_reviews),
            "analyticsEvents": len(_events),
        }


# --- Products ---


def save_product(product: "MarketplaceProduct") -> None:
    with _lock:
        _products[product.id] = product


def get_product(product_id: str) -> "MarketplaceProduct | None":
    with _lock:
        return _products.get(product_id)


def list_products(
    *,
    organization_id: str | None = None,
    status: str | None = None,
    include_deleted: bool = False,
    limit: int = 10_000,
) -> list["MarketplaceProduct"]:
    with _lock:
        items = [
            p
            for p in _products.values()
            if (organization_id is None or p.organization_id == organization_id)
            and (status is None or p.status == status)
            and (include_deleted or p.status != "deleted")
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Versions ---


def save_version(version: "ProductVersion") -> None:
    with _lock:
        _versions[version.id] = version


def list_versions(product_id: str) -> list["ProductVersion"]:
    with _lock:
        items = [v for v in _versions.values() if v.product_id == product_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items


# --- Purchases ---


def save_purchase(purchase: "Purchase") -> None:
    with _lock:
        _purchases[purchase.id] = purchase


def get_purchase(purchase_id: str) -> "Purchase | None":
    with _lock:
        return _purchases.get(purchase_id)


def list_purchases(
    *,
    organization_id: str | None = None,
    buyer_user_id: str | None = None,
    product_id: str | None = None,
    limit: int = 1000,
) -> list["Purchase"]:
    with _lock:
        items = [
            p
            for p in _purchases.values()
            if (organization_id is None or p.organization_id == organization_id)
            and (buyer_user_id is None or p.buyer_user_id == buyer_user_id)
            and (product_id is None or p.product_id == product_id)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Licenses ---


def save_license(license_: "ProductLicense") -> None:
    with _lock:
        _licenses[license_.id] = license_
        _license_by_key[license_.license_key] = license_.id


def get_license(license_id: str) -> "ProductLicense | None":
    with _lock:
        return _licenses.get(license_id)


def get_license_by_key(license_key: str) -> "ProductLicense | None":
    with _lock:
        lid = _license_by_key.get((license_key or "").strip().upper())
        return _licenses.get(lid) if lid else None


def list_licenses(
    *,
    organization_id: str | None = None,
    holder_user_id: str | None = None,
    product_id: str | None = None,
) -> list["ProductLicense"]:
    with _lock:
        items = [
            l
            for l in _licenses.values()
            if (organization_id is None or l.organization_id == organization_id)
            and (holder_user_id is None or l.holder_user_id == holder_user_id)
            and (product_id is None or l.product_id == product_id)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items


# --- Download grants ---


def save_grant(grant: "DownloadGrant") -> None:
    with _lock:
        _download_grants[grant.token] = grant


def get_grant(token: str) -> "DownloadGrant | None":
    with _lock:
        return _download_grants.get(token)


# --- Reviews ---


def save_review(review: "ProductReview") -> None:
    with _lock:
        _reviews[review.id] = review


def list_reviews(product_id: str, *, limit: int = 200) -> list["ProductReview"]:
    with _lock:
        items = [r for r in _reviews.values() if r.product_id == product_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def has_reviewed(product_id: str, user_id: str) -> bool:
    with _lock:
        return any(
            r.product_id == product_id and r.reviewer_user_id == user_id
            for r in _reviews.values()
        )


# --- Analytics events ---


def save_event(event: "AnalyticsEvent") -> None:
    with _lock:
        _events[event.id] = event
        if len(_events) > 100_000:
            _events.popitem(last=False)


def list_events(
    *,
    product_id: str | None = None,
    event_type: str | None = None,
    limit: int = 100_000,
) -> list["AnalyticsEvent"]:
    with _lock:
        items = [
            e
            for e in _events.values()
            if (product_id is None or e.product_id == product_id)
            and (event_type is None or e.event_type == event_type)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]
