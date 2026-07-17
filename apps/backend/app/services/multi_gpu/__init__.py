"""Multi GPU Engine — public API."""

from app.services.multi_gpu.distributor import complete_job, distribute_pending
from app.services.multi_gpu.engine import (
    build_multi_gpu_dict,
    build_multi_gpu_plan,
    get_plan,
)
from app.services.multi_gpu.models import MultiGpuPlan
from app.services.multi_gpu.monitor import build_monitor_snapshot
from app.services.multi_gpu.queue import get_job, queue_status
from app.services.multi_gpu.workers import (
    ensure_default_fleet,
    heartbeat,
    list_workers,
    register_worker,
)

__all__ = [
    "MultiGpuPlan",
    "build_multi_gpu_dict",
    "build_multi_gpu_plan",
    "get_plan",
    "distribute_pending",
    "complete_job",
    "queue_status",
    "get_job",
    "list_workers",
    "register_worker",
    "heartbeat",
    "ensure_default_fleet",
    "build_monitor_snapshot",
]
