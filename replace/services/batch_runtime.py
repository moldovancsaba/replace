from __future__ import annotations

from pathlib import Path

from .batch_models import BatchWorkflowConfig
from .batch_queue import BatchQueue
from .batch_store import BatchStore
from .batch_worker import BatchProcessor, BatchWorker


class BatchRuntime:
    def __init__(
        self,
        *,
        data_root: Path,
        workflow_id: str = "default",
        processor: BatchProcessor | None = None,
    ) -> None:
        self.store = BatchStore(data_root)
        self.queue = BatchQueue(self.store)
        self.worker = BatchWorker(
            store=self.store,
            queue=self.queue,
            processor=processor,
            workflow_id=workflow_id,
        )
        self.workflow_id = workflow_id

    def load_workflow(self) -> BatchWorkflowConfig:
        return self.store.load_workflow(self.workflow_id)

    def save_workflow(self, workflow: BatchWorkflowConfig) -> BatchWorkflowConfig:
        self.store.save_workflow(workflow)
        return self.load_workflow()

