"""Generation queue for Image-to-Video requests."""

from __future__ import annotations

import threading
from collections import OrderedDict, deque
from typing import Any

from app.services.image_to_video.models import I2VProviderRequest, RequestState

_lock = threading.Lock()
_queue: deque[str] = deque()
_requests: OrderedDict[str, I2VProviderRequest] = OrderedDict()
_MAX = 2000


class ImageToVideoQueue:
    def enqueue(self, request: I2VProviderRequest) -> I2VProviderRequest:
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
        self, requests: list[I2VProviderRequest]
    ) -> list[I2VProviderRequest]:
        return [self.enqueue(r) for r in requests]

    def dequeue(self) -> I2VProviderRequest | None:
        with _lock:
            while _queue:
                rid = _queue.popleft()
                req = _requests.get(rid)
                if req and req.state in ("queued", "retrying"):
                    req.state = "running"
                    return req
            return None

    def peek(self, limit: int = 20) -> list[I2VProviderRequest]:
        with _lock:
            out = []
            for rid in list(_queue)[:limit]:
                req = _requests.get(rid)
                if req:
                    out.append(I2VProviderRequest(**req.to_dict()))
            return out

    def get(self, request_id: str) -> I2VProviderRequest | None:
        with _lock:
            req = _requests.get(request_id)
            return I2VProviderRequest(**req.to_dict()) if req else None

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
    ) -> I2VProviderRequest | None:
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
            return I2VProviderRequest(**req.to_dict())

    def requeue(self, request_id: str) -> I2VProviderRequest | None:
        with _lock:
            req = _requests.get(request_id)
            if not req:
                return None
            req.state = "retrying"
            _queue.append(request_id)
            return I2VProviderRequest(**req.to_dict())

    def list_by_job(self, job_id: str) -> list[I2VProviderRequest]:
        with _lock:
            return [
                I2VProviderRequest(**r.to_dict())
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


i2v_queue = ImageToVideoQueue()
