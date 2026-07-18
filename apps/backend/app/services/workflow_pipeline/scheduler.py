"""Workflow Scheduler — queue and pump active workflows."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from app.services.workflow_pipeline import store
from app.services.workflow_pipeline.version import DEFAULT_MAX_CONCURRENT

_lock = threading.Lock()
_executor: ThreadPoolExecutor | None = None
_queued: list[str] = []
_running: set[str] = set()
_max_concurrent = DEFAULT_MAX_CONCURRENT


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(
            max_workers=_max_concurrent, thread_name_prefix="wfpipe"
        )
    return _executor


def set_max_concurrent(n: int) -> None:
    global _max_concurrent, _executor
    _max_concurrent = max(1, int(n))
    if _executor is not None:
        _executor.shutdown(wait=False, cancel_futures=True)
        _executor = None


def enqueue(workflow_id: str) -> None:
    with _lock:
        if workflow_id not in _queued and workflow_id not in _running:
            _queued.append(workflow_id)


def pump(runner: Callable[[str], None]) -> int:
    """Start queued workflows up to concurrency; returns started count."""
    started = 0
    with _lock:
        while _queued and len(_running) < _max_concurrent:
            wid = _queued.pop(0)
            _running.add(wid)
            _get_executor().submit(_wrap, runner, wid)
            started += 1
    return started


def _wrap(runner: Callable[[str], None], workflow_id: str) -> None:
    try:
        runner(workflow_id)
    finally:
        with _lock:
            _running.discard(workflow_id)


def wait_until_idle(timeout_sec: float = 30.0) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        with _lock:
            if not _queued and not _running:
                return True
        time.sleep(0.02)
    return False


def reset_scheduler() -> None:
    global _executor
    with _lock:
        _queued.clear()
        _running.clear()
        if _executor is not None:
            _executor.shutdown(wait=False, cancel_futures=True)
            _executor = None
