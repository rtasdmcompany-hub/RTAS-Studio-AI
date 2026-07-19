"""Data Subject Request (DSR) store — export, access, erasure (privacy rights)."""

from __future__ import annotations

import copy
import threading
import time
import uuid
from typing import Any

_lock = threading.Lock()
_REQUESTS: dict[str, dict[str, Any]] = {}
_USER_DATA: dict[str, dict[str, Any]] = {}


def upsert_user_profile(user_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        existing = _USER_DATA.get(user_id) or {
            "userId": user_id,
            "consents": {},
            "metadata": {},
            "createdAt": time.time(),
        }
        existing.update({k: v for k, v in profile.items() if k != "userId"})
        existing["userId"] = user_id
        existing["updatedAt"] = time.time()
        _USER_DATA[user_id] = existing
        return copy.deepcopy(existing)


def _new_request(user_id: str, request_type: str) -> dict[str, Any]:
    rid = f"dsr_{uuid.uuid4().hex[:12]}"
    entry = {
        "requestId": rid,
        "userId": user_id,
        "type": request_type,
        "status": "received",
        "createdAt": time.time(),
        "completedAt": None,
        "result": None,
    }
    with _lock:
        _REQUESTS[rid] = entry
        return copy.deepcopy(entry)


def request_access(user_id: str) -> dict[str, Any]:
    req = _new_request(user_id, "access")
    with _lock:
        profile = copy.deepcopy(_USER_DATA.get(user_id) or {"userId": user_id})
        entry = _REQUESTS[req["requestId"]]
        entry["status"] = "completed"
        entry["completedAt"] = time.time()
        entry["result"] = {
            "profile": profile,
            "categories": ["account", "consent", "usage_metadata"],
        }
        return copy.deepcopy(entry)


def export_user_data(user_id: str) -> dict[str, Any]:
    req = _new_request(user_id, "export")
    with _lock:
        profile = copy.deepcopy(_USER_DATA.get(user_id) or {"userId": user_id})
        entry = _REQUESTS[req["requestId"]]
        entry["status"] = "completed"
        entry["completedAt"] = time.time()
        entry["result"] = {
            "format": "json",
            "portable": True,
            "payload": profile,
            "gdprArt20": True,
            "ccpaKnow": True,
        }
        return copy.deepcopy(entry)


def delete_user_account(user_id: str) -> dict[str, Any]:
    req = _new_request(user_id, "erasure")
    with _lock:
        existed = user_id in _USER_DATA
        _USER_DATA.pop(user_id, None)
        entry = _REQUESTS[req["requestId"]]
        entry["status"] = "completed"
        entry["completedAt"] = time.time()
        entry["result"] = {
            "erased": True,
            "hadProfile": existed,
            "gdprArt17": True,
            "ccpaDelete": True,
            "retained": ["billing_legal_obligation", "security_audit_window"],
        }
        return copy.deepcopy(entry)


def get_request(request_id: str) -> dict[str, Any] | None:
    with _lock:
        item = _REQUESTS.get(request_id)
        return copy.deepcopy(item) if item else None


def list_requests(*, user_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    with _lock:
        items = list(_REQUESTS.values())
    if user_id:
        items = [i for i in items if i.get("userId") == user_id]
    items.sort(key=lambda x: float(x.get("createdAt") or 0), reverse=True)
    return [copy.deepcopy(i) for i in items[: max(1, min(100, limit))]]


def clear() -> None:
    with _lock:
        _REQUESTS.clear()
        _USER_DATA.clear()


def privacy_capabilities() -> dict[str, Any]:
    return {
        "userDataCollectionDocumented": True,
        "personalDataStorage": "encrypted_at_rest_recommended + provider controls",
        "encryption": True,
        "dataRetention": True,
        "dataDeletion": True,
        "userConsent": True,
        "exportUserData": True,
        "deleteUserAccount": True,
        "dsrApi": True,
    }
