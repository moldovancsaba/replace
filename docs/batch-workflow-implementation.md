# Batch Workflow Implementation

## Goal

Allow the app to watch an input directory, queue new person images, process them with the active garment and settings, and write results into an output directory continuously.

## Phase 1 Scope

- One active workflow
- One input directory
- One output directory
- One garment profile
- One worker
- FIFO processing
- Local-only

## Backend File Map

### `services/batch_models.py`

Defines the persistent data contracts:

- `BatchWorkflowConfig`
- `BatchJobRecord`
- `WorkflowStatusSnapshot`

These models are JSON-serializable and filesystem-oriented.

### `services/batch_store.py`

Persistent storage for workflow config and job records.

Responsibilities:

- create workflow data directories
- read/write workflow config
- read/write per-job JSON files
- list jobs by status/time

### `services/batch_queue.py`

Persistent queue manager for batch jobs.

Responsibilities:

- enqueue valid input files
- dedupe jobs by source path + file mtime
- transition jobs across `pending/running/succeeded/failed/cancelled`
- expose a status snapshot for the future API/UI

## Planned Next Files

### `services/batch_worker.py`

Will:

- poll the queue
- process one job at a time
- call the existing try-on pipeline
- save outputs and logs

### `routers/workflows.py`

Will expose:

- `GET /api/workflows/default`
- `PUT /api/workflows/default`
- `POST /api/workflows/default/start`
- `POST /api/workflows/default/pause`
- `GET /api/workflows/default/status`
- `GET /api/workflows/default/jobs`

### `frontend/src/pages/WorkflowPage.tsx`

Will provide:

- input/output directory settings
- garment/profile selection
- start/pause controls
- queue/job table
- recent results

## Runtime Layout

Recommended filesystem layout:

```text
data/
  workflows/
    default.json
    jobs/
      <job-id>.json
```

Input/output/archive directories are user-configurable absolute paths and are stored in the workflow config.

## Integration Sequence

1. Land config + queue persistence
2. Add worker loop
3. Expose workflow API
4. Add UI page
5. Add restart recovery

## Acceptance Criteria For This Slice

This first backend slice is complete when:

- workflow config can be saved and loaded
- batch jobs can be persisted to disk
- duplicate input files are rejected cleanly
- queue state survives app restart
