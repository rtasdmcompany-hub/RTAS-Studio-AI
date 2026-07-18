"""Thread-safe in-memory store for billing & subscriptions."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.billing.models import (
        BillingProfile,
        CreditTransaction,
        CreditWallet,
        Invoice,
        OrganizationSubscription,
        SubscriptionPlan,
        UsageRecord,
        UserSubscription,
    )

_lock = threading.RLock()

_plans: OrderedDict[str, "SubscriptionPlan"] = OrderedDict()
_plans_by_key: dict[str, str] = {}
_org_subs: OrderedDict[str, "OrganizationSubscription"] = OrderedDict()
_org_sub_by_org: dict[str, str] = {}
_user_subs: OrderedDict[str, "UserSubscription"] = OrderedDict()
_wallets: OrderedDict[str, "CreditWallet"] = OrderedDict()
_wallet_by_org: dict[str, str] = {}
_credit_txns: OrderedDict[str, "CreditTransaction"] = OrderedDict()
_usage: OrderedDict[str, "UsageRecord"] = OrderedDict()
_profiles: OrderedDict[str, "BillingProfile"] = OrderedDict()
_profile_by_org: dict[str, str] = {}
_invoices: OrderedDict[str, "Invoice"] = OrderedDict()

_api_timings: list[float] = []
_api_count = 0
_error_count = 0
_seeded = False


def reset_store() -> None:
    global _api_count, _error_count, _seeded
    with _lock:
        _plans.clear()
        _plans_by_key.clear()
        _org_subs.clear()
        _org_sub_by_org.clear()
        _user_subs.clear()
        _wallets.clear()
        _wallet_by_org.clear()
        _credit_txns.clear()
        _usage.clear()
        _profiles.clear()
        _profile_by_org.clear()
        _invoices.clear()
        _api_timings.clear()
        _api_count = 0
        _error_count = 0
        _seeded = False


def is_seeded() -> bool:
    with _lock:
        return _seeded


def mark_seeded() -> None:
    global _seeded
    with _lock:
        _seeded = True


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
            "plans": len(_plans),
            "orgSubscriptions": len(_org_subs),
            "userSubscriptions": len(_user_subs),
            "wallets": len(_wallets),
            "creditTransactions": len(_credit_txns),
            "usageRecords": len(_usage),
            "invoices": len(_invoices),
        }


# --- Plans ---


def save_plan(plan: "SubscriptionPlan") -> None:
    with _lock:
        _plans[plan.id] = plan
        _plans_by_key[plan.key] = plan.id


def get_plan(plan_id: str) -> "SubscriptionPlan | None":
    with _lock:
        return _plans.get(plan_id)


def get_plan_by_key(key: str) -> "SubscriptionPlan | None":
    with _lock:
        pid = _plans_by_key.get(key)
        return _plans.get(pid) if pid else None


def list_plans(*, public_only: bool = True) -> list["SubscriptionPlan"]:
    with _lock:
        items = list(_plans.values())
        if public_only:
            items = [p for p in items if p.is_public and p.status == "active"]
        return items


# --- Org subscriptions ---


def save_org_subscription(sub: "OrganizationSubscription") -> None:
    with _lock:
        _org_subs[sub.id] = sub
        _org_sub_by_org[sub.organization_id] = sub.id


def get_org_subscription(sub_id: str) -> "OrganizationSubscription | None":
    with _lock:
        return _org_subs.get(sub_id)


def get_org_subscription_by_org(organization_id: str) -> "OrganizationSubscription | None":
    with _lock:
        sid = _org_sub_by_org.get(organization_id)
        return _org_subs.get(sid) if sid else None


# --- User subscriptions ---


def save_user_subscription(sub: "UserSubscription") -> None:
    with _lock:
        _user_subs[sub.id] = sub


def list_user_subscriptions(user_id: str) -> list["UserSubscription"]:
    with _lock:
        return [s for s in _user_subs.values() if s.user_id == user_id]


# --- Wallets / credits ---


def save_wallet(wallet: "CreditWallet") -> None:
    with _lock:
        _wallets[wallet.id] = wallet
        if wallet.workspace_id is None:
            _wallet_by_org[wallet.organization_id] = wallet.id


def get_wallet(wallet_id: str) -> "CreditWallet | None":
    with _lock:
        return _wallets.get(wallet_id)


def get_wallet_by_org(organization_id: str) -> "CreditWallet | None":
    with _lock:
        wid = _wallet_by_org.get(organization_id)
        return _wallets.get(wid) if wid else None


def save_credit_txn(txn: "CreditTransaction") -> None:
    with _lock:
        _credit_txns[txn.id] = txn


def list_credit_txns(organization_id: str, *, limit: int = 50) -> list["CreditTransaction"]:
    with _lock:
        items = [t for t in _credit_txns.values() if t.organization_id == organization_id]
        items.sort(key=lambda t: t.created_at, reverse=True)
        return items[:limit]


# --- Usage ---


def save_usage(rec: "UsageRecord") -> None:
    with _lock:
        _usage[rec.id] = rec


def list_usage(
    organization_id: str,
    *,
    workspace_id: str | None = None,
    limit: int = 100,
) -> list["UsageRecord"]:
    with _lock:
        items = [u for u in _usage.values() if u.organization_id == organization_id]
        if workspace_id:
            items = [u for u in items if u.workspace_id == workspace_id]
        items.sort(key=lambda u: u.recorded_at, reverse=True)
        return items[:limit]


# --- Profiles / invoices ---


def save_profile(profile: "BillingProfile") -> None:
    with _lock:
        _profiles[profile.id] = profile
        _profile_by_org[profile.organization_id] = profile.id


def get_profile_by_org(organization_id: str) -> "BillingProfile | None":
    with _lock:
        pid = _profile_by_org.get(organization_id)
        return _profiles.get(pid) if pid else None


def save_invoice(invoice: "Invoice") -> None:
    with _lock:
        _invoices[invoice.id] = invoice


def list_invoices(organization_id: str, *, limit: int = 50) -> list["Invoice"]:
    with _lock:
        items = [i for i in _invoices.values() if i.organization_id == organization_id]
        items.sort(key=lambda i: i.created_at, reverse=True)
        return items[:limit]
