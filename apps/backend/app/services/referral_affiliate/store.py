"""Thread-safe in-memory store for referrals, affiliates, commissions, payouts."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.referral_affiliate.models import (
        Affiliate,
        AffiliateCampaign,
        AffiliateClick,
        AffiliateConversion,
        Commission,
        PayoutHistoryEntry,
        PayoutRequest,
        Referral,
        ReferralCode,
    )

_lock = threading.RLock()

_referral_codes: OrderedDict[str, "ReferralCode"] = OrderedDict()
_code_index: dict[str, str] = {}  # CODE -> referral_code id
_referrals: OrderedDict[str, "Referral"] = OrderedDict()
_affiliates: OrderedDict[str, "Affiliate"] = OrderedDict()
_affiliate_by_user: dict[tuple[str, str], str] = {}  # (org, user) -> affiliate id
_campaigns: OrderedDict[str, "AffiliateCampaign"] = OrderedDict()
_clicks: OrderedDict[str, "AffiliateClick"] = OrderedDict()
_conversions: OrderedDict[str, "AffiliateConversion"] = OrderedDict()
_commissions: OrderedDict[str, "Commission"] = OrderedDict()
_payouts: OrderedDict[str, "PayoutRequest"] = OrderedDict()
_payout_history: OrderedDict[str, "PayoutHistoryEntry"] = OrderedDict()

_api_timings: list[float] = []
_api_count = 0
_error_count = 0


def reset_store() -> None:
    global _api_count, _error_count
    with _lock:
        _referral_codes.clear()
        _code_index.clear()
        _referrals.clear()
        _affiliates.clear()
        _affiliate_by_user.clear()
        _campaigns.clear()
        _clicks.clear()
        _conversions.clear()
        _commissions.clear()
        _payouts.clear()
        _payout_history.clear()
        _api_timings.clear()
        _api_count = 0
        _error_count = 0


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


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


def metrics() -> dict[str, Any]:
    with _lock:
        timings = list(_api_timings)
        avg = sum(timings) / len(timings) if timings else 0.0
        return {
            "apiCount": _api_count,
            "errorCount": _error_count,
            "avgLatencyMs": round(avg, 3),
            "referralCodes": len(_referral_codes),
            "referrals": len(_referrals),
            "affiliates": len(_affiliates),
            "campaigns": len(_campaigns),
            "clicks": len(_clicks),
            "conversions": len(_conversions),
            "commissions": len(_commissions),
            "payoutRequests": len(_payouts),
            "payoutHistory": len(_payout_history),
        }


# --- Referral codes ---


def save_referral_code(rc: "ReferralCode") -> None:
    with _lock:
        _referral_codes[rc.id] = rc
        _code_index[rc.code.upper()] = rc.id


def get_referral_code(code_id: str) -> "ReferralCode | None":
    with _lock:
        return _referral_codes.get(code_id)


def get_referral_code_by_code(code: str) -> "ReferralCode | None":
    with _lock:
        rc_id = _code_index.get((code or "").strip().upper())
        return _referral_codes.get(rc_id) if rc_id else None


def list_referral_codes(
    organization_id: str, *, owner_user_id: str | None = None, limit: int = 100
) -> list["ReferralCode"]:
    with _lock:
        items = [
            rc
            for rc in _referral_codes.values()
            if rc.organization_id == organization_id
            and (owner_user_id is None or rc.owner_user_id == owner_user_id)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Referrals ---


def save_referral(ref: "Referral") -> None:
    with _lock:
        _referrals[ref.id] = ref


def get_referral(referral_id: str) -> "Referral | None":
    with _lock:
        return _referrals.get(referral_id)


def list_referrals(
    organization_id: str,
    *,
    referrer_user_id: str | None = None,
    status: str | None = None,
    limit: int = 200,
) -> list["Referral"]:
    with _lock:
        items = [
            r
            for r in _referrals.values()
            if r.organization_id == organization_id
            and (referrer_user_id is None or r.referrer_user_id == referrer_user_id)
            and (status is None or r.status == status)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def find_referral_by_referred_user(referred_user_id: str) -> "Referral | None":
    with _lock:
        for r in _referrals.values():
            if r.referred_user_id == referred_user_id:
                return r
        return None


# --- Affiliates ---


def save_affiliate(aff: "Affiliate") -> None:
    with _lock:
        _affiliates[aff.id] = aff
        _affiliate_by_user[(aff.organization_id, aff.user_id)] = aff.id


def get_affiliate(affiliate_id: str) -> "Affiliate | None":
    with _lock:
        return _affiliates.get(affiliate_id)


def get_affiliate_by_user(organization_id: str, user_id: str) -> "Affiliate | None":
    with _lock:
        aff_id = _affiliate_by_user.get((organization_id, user_id))
        return _affiliates.get(aff_id) if aff_id else None


def list_affiliates(organization_id: str, *, limit: int = 100) -> list["Affiliate"]:
    with _lock:
        items = [a for a in _affiliates.values() if a.organization_id == organization_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Campaigns / clicks / conversions ---


def save_campaign(c: "AffiliateCampaign") -> None:
    with _lock:
        _campaigns[c.id] = c


def get_campaign(campaign_id: str) -> "AffiliateCampaign | None":
    with _lock:
        return _campaigns.get(campaign_id)


def list_campaigns(affiliate_id: str, *, limit: int = 100) -> list["AffiliateCampaign"]:
    with _lock:
        items = [c for c in _campaigns.values() if c.affiliate_id == affiliate_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def save_click(click: "AffiliateClick") -> None:
    with _lock:
        _clicks[click.id] = click


def count_clicks(affiliate_id: str) -> int:
    with _lock:
        return sum(1 for c in _clicks.values() if c.affiliate_id == affiliate_id)


def save_conversion(conv: "AffiliateConversion") -> None:
    with _lock:
        _conversions[conv.id] = conv


def list_conversions(affiliate_id: str, *, limit: int = 200) -> list["AffiliateConversion"]:
    with _lock:
        items = [c for c in _conversions.values() if c.affiliate_id == affiliate_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Commissions ---


def save_commission(com: "Commission") -> None:
    with _lock:
        _commissions[com.id] = com


def get_commission(commission_id: str) -> "Commission | None":
    with _lock:
        return _commissions.get(commission_id)


def list_commissions(
    *,
    organization_id: str | None = None,
    affiliate_id: str | None = None,
    status: str | None = None,
    limit: int = 200,
) -> list["Commission"]:
    with _lock:
        items = [
            c
            for c in _commissions.values()
            if (organization_id is None or c.organization_id == organization_id)
            and (affiliate_id is None or c.affiliate_id == affiliate_id)
            and (status is None or c.status == status)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Payouts ---


def save_payout(p: "PayoutRequest") -> None:
    with _lock:
        _payouts[p.id] = p


def get_payout(payout_id: str) -> "PayoutRequest | None":
    with _lock:
        return _payouts.get(payout_id)


def list_payouts(
    *,
    organization_id: str | None = None,
    affiliate_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list["PayoutRequest"]:
    with _lock:
        items = [
            p
            for p in _payouts.values()
            if (organization_id is None or p.organization_id == organization_id)
            and (affiliate_id is None or p.affiliate_id == affiliate_id)
            and (status is None or p.status == status)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


def save_payout_history(entry: "PayoutHistoryEntry") -> None:
    with _lock:
        _payout_history[entry.id] = entry


def list_payout_history(
    affiliate_id: str, *, limit: int = 200
) -> list["PayoutHistoryEntry"]:
    with _lock:
        items = [h for h in _payout_history.values() if h.affiliate_id == affiliate_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]
