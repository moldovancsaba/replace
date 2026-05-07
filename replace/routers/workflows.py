from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.batch_models import BatchWorkflowConfig
from ..services.batch_queue import BatchQueueError
from ..services.batch_runtime import BatchRuntime


router = APIRouter(prefix="/api/workflows", tags=["workflows"])

_runtime: BatchRuntime | None = None


def set_batch_runtime(runtime: BatchRuntime) -> None:
    global _runtime
    _runtime = runtime


def get_batch_runtime() -> BatchRuntime:
    if _runtime is None:
        raise RuntimeError("Batch runtime not configured.")
    return _runtime


class WorkflowConfigPayload(BaseModel):
    name: str = "Default Workflow"
    enabled: bool = False
    input_dir: str = ""
    output_dir: str = ""
    archive_dir: str = ""
    failed_dir: str = ""
    garment_id: str = ""
    engine_mode: str = "lite"
    preset: str = "high_quality"
    settings: dict[str, Any] = Field(default_factory=dict)
    move_processed_inputs: bool = True
    retry_once: bool = True
    file_extensions: list[str] = Field(
        default_factory=lambda: [".png", ".jpg", ".jpeg", ".webp"]
    )


class EnqueuePayload(BaseModel):
    source_path: str


@router.get("/default")
def get_default_workflow() -> dict[str, Any]:
    runtime = get_batch_runtime()
    return runtime.load_workflow().to_dict()


@router.put("/default")
def update_default_workflow(payload: WorkflowConfigPayload) -> dict[str, Any]:
    runtime = get_batch_runtime()
    current = runtime.load_workflow()
    updated = BatchWorkflowConfig(
        id=current.id,
        name=payload.name,
        enabled=payload.enabled,
        input_dir=payload.input_dir,
        output_dir=payload.output_dir,
        archive_dir=payload.archive_dir,
        failed_dir=payload.failed_dir,
        garment_id=payload.garment_id,
        engine_mode=payload.engine_mode,
        preset=payload.preset,
        settings=payload.settings,
        move_processed_inputs=payload.move_processed_inputs,
        retry_once=payload.retry_once,
        file_extensions=payload.file_extensions,
        created_at=current.created_at,
    )
    return runtime.save_workflow(updated).to_dict()


@router.post("/default/start")
def start_default_workflow() -> dict[str, Any]:
    runtime = get_batch_runtime()
    workflow = runtime.load_workflow()
    workflow.enabled = True
    runtime.save_workflow(workflow)
    runtime.worker.start()
    return {
        "workflow_id": workflow.id,
        "enabled": True,
        "worker_running": runtime.worker.is_running,
    }


@router.post("/default/pause")
def pause_default_workflow() -> dict[str, Any]:
    runtime = get_batch_runtime()
    workflow = runtime.load_workflow()
    workflow.enabled = False
    runtime.save_workflow(workflow)
    runtime.worker.stop()
    return {
        "workflow_id": workflow.id,
        "enabled": False,
        "worker_running": runtime.worker.is_running,
    }


@router.get("/default/status")
def get_default_workflow_status() -> dict[str, Any]:
    runtime = get_batch_runtime()
    workflow = runtime.load_workflow()
    snapshot = runtime.queue.status_snapshot(workflow.id).to_dict()
    snapshot["worker_running"] = runtime.worker.is_running
    snapshot["workflow"] = workflow.to_dict()
    return snapshot


@router.get("/default/jobs")
def list_default_workflow_jobs() -> list[dict[str, Any]]:
    runtime = get_batch_runtime()
    return [job.to_dict() for job in runtime.queue.list_jobs(runtime.workflow_id)]


@router.post("/default/enqueue")
def enqueue_default_workflow_job(payload: EnqueuePayload) -> dict[str, Any]:
    runtime = get_batch_runtime()
    source_path = Path(payload.source_path)
    try:
        job = runtime.queue.enqueue_file(runtime.workflow_id, source_path)
    except BatchQueueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return job.to_dict()

