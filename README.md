# replace

Local batch-workflow API scaffold for a future image try-on pipeline. The current source provides filesystem-backed workflow configuration, an explicit file queue and a background worker. **No image processor is wired into the application:** an enqueued job fails with a clear “No batch processor configured yet” error when processed.

This repository is useful for investigating the queue/API foundation. It is not a complete image-processing product. The inspected tree has no frontend, automatic input-directory watcher or deployment configuration.

## Start here

| Need | Source |
| --- | --- |
| App creation and health endpoint | [app.py](app.py) |
| Workflow API and payloads | [routers/workflows.py](routers/workflows.py) |
| Runtime composition and processor injection | [services/batch_runtime.py](services/batch_runtime.py) |
| Configuration and job records | [services/batch_models.py](services/batch_models.py) |
| Queue validation, deduplication and status | [services/batch_queue.py](services/batch_queue.py) |
| Worker lifecycle and missing-processor behaviour | [services/batch_worker.py](services/batch_worker.py) |
| JSON persistence | [services/batch_store.py](services/batch_store.py) |
| Implemented scope and roadmap | [Batch workflow implementation](docs/batch-workflow-implementation.md) |
| Dependency ranges | [requirements.txt](requirements.txt) |
| Documentation changes and remaining limits | [Release notes](RELEASE_NOTES.md) |

## Local setup

Use a disposable checkout and synthetic inputs first. Python 3.12 is the verification environment for this welcome repair; the dependency file specifies ranges rather than a reproducible lockfile.

From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open the local API documentation at http://127.0.0.1:8000/docs. Check http://127.0.0.1:8000/api/health for `{"status":"ok"}`. This health response does not inspect the queue, storage integrity or processor readiness.

The application creates a repository-relative `data/workflows/` directory during import. Workflow configuration is stored in `data/workflows/default.json`; job records are separate JSON files under `data/workflows/jobs/`. The existing ignore rules exclude `data/` and `.venv/`.

## API map

All workflow routes use the prefix `/api/workflows/default`.

| Method and path | Current behaviour |
| --- | --- |
| `GET /api/health` | Static process-level health response |
| `GET /api/workflows/default` | Load or create the default configuration |
| `PUT /api/workflows/default` | Save configuration from the request model |
| `GET /api/workflows/default/status` | Configuration, queue counts and worker flag |
| `GET /api/workflows/default/jobs` | List persisted jobs |
| `POST /api/workflows/default/enqueue` | Enqueue a server-local `source_path` |
| `POST /api/workflows/default/start` | Enable configuration and start the worker thread |
| `POST /api/workflows/default/pause` | Disable configuration and signal worker stop |

Use the generated API documentation to inspect request bodies. Enqueue accepts an existing local file with a configured extension; it does not validate image contents. Default extensions are PNG, JPG, JPEG and WebP. The queue rejects duplicate active jobs and previously successful jobs for the same resolved path and file modification time.

`PUT` uses defaults for omitted fields; it is not a partial-update operation. Saving `enabled: true` alone does not start the worker thread. Start and pause have dedicated routes.

## Data and operational boundaries

Run one local app process with one worker. The current JSON store has no cross-process locking or transactional writes. There is no authentication layer in the inspected routes, so keep the server bound to loopback and do not expose these local-file operations publicly.

Persisted workflow and job records survive a process restart. Worker threads do not restart automatically, and interrupted `running` jobs are not recovered or retried. Pause signals the worker and waits up to five seconds; it does not cancel or roll back an in-flight processor.

Stop the server with Ctrl-C. Before moving or resetting local data, stop the process and back up the entire `data/` directory. Preserve source inputs separately. This scaffold has no supported job-reset or restart-recovery command; do not infer one from the configuration fields.

## Implemented versus planned

Implemented: configuration persistence, explicit enqueue, extension checks, path/mtime deduplication, job states and counts, worker start/pause and API routes.

Still unimplemented in this tree: the actual image processor, folder watching, frontend, automatic retry, archive/output moves, cancelled-job API and interrupted-job recovery. Configuration fields such as `input_dir`, `output_dir`, `garment_id`, `retry_once` and `move_processed_inputs` do not establish those behaviours. See the [implementation note](docs/batch-workflow-implementation.md) for the next integration steps.

## Support, evidence and delivery

Repository owner: [moldovancsaba](https://github.com/moldovancsaba). Report product questions in this repository's [issues](https://github.com/moldovancsaba/replace/issues). This welcome repair is tracked in [portfolio issue #925](https://github.com/moldovancsaba/mvp-factory-control/issues/925); that issue does not migrate future product work into the control repository.

The runtime claims above were reviewed against source revision `fb1a18039e6354bf18055ef28dd032f5548fd22b`. The repair issue records the disposable startup/API/queue checks and their exact tested revision. Those checks use synthetic files and do not establish image-processing quality, production readiness or a hosted deployment.
