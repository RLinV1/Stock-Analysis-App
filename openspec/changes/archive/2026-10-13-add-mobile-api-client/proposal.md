## Why

The service now publishes its HTTP contract (`contracts/runs-api.v1.openapi.yaml`). The phone needs a typed, testable client for that contract before any screen can submit or read runs. Building it separately from the UI keeps the offline preview honest until a reachable service is configured.

## What Changes

- Add `mobile/src/api/contract.ts` with request v1 types, bounds and validation, and `mobile/src/api/client.ts` with submit, status, cancel and manifest calls.
- Validate inputs before any network call, send the bearer credential and Idempotency-Key, enforce a timeout, shape-check every response and raise typed errors instead of inventing results.
- Reuse the shared bounds in the existing draft form. No UI wiring; Start experiment stays disabled.

## Capabilities

### Modified Capabilities

- `mobile-experiment-shell`: a contract-checked API client exists but is not connected to screens.

## Impact

Mobile source and tests only. No service configuration, credential storage or network use is added to the running app.
