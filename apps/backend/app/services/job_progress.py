"""Push long-render pipeline state to the Next.js / Supabase job grid."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import reload_settings, settings

logger = logging.getLogger(__name__)


def _webhook_secret() -> str | None:
    reload_settings()
    secret = (
        getattr(settings, "generation_webhook_secret", None)
        or settings.ai_backend_secret
    )
    if secret and str(secret).strip():
        return str(secret).strip()
    return None


async def notify_pipeline_status(
    callback_url: str,
    *,
    status: str,
    chunks_completed: int | None = None,
    chunk_total: int | None = None,
    chunk_manifest: list[dict[str, Any]] | None = None,
    generated_video_url: str | None = None,
    error_message: str | None = None,
    backend_job_id: str | None = None,
) -> None:
    """PATCH pipeline status to the SaaS job row (Postgres via Next.js)."""
    if not callback_url:
        return

    secret = _webhook_secret()
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if secret:
        headers["Authorization"] = f"Bearer {secret}"
        headers["X-Rtas-Generation-Secret"] = secret

    progress_map = {
        "queued": 5,
        "preparing": 12,
        "generating": 40,
        "generating_chunks": 40,
        "rendering": 90,
        "compiling_media": 90,
        "uploading": 96,
        "completed": 100,
        "failed": 0,
        "cancelled": 0,
    }
    stage_labels = {
        "queued": "Queued for GPU worker",
        "preparing": "Preparing assets",
        "generating": "Generating video",
        "generating_chunks": "Generating video",
        "rendering": "Rendering / stitching",
        "compiling_media": "Rendering / stitching",
        "uploading": "Uploading output",
        "completed": "Render complete",
        "failed": "Render failed",
        "cancelled": "Cancelled",
    }
    normalized = status.lower()
    if (
        normalized == "generating"
        and chunk_total
        and chunks_completed is not None
        and chunk_total > 0
    ):
        progress_percent = min(
            88, int(15 + (chunks_completed / chunk_total) * 70)
        )
    else:
        progress_percent = progress_map.get(normalized, 20)

    payload: dict[str, Any] = {
        "status": status,
        "progressPercent": progress_percent,
        "stageLabel": stage_labels.get(normalized, "Processing"),
    }
    if chunks_completed is not None:
        payload["chunksCompleted"] = chunks_completed
    if chunk_total is not None:
        payload["chunkTotal"] = chunk_total
    if chunk_manifest is not None:
        payload["chunkManifest"] = chunk_manifest
    if generated_video_url is not None:
        payload["generatedVideoUrl"] = generated_video_url
    if error_message is not None:
        payload["errorMessage"] = error_message
    if backend_job_id is not None:
        payload["backendJobId"] = backend_job_id

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(callback_url, json=payload, headers=headers)
            response.raise_for_status()
    except Exception as exc:
        logger.warning(
            "Pipeline status webhook failed url=%s status=%s err=%s",
            callback_url,
            status,
            exc,
        )


class PipelineProgressReporter:
    """Reports chunk + stitch phases to the SaaS job grid."""

    def __init__(self, callback_url: str | None, backend_job_id: str) -> None:
        self.callback_url = callback_url
        self.backend_job_id = backend_job_id
        self._manifest: list[dict[str, Any]] = []

    async def queued(self, chunk_total: int) -> None:
        await notify_pipeline_status(
            self.callback_url or "",
            status="preparing",
            chunk_total=chunk_total,
            chunks_completed=0,
            chunk_manifest=[],
            backend_job_id=self.backend_job_id,
        )

    async def preparing(self, chunk_total: int) -> None:
        await notify_pipeline_status(
            self.callback_url or "",
            status="preparing",
            chunk_total=chunk_total,
            chunks_completed=0,
            chunk_manifest=list(self._manifest),
            backend_job_id=self.backend_job_id,
        )

    async def chunk_started(self, index: int, total: int, duration_sec: int) -> None:
        while len(self._manifest) <= index:
            self._manifest.append(
                {
                    "index": len(self._manifest),
                    "durationSec": 0,
                    "status": "pending",
                }
            )
        self._manifest[index] = {
            "index": index,
            "durationSec": duration_sec,
            "status": "generating",
        }
        await notify_pipeline_status(
            self.callback_url or "",
            status="generating",
            chunk_total=total,
            chunks_completed=sum(
                1 for row in self._manifest if row.get("status") == "completed"
            ),
            chunk_manifest=list(self._manifest),
            backend_job_id=self.backend_job_id,
        )

    async def chunk_completed(
        self,
        index: int,
        total: int,
        *,
        fal_url: str,
        local_path: str,
    ) -> None:
        self._manifest[index] = {
            "index": index,
            "durationSec": self._manifest[index].get("durationSec", 0),
            "status": "completed",
            "falUrl": fal_url,
            "localPath": local_path,
        }
        completed = sum(
            1 for row in self._manifest if row.get("status") == "completed"
        )
        await notify_pipeline_status(
            self.callback_url or "",
            status="generating",
            chunk_total=total,
            chunks_completed=completed,
            chunk_manifest=list(self._manifest),
            backend_job_id=self.backend_job_id,
        )

    async def chunk_failed(self, index: int, total: int, message: str) -> None:
        if index < len(self._manifest):
            self._manifest[index] = {
                **self._manifest[index],
                "status": "failed",
                "error": message,
            }
        await notify_pipeline_status(
            self.callback_url or "",
            status="failed",
            chunk_total=total,
            chunks_completed=sum(
                1 for row in self._manifest if row.get("status") == "completed"
            ),
            chunk_manifest=list(self._manifest),
            error_message=message,
            backend_job_id=self.backend_job_id,
        )

    async def compiling(self, total: int) -> None:
        await notify_pipeline_status(
            self.callback_url or "",
            status="rendering",
            chunk_total=total,
            chunks_completed=total,
            chunk_manifest=list(self._manifest),
            backend_job_id=self.backend_job_id,
        )

    async def uploading(self, total: int) -> None:
        await notify_pipeline_status(
            self.callback_url or "",
            status="uploading",
            chunk_total=total,
            chunks_completed=total,
            chunk_manifest=list(self._manifest),
            backend_job_id=self.backend_job_id,
        )

    async def completed(self, video_url: str, total: int) -> None:
        await self.uploading(total)
        await notify_pipeline_status(
            self.callback_url or "",
            status="completed",
            chunk_total=total,
            chunks_completed=total,
            chunk_manifest=list(self._manifest),
            generated_video_url=video_url,
            backend_job_id=self.backend_job_id,
        )

    async def failed(self, message: str, total: int | None = None) -> None:
        await notify_pipeline_status(
            self.callback_url or "",
            status="failed",
            chunk_total=total,
            error_message=message,
            chunk_manifest=list(self._manifest),
            backend_job_id=self.backend_job_id,
        )
