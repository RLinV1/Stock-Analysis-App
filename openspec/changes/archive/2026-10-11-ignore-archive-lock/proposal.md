## Why

The transient OpenSpec archive claim is tracked in Git. A stale PID from September blocked archiving the completed mobile preview, and archiving wrote another machine-specific PID into the tracked file. Future changes should not depend on manual lock cleanup.

## What Changes

- Stop tracking `openspec/changes/archive/.openspec-archive.lock` and ignore future transient claims at that path.
- Verify the recorded process is absent before removing the current claim, then validate the workflow and repository state.

## Capabilities

No behavioral capability changes. This is tooling hygiene; `skip_specs: true` applies.

## Impact

The archive lock is a local concurrency guard only. Existing archived changes and main specs remain intact.
