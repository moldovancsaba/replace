from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .batch_models import BatchJobRecord, BatchWorkflowConfig


class BatchStore:
    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir)
        self.workflows_dir = self.root_dir / "workflows"
        self.jobs_dir = self.workflows_dir / "jobs"
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def workflow_path(self, workflow_id: str) -> Path:
        return self.workflows_dir / f"{workflow_id}.json"

    def job_path(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.json"

    def load_workflow(self, workflow_id: str = "default") -> BatchWorkflowConfig:
        path = self.workflow_path(workflow_id)
        if not path.exists():
            cfg = BatchWorkflowConfig(id=workflow_id)
            self.save_workflow(cfg)
            return cfg
        with path.open("r", encoding="utf-8") as fh:
            return BatchWorkflowConfig.from_dict(json.load(fh))

    def save_workflow(self, workflow: BatchWorkflowConfig) -> Path:
        path = self.workflow_path(workflow.id)
        data = workflow.to_dict()
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
            fh.write("\n")
        return path

    def save_job(self, job: BatchJobRecord) -> Path:
        path = self.job_path(job.id)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(job.to_dict(), fh, indent=2, sort_keys=True)
            fh.write("\n")
        return path

    def load_job(self, job_id: str) -> BatchJobRecord:
        with self.job_path(job_id).open("r", encoding="utf-8") as fh:
            return BatchJobRecord.from_dict(json.load(fh))

    def iter_jobs(self) -> Iterable[BatchJobRecord]:
        for path in sorted(self.jobs_dir.glob("*.json")):
            with path.open("r", encoding="utf-8") as fh:
                yield BatchJobRecord.from_dict(json.load(fh))

    def list_jobs(self, workflow_id: str | None = None) -> list[BatchJobRecord]:
        jobs = list(self.iter_jobs())
        if workflow_id:
            jobs = [job for job in jobs if job.workflow_id == workflow_id]
        jobs.sort(key=lambda job: (job.created_at, job.id))
        return jobs

