from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from src.services.cache_service import CacheService


JOB_TTL_SECONDS = 60 * 60 * 24


class JobService:
    def __init__(self, namespace: str) -> None:
        self.namespace = namespace
        self.cache = CacheService()

    def create_job(self, prefix: str) -> str:
        job_id = f"{prefix}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        self.set_status(job_id, status="queued")
        return job_id

    def set_status(self, job_id: str, **updates: Any) -> None:
        current = self.get_status(job_id) or {}
        payload = {
            **current,
            **updates,
            "job_id": job_id,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        self.cache.set_json(self.namespace, job_id, payload, ttl_seconds=JOB_TTL_SECONDS)

    def mark_running(self, job_id: str) -> None:
        self.set_status(
            job_id,
            status="running",
            started_at=datetime.now(UTC).isoformat(),
            error=None,
        )

    def mark_completed(self, job_id: str, **result: Any) -> None:
        self.set_status(
            job_id,
            status="completed",
            finished_at=datetime.now(UTC).isoformat(),
            error=None,
            **result,
        )

    def mark_failed(self, job_id: str, error: Exception) -> None:
        self.set_status(
            job_id,
            status="failed",
            finished_at=datetime.now(UTC).isoformat(),
            error=str(error),
        )

    def get_status(self, job_id: str) -> dict[str, Any] | None:
        return self.cache.get_json(self.namespace, job_id)
