from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .batch_models import BatchJobRecord, WorkflowStatusSnapshot, utc_now_iso
from .batch_store import BatchStore


class BatchQueueError(ValueError):
    pass


class BatchQueue:
    def __init__(self, store: BatchStore):
        self.store = store

    def _jobs(self, workflow_id: str) -> list[BatchJobRecord]:
        return self.store.list_jobs(workflow_id=workflow_id)

    def _active_jobs(self, workflow_id: str) -> list[BatchJobRecord]:
        return [
            job
            for job in self._jobs(workflow_id)
            if job.status in {"pending", "running"}
        ]

    def _same_source(self, left: BatchJobRecord, source_path: Path, source_mtime_ns: int) -> bool:
        return left.source_path == str(source_path.resolve()) and left.file_mtime_ns == source_mtime_ns

    def enqueue_file(self, workflow_id: str, source_path: Path) -> BatchJobRecord:
        source_path = Path(source_path)
        if not source_path.exists() or not source_path.is_file():
            raise BatchQueueError(f"Input file does not exist: {source_path}")

        workflow = self.store.load_workflow(workflow_id)
        if source_path.suffix.lower() not in workflow.normalized_extensions():
            raise BatchQueueError(f"Unsupported file extension: {source_path.suffix}")

        stat = source_path.stat()
        for job in self._active_jobs(workflow_id):
            if self._same_source(job, source_path, stat.st_mtime_ns):
                raise BatchQueueError(f"Duplicate active job for: {source_path.name}")

        for job in self._jobs(workflow_id):
            if job.status == "succeeded" and self._same_source(job, source_path, stat.st_mtime_ns):
                raise BatchQueueError(f"File already processed: {source_path.name}")

        job = BatchJobRecord.new(workflow_id=workflow_id, source_path=source_path)
        self.store.save_job(job)
        return job

    def next_pending_job(self, workflow_id: str) -> BatchJobRecord | None:
        for job in self._jobs(workflow_id):
            if job.status == "pending":
                return job
        return None

    def mark_running(self, job_id: str) -> BatchJobRecord:
        job = self.store.load_job(job_id)
        job.status = "running"
        job.attempt += 1
        job.started_at = utc_now_iso()
        job.error = None
        self.store.save_job(job)
        return job

    def mark_succeeded(
        self,
        job_id: str,
        *,
        output_image: str,
        output_metadata: str | None = None,
    ) -> BatchJobRecord:
        job = self.store.load_job(job_id)
        job.status = "succeeded"
        job.finished_at = utc_now_iso()
        job.output_image = output_image
        job.output_metadata = output_metadata
        job.error = None
        self.store.save_job(job)
        return job

    def mark_failed(self, job_id: str, error: str) -> BatchJobRecord:
        job = self.store.load_job(job_id)
        job.status = "failed"
        job.finished_at = utc_now_iso()
        job.error = error
        self.store.save_job(job)
        return job

    def mark_cancelled(self, job_id: str, error: str | None = None) -> BatchJobRecord:
        job = self.store.load_job(job_id)
        job.status = "cancelled"
        job.finished_at = utc_now_iso()
        job.error = error
        self.store.save_job(job)
        return job

    def status_snapshot(self, workflow_id: str = "default") -> WorkflowStatusSnapshot:
        jobs = self._jobs(workflow_id)
        current = next((job for job in jobs if job.status == "running"), None)
        processed = [job for job in jobs if job.status == "succeeded"]
        failed = [job for job in jobs if job.status == "failed"]
        cancelled = [job for job in jobs if job.status == "cancelled"]
        queue_length = len([job for job in jobs if job.status == "pending"])
        last_error = failed[-1].error if failed else None
        workflow = self.store.load_workflow(workflow_id)
        return WorkflowStatusSnapshot(
            workflow_id=workflow_id,
            enabled=workflow.enabled,
            queue_length=queue_length,
            current_job_id=current.id if current else None,
            processed_count=len(processed),
            failed_count=len(failed),
            cancelled_count=len(cancelled),
            last_error=last_error,
        )

    def list_jobs(self, workflow_id: str = "default") -> list[BatchJobRecord]:
        return self._jobs(workflow_id)

