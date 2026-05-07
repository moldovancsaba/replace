from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4


JobStatus = Literal["pending", "running", "succeeded", "failed", "cancelled"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class BatchWorkflowConfig:
    id: str = "default"
    name: str = "Default Workflow"
    enabled: bool = False
    input_dir: str = ""
    output_dir: str = ""
    archive_dir: str = ""
    failed_dir: str = ""
    garment_id: str = ""
    engine_mode: str = "lite"
    preset: str = "high_quality"
    settings: dict[str, Any] = field(default_factory=dict)
    move_processed_inputs: bool = True
    retry_once: bool = True
    file_extensions: list[str] = field(
        default_factory=lambda: [".png", ".jpg", ".jpeg", ".webp"]
    )
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["updated_at"] = utc_now_iso()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BatchWorkflowConfig":
        merged = cls().to_dict()
        merged.update(data or {})
        return cls(**merged)

    def normalized_extensions(self) -> set[str]:
        return {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in self.file_extensions}


@dataclass(slots=True)
class BatchJobRecord:
    id: str
    workflow_id: str
    source_path: str
    source_filename: str
    status: JobStatus = "pending"
    created_at: str = field(default_factory=utc_now_iso)
    started_at: str | None = None
    finished_at: str | None = None
    attempt: int = 0
    output_image: str | None = None
    output_metadata: str | None = None
    error: str | None = None
    file_mtime_ns: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BatchJobRecord":
        return cls(**data)

    @classmethod
    def new(cls, workflow_id: str, source_path: Path) -> "BatchJobRecord":
        stat = source_path.stat()
        return cls(
            id=f"job_{utc_now_iso().replace(':', '').replace('-', '')}_{uuid4().hex[:8]}",
            workflow_id=workflow_id,
            source_path=str(source_path.resolve()),
            source_filename=source_path.name,
            file_mtime_ns=stat.st_mtime_ns,
        )


@dataclass(slots=True)
class WorkflowStatusSnapshot:
    workflow_id: str
    enabled: bool
    queue_length: int
    current_job_id: str | None
    processed_count: int
    failed_count: int
    cancelled_count: int
    last_error: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

