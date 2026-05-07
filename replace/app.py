from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from .routers.workflows import router as workflows_router
from .routers.workflows import set_batch_runtime
from .services.batch_runtime import BatchRuntime


def create_app() -> FastAPI:
    app = FastAPI(title="replace")

    data_root = Path(__file__).resolve().parent.parent / "data"
    runtime = BatchRuntime(data_root=data_root)
    set_batch_runtime(runtime)

    app.include_router(workflows_router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

