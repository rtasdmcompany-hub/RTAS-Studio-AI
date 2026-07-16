"""Generation queue for Text-to-Video scene/shot requests."""

from __future__ import annotations

import threading
from collections import OrderedDict, deque
from typing import Any

from app.services.text_to_video.models import ProviderGenerationRequest, RequestState

_lock = threading.Lock()
_queue: deque[str] = deque()
_requests: OrderedDict[str, ProviderGenerationRequest] = OrderedDict()
_MAX = 2000


class TextToVideoQueue:
    """Thread-safe in-memory queue of provider generation requests."""

    def enqueue(self, request: ProviderGenerationRequest) -> ProviderGenerationRequest:
        with _lock:
            request.state = "queued"
            _requests[request.request_id] = request
            _queue.append(request.request_id)
            while len(_requests) > _MAX:
                old_id, _ = _requests.popitem(last=False)
                try:
                    _queue.remove(old_id)
                except ValueError:
                    pass
            return request

    def enqueue_many(
        self, requests: list[ProviderGenerationRequest]
    ) -> list[ProviderGenerationRequest]:
        return [self.enqueue(r) for r in requests]

    def dequeue(self) -> ProviderGenerationRequest | None:
        with _lock:
            while _queue:
                rid = _queue.popleft()
                req = _requests.get(rid)
                if req and req.state in ("queued", "retrying"):
                    req.state = "running"
                    return req
            return None

    def peek(self, limit: int = 20) -> list[ProviderGenerationRequest]:
        with _lock:
            out = []
            for rid in list(_queue)[:limit]:
                req = _requests.get(rid)
                if req:
                    out.append(ProviderGenerationRequest(**req.to_dict()))
            return out

    def get(self, request_id: str) -> ProviderGenerationRequest | None:
        with _lock:
            req = _requests.get(request_id)
            return ProviderGenerationRequest(**req.to_dict()) if req else None

    def update(
        self,
        request_id: str,
        *,
        state: RequestState | None = None,
        error: str | None = None,
        result_url: str | None = None,
        external_job_id: str | None = None,
        attempts: int | None = None,
        **metadata: Any,
    ) -> ProviderGenerationRequest | None:
        with _lock:
            req = _requests.get(request_id)
            if not req:
                return None
            if state is not None:
                req.state = state
            if error is not None:
                req.error = error
            if result_url is not None:
                req.result_url = result_url
            if external_job_id is not None:
                req.external_job_id = external_job_id
            if attempts is not None:
                req.attempts = attempts
            if metadata:
                req.metadata.update(metadata)
            return ProviderGenerationRequest(**req.to_dict())

    def requeue(self, request_id: str) -> ProviderGenerationRequest | None:
        with _lock:
            req = _requests.get(request_id)
            if not req:
                return None
            req.state = "retrying"
            _queue.append(request_id)
            return ProviderGenerationRequest(**req.to_dict())

    def list_by_job(self, job_id: str) -> list[ProviderGenerationRequest]:
        with _lock:
            return [
                ProviderGenerationRequest(**r.to_dict())
                for r in _requests.values()
                if r.job_id == job_id
            ]

    def size(self) -> int:
        with _lock:
            return len(_queue)

    def clear(self) -> None:
        with _lock:
            _queue.clear()
            _requests.clear()


t2v_queue = TextToVideoQueue()
