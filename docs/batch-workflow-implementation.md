# Batch workflow implementation

## Current purpose and status

The goal is a local workflow that watches an input directory, processes person images with a selected garment/settings and writes results continuously. The current repository implements the queue/API foundation for that goal. The try-on processor, directory watcher and frontend are not present.

The earlier implementation plan described the worker and router as future files. Both now exist; the source map below distinguishes their implemented behaviour from remaining integration work. This is a source review of revision `fb1a18039e6354bf18055ef28dd032f5548fd22b`, not a production-readiness claim.

## Implemented source map

| File | Current responsibility |
| --- | --- |
| [app.py](../app.py) | Compose FastAPI, a repository-local runtime and static health route |
| [batch_models.py](../services/batch_models.py) | Workflow/job/status data contracts |
| [batch_store.py](../services/batch_store.py) | Create data directories and read/write JSON records |
| [batch_queue.py](../services/batch_queue.py) | Explicit enqueue, extension validation, path/mtime deduplication and job transitions/counts |
| [batch_worker.py](../services/batch_worker.py) | Poll pending jobs, invoke a processor callback, record success/failure, start and stop a daemon thread |
| [batch_runtime.py](../services/batch_runtime.py) | Compose store, queue and worker; accept an optional processor callback |
| [workflows.py](../routers/workflows.py) | Configuration, start/pause, status/jobs and explicit enqueue routes |

The default app creates `BatchRuntime` without a processor. Its fallback raises `NotImplementedError`; the worker catches that exception and persists a failed job. No image inference or output generation happens in that default path.

## Local scope and persistence

The source exposes one default workflow and one worker per app process. Jobs are selected in the store's creation-time/ID order. Use a single process: JSON persistence has no cross-process lock or transactional protection.

Runtime layout:

```text
data/
  workflows/
    default.json
    jobs/
      <job-id>.json
```

Configuration and jobs survive reload from disk. That does not mean interrupted jobs recover: a persisted `running` job is not reset to pending, and the worker does not auto-start after application restart.

Input/output/archive/failed directory fields are persisted configuration only. The current worker does not scan directories, move input files, retry failed jobs or use those paths to create outputs.

## Remaining integration sequence

1. Define and connect a real image-processing callback through `BatchRuntime(processor=...)`.
2. Define output/metadata handling and safe input/archive behaviour.
3. Add folder watching and explicit retry/recovery semantics.
4. Build a frontend for configuration, controls, queue state and results.
5. Verify restart recovery, concurrency/data integrity and access boundaries before any broader exposure.

These are roadmap steps, not delivered capabilities. No such runtime change is included in the welcome repair.

## Verification and operation

Use the [root README](../README.md) for loopback startup, endpoint contracts, data boundaries and stop/recovery guidance. [Portfolio issue #925](https://github.com/moldovancsaba/mvp-factory-control/issues/925) records the synthetic verification results for this documentation repair. The static health endpoint alone cannot certify storage or processor readiness.
