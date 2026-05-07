from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

from .batch_models import BatchJobRecord, BatchWorkflowConfig
from .batch_queue import BatchQueue
from .batch_store import BatchStore


BatchProcessor = Callable[[BatchJobRecord, BatchWorkflowConfig], tuple[str, str | None]]


class BatchWorker:
    def __init__(
        self,
        *,
        store: BatchStore,
        queue: BatchQueue,
        processor: BatchProcessor | None = None,
        workflow_id: str = "default",
        poll_interval_seconds: float = 1.0,
    ) -> None:
        self.store = store
        self.queue = queue
        self.processor = processor or self._unconfigured_processor
        self.workflow_id = workflow_id
        self.poll_interval_seconds = poll_interval_seconds
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._state_lock = threading.Lock()
        self._running = False

    @property
    def is_running(self) -> bool:
        with self._state_lock:
            return self._running

    def start(self) -> None:
        with self._state_lock:
            if self._running:
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_loop,
                name=f"batch-worker-{self.workflow_id}",
                daemon=True,
            )
            self._running = True
            self._thread.start()

    def stop(self) -> None:
        with self._state_lock:
            if not self._running:
                return
            self._stop_event.set()
            thread = self._thread
            self._running = False
        if thread and thread.is_alive():
            thread.join(timeout=5)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            workflow = self.store.load_workflow(self.workflow_id)
            if not workflow.enabled:
                time.sleep(self.poll_interval_seconds)
                continue

            job = self.queue.next_pending_job(self.workflow_id)
            if job is None:
                time.sleep(self.poll_interval_seconds)
                continue

            self._process(job, workflow)

    def _process(self, job: BatchJobRecord, workflow: BatchWorkflowConfig) -> None:
        self.queue.mark_running(job.id)
        try:
            output_image, output_metadata = self.processor(job, workflow)
            self.queue.mark_succeeded(
                job.id,
                output_image=output_image,
                output_metadata=output_metadata,
            )
        except Exception as exc:
            self.queue.mark_failed(job.id, str(exc))

    @staticmethod
    def _unconfigured_processor(
        job: BatchJobRecord, workflow: BatchWorkflowConfig
    ) -> tuple[str, str | None]:
        raise NotImplementedError(
            "No batch processor configured yet. Wire the worker to the try-on pipeline "
            f"before running workflow {workflow.id} for {Path(job.source_path).name}."
        )

