"""Thread-safe in-memory store for the template store & asset management engine."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.template_store.models import (
        AssetCollectionRecord,
        AssetLibrary,
        Template,
        TemplateVersion,
    )

_lock = threading.RLock()

_templates: OrderedDict[str, "Template"] = OrderedDict()
_versions: OrderedDict[str, "TemplateVersion"] = OrderedDict()
_libraries: OrderedDict[str, "AssetLibrary"] = OrderedDict()
_collections: OrderedDict[str, "AssetCollectionRecord"] = OrderedDict()
_categories: dict[str, str] = {}  # slug -> label
_tag_counts: dict[str, int] = {}
_search_index: dict[str, set[str]] = {}  # template_id -> tokens
_ratings: dict[tuple[str, str], int] = {}  # (template_id, user_id) -> value

_op_timings: list[float] = []
_op_count = 0
_error_count = 0


def reset_store() -> None:
    global _op_count, _error_count
    with _lock:
        for coll in (
            _templates, _versions, _libraries, _collections,
            _categories, _tag_counts, _search_index, _ratings,
        ):
            coll.clear()
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
            "templates": len(_templates),
            "versions": len(_versions),
            "libraries": len(_libraries),
            "collections": len(_collections),
            "categories": len(_categories),
            "tags": len(_tag_counts),
            "indexedTemplates": len(_search_index),
        }


# --- Templates ---


def save_template(template: "Template") -> None:
    with _lock:
        _templates[template.id] = template


def get_template(template_id: str) -> "Template | None":
    with _lock:
        return _templates.get(template_id)


def list_templates(
    *,
    organization_id: str | None = None,
    owner: str | None = None,
    status: str | None = None,
    include_deleted: bool = False,
) -> list["Template"]:
    with _lock:
        return [
            t
            for t in _templates.values()
            if (organization_id is None or t.organization_id == organization_id)
            and (owner is None or t.owner_user_id == owner)
            and (status is None or t.status == status)
            and (include_deleted or t.status != "deleted")
        ]


# --- Versions ---


def save_version(version: "TemplateVersion") -> None:
    with _lock:
        _versions[version.id] = version


def list_versions(template_id: str) -> list["TemplateVersion"]:
    with _lock:
        items = [v for v in _versions.values() if v.template_id == template_id]
        items.sort(key=lambda x: x.created_at)
        return items


def get_version(template_id: str, version: str) -> "TemplateVersion | None":
    with _lock:
        for v in _versions.values():
            if v.template_id == template_id and v.version == version:
                return v
        return None


# --- Libraries & collections ---


def save_library(library: "AssetLibrary") -> None:
    with _lock:
        _libraries[library.id] = library


def get_library(library_id: str) -> "AssetLibrary | None":
    with _lock:
        return _libraries.get(library_id)


def list_libraries(organization_id: str) -> list["AssetLibrary"]:
    with _lock:
        return [
            l for l in _libraries.values() if l.organization_id == organization_id
        ]


def save_collection(collection: "AssetCollectionRecord") -> None:
    with _lock:
        _collections[collection.id] = collection


def get_collection(collection_id: str) -> "AssetCollectionRecord | None":
    with _lock:
        return _collections.get(collection_id)


def list_collections(organization_id: str) -> list["AssetCollectionRecord"]:
    with _lock:
        return [
            c for c in _collections.values() if c.organization_id == organization_id
        ]


# --- Categories & tags ---


def upsert_category(slug: str, label: str) -> None:
    with _lock:
        _categories[slug] = label


def remove_category(slug: str) -> bool:
    with _lock:
        return _categories.pop(slug, None) is not None


def list_categories() -> dict[str, str]:
    with _lock:
        return dict(_categories)


def has_category(slug: str) -> bool:
    with _lock:
        return slug in _categories


def bump_tag(slug: str, delta: int = 1) -> None:
    with _lock:
        count = _tag_counts.get(slug, 0) + delta
        if count <= 0:
            _tag_counts.pop(slug, None)
        else:
            _tag_counts[slug] = count


def list_tags() -> dict[str, int]:
    with _lock:
        return dict(_tag_counts)


# --- Search index ---


def index_template(template_id: str, tokens: set[str]) -> None:
    with _lock:
        _search_index[template_id] = set(tokens)


def unindex_template(template_id: str) -> None:
    with _lock:
        _search_index.pop(template_id, None)


def search_tokens(template_id: str) -> set[str]:
    with _lock:
        return set(_search_index.get(template_id) or set())


# --- Ratings ---


def save_rating(template_id: str, user_id: str, value: int) -> bool:
    """Record a rating; returns False when the user already rated."""
    with _lock:
        key = (template_id, user_id)
        if key in _ratings:
            return False
        _ratings[key] = value
        return True
