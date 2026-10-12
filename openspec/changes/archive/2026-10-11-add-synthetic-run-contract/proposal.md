## Why

The tested research runner and the synthetic mobile preview have no shared request format. Define the smallest bounded input that a later Spring API can store and a Python worker can execute, without presenting A0 artifacts as the planned v2 replay manifest.

## What Changes

- Add a closed, versioned JSON Schema for one synthetic fixed-holdout experiment and a checked example.
- Validate the same shape in Python before creating files, derive the existing A0 split deterministically, and expose a CLI command that runs the request locally.
- Record a canonical request hash suitable for later idempotency mapping. This is a request hash, not the v2 input-identity digest.
- Test rejection and a small end-to-end local run; keep durable jobs, HTTP, Compose, and external-manifest verification in later changes.

## Capabilities

### New Capabilities

- `synthetic-run-contract`: a bounded executable local request contract for the first service slice.

## Impact

Adds `contracts/`, a Python adapter and CLI path. No dependency, network service, database or mobile behavior changes. Full v2 manifest/replay remains planned.
