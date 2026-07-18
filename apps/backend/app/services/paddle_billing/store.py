"""Thread-safe in-memory store for Paddle billing integration."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.paddle_billing.models import (
        BillingEvent,
        CheckoutSession,
        PaddleCustomer,
        PaddleSubscription,
        PaddleTransaction,
        PaddleWebhookLog,
    )

_lock = threading.RLock()

_customers: OrderedDict[str, "PaddleCustomer"] = OrderedDict()
_customer_by_org: dict[str, str] = {}
_customer_by_paddle: dict[str, str] = {}
_subscriptions: OrderedDict[str, "PaddleSubscription"] = OrderedDict()
_sub_by_org: dict[str, str] = {}
_sub_by_paddle: dict[str, str] = {}
_transactions: OrderedDict[str, "PaddleTransaction"] = OrderedDict()
_webhooks: OrderedDict[str, "PaddleWebhookLog"] = OrderedDict()
_events: OrderedDict[str, "BillingEvent"] = OrderedDict()
_checkouts: OrderedDict[str, "CheckoutSession"] = OrderedDict()
_processed_event_ids: set[str] = set()

_api_timings: list[float] = []
_api_count = 0
_error_count = 0


def reset_store() -> None:
    global _api_count, _error_count
    with _lock:
        _customers.clear()
        _customer_by_org.clear()
        _customer_by_paddle.clear()
        _subscriptions.clear()
        _sub_by_org.clear()
        _sub_by_paddle.clear()
        _transactions.clear()
        _webhooks.clear()
        _events.clear()
        _checkouts.clear()
        _processed_event_ids.clear()
        _api_timings.clear()
        _api_count = 0
        _error_count = 0


@contextmanager
def timed_op() -> Iterator[None]:
    global _api_count
    start = time.perf_counter()
    try:
        yield
    except Exception:
        record_error()
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        with _lock:
            _api_timings.append(ms)
            if len(_api_timings) > 500:
                del _api_timings[: len(_api_timings) - 500]
            _api_count += 1


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


def metrics() -> dict[str, Any]:
    with _lock:
        avg = sum(_api_timings) / len(_api_timings) if _api_timings else 0.0
        return {
            "apiCalls": _api_count,
            "avgLatencyMs": round(avg, 2),
            "errors": _error_count,
            "customers": len(_customers),
            "subscriptions": len(_subscriptions),
            "transactions": len(_transactions),
            "webhooks": len(_webhooks),
            "billingEvents": len(_events),
            "checkouts": len(_checkouts),
        }


def save_customer(c: "PaddleCustomer") -> None:
    with _lock:
        _customers[c.id] = c
        _customer_by_org[c.organization_id] = c.id
        _customer_by_paddle[c.paddle_customer_id] = c.id


def get_customer_by_org(organization_id: str) -> "PaddleCustomer | None":
    with _lock:
        cid = _customer_by_org.get(organization_id)
        return _customers.get(cid) if cid else None


def get_customer_by_paddle(paddle_customer_id: str) -> "PaddleCustomer | None":
    with _lock:
        cid = _customer_by_paddle.get(paddle_customer_id)
        return _customers.get(cid) if cid else None


def save_subscription(s: "PaddleSubscription") -> None:
    with _lock:
        _subscriptions[s.id] = s
        _sub_by_org[s.organization_id] = s.id
        _sub_by_paddle[s.paddle_subscription_id] = s.id


def get_subscription_by_org(organization_id: str) -> "PaddleSubscription | None":
    with _lock:
        sid = _sub_by_org.get(organization_id)
        return _subscriptions.get(sid) if sid else None


def get_subscription_by_paddle(paddle_sub_id: str) -> "PaddleSubscription | None":
    with _lock:
        sid = _sub_by_paddle.get(paddle_sub_id)
        return _subscriptions.get(sid) if sid else None


def save_transaction(t: "PaddleTransaction") -> None:
    with _lock:
        _transactions[t.id] = t


def save_webhook(w: "PaddleWebhookLog") -> None:
    with _lock:
        _webhooks[w.id] = w


def mark_event_processed(event_id: str) -> bool:
    """Return True if first time seen."""
    with _lock:
        if event_id in _processed_event_ids:
            return False
        _processed_event_ids.add(event_id)
        return True


def save_event(e: "BillingEvent") -> None:
    with _lock:
        _events[e.id] = e


def list_events(organization_id: str, *, limit: int = 50) -> list["BillingEvent"]:
    with _lock:
        items = [e for e in _events.values() if e.organization_id == organization_id]
        items.sort(key=lambda e: e.created_at, reverse=True)
        return items[:limit]


def save_checkout(c: "CheckoutSession") -> None:
    with _lock:
        _checkouts[c.id] = c


def get_checkout(checkout_id: str) -> "CheckoutSession | None":
    with _lock:
        return _checkouts.get(checkout_id)
