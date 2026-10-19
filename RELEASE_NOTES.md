# Release notes

## New Features

Added a root navigation and local-operation guide for the existing batch-workflow API scaffold.

## Fixed Bugs

Corrected the implementation note that still listed the existing worker and API router as planned. Documented that the default processor is unconfigured and does not generate images.

## Known Issues

No image processor, automatic folder watcher or frontend is wired into the inspected source. Retry/archive configuration is not implemented behaviour. JSON storage has no cross-process locking, interrupted jobs have no automatic recovery and the routes have no authentication layer. Dependencies use version ranges rather than a lockfile. See [README.md](README.md) for safe local boundaries.

## Future Roadmap

Connect and verify a processor, define output/archive handling, then add watching, explicit recovery and a UI. Keep these changes scoped and evidenced separately.

This release changes documentation only. Runtime, dependencies and deployment configuration are unchanged. Revert this documentation commit to roll back the welcome repair; no data migration is needed.
