## Why

The local request adapter can complete an A0 experiment, but the phone preview cannot submit one and no durable service exists. Build the first bounded backend path under the approved stack, using the request contract before widening the research surface.

## What Changes

- Add a Java 21/Spring Boot API that validates version 1 synthetic requests, requires a private operator credential, stores idempotent submissions and exposes run status/cancel, a paginated run list (added 2026-10-13) and completed report links.
- Let Liquibase own PostgreSQL job/attempt tables. A Python worker claims one job at a time with leases/fencing, executes the current runner, stores verified artifacts in LocalStack S3 and publishes completion conditionally.
- Add standalone Compose startup for API, worker, PostgreSQL, migration, LocalStack and bucket initialization; keep the API host port loopback-only and no database/S3 host ports.
- Test contracts, state transitions, worker failure paths and a full synthetic round trip. Keep physical Android/Tailscale and K3s separate.

## Capabilities

### New Capabilities

- `synthetic-service-jobs`: durable local synthetic experiment submission, execution and retrieval.

## Impact

2026-10-15 independent image continuation: exclude ignored credentials and local agent/account directories from Docker build contexts, audit the actual exported context without revealing contents, build the existing API/worker images, and run non-root migration/API and synthetic training checks without LocalStack. Use disposable PostgreSQL/network resources; do not replace S3 with a different production backend or treat these checks as full Compose/result-publication acceptance. Correct packaging defects revealed by the builds and record image/runtime evidence immediately.

Adds `backend/`, worker integration and Compose infrastructure. The existing A0 CLI and synthetic preview remain usable. External v2 manifests, historical studies, ONNX, iOS and K3s are not delivered in this slice.
