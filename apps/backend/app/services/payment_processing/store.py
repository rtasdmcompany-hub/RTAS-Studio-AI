"""Thread-safe in-memory store for payment processing & wallets."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.payment_processing.models import (
        PaymentHistoryEntry,
        PayPalPayment,
        RefundHistoryEntry,
        RefundRequest,
        WalletAccount,
        WalletTransaction,
    )

_lock = threading.RLock()

_wallets: OrderedDict[str, "WalletAccount"] = OrderedDict()
_wallet_by_org: dict[str, str] = {}
_txns: OrderedDict[str, "WalletTransaction"] = OrderedDict()
_payments: OrderedDict[str, "PayPalPayment"] = OrderedDict()
_payment_by_order: dict[str, str] = {}
_payment_history: OrderedDict[str, "PaymentHistoryEntry"] = OrderedDict()
_refunds: OrderedDict[str, "RefundRequest"] = OrderedDict()
_refund_history: OrderedDict[str, "RefundHistoryEntry"] = OrderedDict()
_processed_events: set[str] = set()

_api_timings: list[float] = []
_api_count = 0
_error_count = 0


def reset_store() -> None:
    global _api_count, _error_count
    with _lock:
        _wallets.clear()
        _wallet_by_org.clear()
        _txns.clear()
        _payments.clear()
        _payment_by_order.clear()
        _payment_history.clear()
        _refunds.clear()
        _refund_history.clear()
        _processed_events.clear()
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
            "wallets": len(_wallets),
            "transactions": len(_txns),
            "paypalPayments": len(_payments),
            "refundRequests": len(_refunds),
        }


def save_wallet(w: "WalletAccount") -> None:
    with _lock:
        _wallets[w.id] = w
        _wallet_by_org[w.organization_id] = w.id


def get_wallet_by_org(organization_id: str) -> "WalletAccount | None":
    with _lock:
        wid = _wallet_by_org.get(organization_id)
        return _wallets.get(wid) if wid else None


def save_txn(t: "WalletTransaction") -> None:
    with _lock:
        _txns[t.id] = t


def list_txns(organization_id: str, *, limit: int = 100) -> list["WalletTransaction"]:
    with _lock:
        items = [t for t in _txns.values() if t.organization_id == organization_id]
        items.sort(key=lambda t: t.created_at, reverse=True)
        return items[:limit]


def save_payment(p: "PayPalPayment") -> None:
    with _lock:
        _payments[p.id] = p
        _payment_by_order[p.paypal_order_id] = p.id


def get_payment(payment_id: str) -> "PayPalPayment | None":
    with _lock:
        return _payments.get(payment_id)


def get_payment_by_order(order_id: str) -> "PayPalPayment | None":
    with _lock:
        pid = _payment_by_order.get(order_id)
        return _payments.get(pid) if pid else None


def save_payment_history(h: "PaymentHistoryEntry") -> None:
    with _lock:
        _payment_history[h.id] = h


def list_payment_history(
    organization_id: str, *, limit: int = 100
) -> list["PaymentHistoryEntry"]:
    with _lock:
        items = [
            h for h in _payment_history.values() if h.organization_id == organization_id
        ]
        items.sort(key=lambda h: h.created_at, reverse=True)
        return items[:limit]


def save_refund(r: "RefundRequest") -> None:
    with _lock:
        _refunds[r.id] = r


def get_refund(refund_id: str) -> "RefundRequest | None":
    with _lock:
        return _refunds.get(refund_id)


def save_refund_history(h: "RefundHistoryEntry") -> None:
    with _lock:
        _refund_history[h.id] = h


def mark_event(event_id: str) -> bool:
    with _lock:
        if event_id in _processed_events:
            return False
        _processed_events.add(event_id)
        return True
