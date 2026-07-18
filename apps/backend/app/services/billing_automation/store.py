"""Thread-safe in-memory store for billing automation."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.billing_automation.models import (
        AutomationBillingEvent,
        Coupon,
        CouponUsage,
        DiscountRecord,
        InvoiceItem,
        InvoiceRecord,
        PaymentRetry,
        TaxRecord,
    )

_lock = threading.RLock()

_invoices: OrderedDict[str, "InvoiceRecord"] = OrderedDict()
_invoice_by_number: dict[str, str] = {}
_items: OrderedDict[str, "InvoiceItem"] = OrderedDict()
_tax_records: OrderedDict[str, "TaxRecord"] = OrderedDict()
_coupons: OrderedDict[str, "Coupon"] = OrderedDict()
_coupon_by_code: dict[str, str] = {}
_coupon_usage: OrderedDict[str, "CouponUsage"] = OrderedDict()
_discounts: OrderedDict[str, "DiscountRecord"] = OrderedDict()
_events: OrderedDict[str, "AutomationBillingEvent"] = OrderedDict()
_retries: OrderedDict[str, "PaymentRetry"] = OrderedDict()
_tax_exemptions: dict[str, str] = {}  # org_id -> reason
_invoice_seq = 0

_api_timings: list[float] = []
_api_count = 0
_error_count = 0


def reset_store() -> None:
    global _api_count, _error_count, _invoice_seq
    with _lock:
        _invoices.clear()
        _invoice_by_number.clear()
        _items.clear()
        _tax_records.clear()
        _coupons.clear()
        _coupon_by_code.clear()
        _coupon_usage.clear()
        _discounts.clear()
        _events.clear()
        _retries.clear()
        _tax_exemptions.clear()
        _invoice_seq = 0
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


def metrics_snapshot() -> dict[str, Any]:
    with _lock:
        timings = list(_api_timings)
        avg = sum(timings) / len(timings) if timings else 0.0
        return {
            "apiCount": _api_count,
            "errorCount": _error_count,
            "avgLatencyMs": round(avg, 3),
            "invoices": len(_invoices),
            "coupons": len(_coupons),
            "retries": len(_retries),
            "events": len(_events),
        }


def next_invoice_seq() -> int:
    global _invoice_seq
    with _lock:
        _invoice_seq += 1
        return _invoice_seq


def save_invoice(inv: "InvoiceRecord") -> None:
    with _lock:
        _invoices[inv.id] = inv
        _invoice_by_number[inv.invoice_number] = inv.id


def get_invoice(invoice_id: str) -> "InvoiceRecord | None":
    with _lock:
        return _invoices.get(invoice_id)


def list_invoices(organization_id: str, *, limit: int = 100) -> list["InvoiceRecord"]:
    with _lock:
        items = [i for i in _invoices.values() if i.organization_id == organization_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def save_item(item: "InvoiceItem") -> None:
    with _lock:
        _items[item.id] = item


def list_items(invoice_id: str) -> list["InvoiceItem"]:
    with _lock:
        return [i for i in _items.values() if i.invoice_id == invoice_id]


def save_tax(record: "TaxRecord") -> None:
    with _lock:
        _tax_records[record.id] = record


def list_tax(organization_id: str, *, limit: int = 100) -> list["TaxRecord"]:
    with _lock:
        items = [t for t in _tax_records.values() if t.organization_id == organization_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def set_exemption(organization_id: str, reason: str) -> None:
    with _lock:
        _tax_exemptions[organization_id] = reason


def get_exemption(organization_id: str) -> str | None:
    with _lock:
        return _tax_exemptions.get(organization_id)


def clear_exemption(organization_id: str) -> None:
    with _lock:
        _tax_exemptions.pop(organization_id, None)


def save_coupon(coupon: "Coupon") -> None:
    with _lock:
        _coupons[coupon.id] = coupon
        _coupon_by_code[coupon.code.upper()] = coupon.id


def get_coupon_by_code(code: str) -> "Coupon | None":
    with _lock:
        cid = _coupon_by_code.get(code.strip().upper())
        return _coupons.get(cid) if cid else None


def list_coupons() -> list["Coupon"]:
    with _lock:
        return list(_coupons.values())


def save_coupon_usage(usage: "CouponUsage") -> None:
    with _lock:
        _coupon_usage[usage.id] = usage


def list_coupon_usage(
    organization_id: str, *, coupon_code: str | None = None
) -> list["CouponUsage"]:
    with _lock:
        items = [
            u
            for u in _coupon_usage.values()
            if u.organization_id == organization_id
            and (coupon_code is None or u.coupon_code.upper() == coupon_code.upper())
        ]
        return items


def save_discount(discount: "DiscountRecord") -> None:
    with _lock:
        _discounts[discount.id] = discount


def save_event(event: "AutomationBillingEvent") -> None:
    with _lock:
        _events[event.id] = event


def list_events(organization_id: str, *, limit: int = 100) -> list["AutomationBillingEvent"]:
    with _lock:
        items = [e for e in _events.values() if e.organization_id == organization_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def save_retry(retry: "PaymentRetry") -> None:
    with _lock:
        _retries[retry.id] = retry


def get_retry(retry_id: str) -> "PaymentRetry | None":
    with _lock:
        return _retries.get(retry_id)


def get_retry_by_invoice(invoice_id: str) -> "PaymentRetry | None":
    with _lock:
        for r in _retries.values():
            if r.invoice_id == invoice_id and r.status in {
                "scheduled",
                "processing",
                "failed",
            }:
                return r
        return None


def list_retries(organization_id: str) -> list["PaymentRetry"]:
    with _lock:
        return [r for r in _retries.values() if r.organization_id == organization_id]
