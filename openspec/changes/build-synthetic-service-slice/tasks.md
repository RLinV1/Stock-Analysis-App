## Tasks

- [x] Add a Java 21/Spring Boot API build, strict synthetic-request validation and a cross-language canonical-hash test.
- [x] Add Liquibase-owned PostgreSQL schema and transactional idempotent submission/status/cancel logic with state-transition tests.
- [ ] Add the Python PostgreSQL worker, attempt-scoped S3 publication, lease/fencing and recovery tests.
- [ ] Add an authenticated completed-manifest route that reads the registered S3 object with a size bound and verifies its SHA-256 before returning it.
- [x] Add an authenticated, keyset-paginated run list (newest first) with a supporting append-only index migration.
- [ ] Let the worker stop on SIGTERM without claiming new work and release an owned run it has not published.
- [ ] Add a hash-verified completed report route that resolves `report.json` through the verified artifact index.
- [ ] Stop training at the next epoch boundary when a running run's cancellation wins, without publishing.
- [x] Add PostgreSQL integration tests for repository and worker SQL that skip without Docker or a test database.
- [ ] Add standalone Compose images, health/init ordering and a full submit-to-result/restart/cancel verification.
- [ ] Reconcile docs/handoff after each step, validate OpenSpec, archive only after required runtime checks pass.

## Attempt lifecycle correction — 2026-10-13 continuation

- [x] Close an expired open attempt when claim rejects its invalid stored request; write a PostgreSQL regression test (not executed).
- [x] Execute the regression against PostgreSQL when allowed; reconcile implementation evidence and validate OpenSpec.

## Lease fencing continuation — 2026-10-14

- [x] Guard cancellation acknowledgement, owned failure and shutdown release with the unexpired database lease, and roll back if the owned attempt cannot be closed; verify unit behavior.
- [x] Execute expiry/no-mutation PostgreSQL regression tests when a disposable database is available.

## Training supervision continuation — 2026-10-14

- [x] Isolate training in a child process, supervise cancellation independently, enforce a two-hour hard compute deadline, bound database calls and reap unresponsive children; verify subprocess and unit tests.
- [x] Register retained completed-epoch checkpoints through the existing attempt checkpoint columns with lease/token fencing, and verify source/unit guards.
- [ ] Verify supervisor cancellation, deadline, checkpoint recovery and database outage against PostgreSQL/LocalStack under Compose.

## Lease lock-wait regression continuation — 2026-10-15

- [x] Extend unit lease guards and write PostgreSQL regressions proving every owned transition rechecks database time after a competing run-row lock wait; execute local worker/child-process and research checks.
- [x] Execute the lock-wait regressions against disposable PostgreSQL and verify no expired-owner mutation after contention.

## Explicit browser CORS continuation — 2026-10-15

- [x] Add default-disabled exact-origin CORS before bearer authentication, strict configuration/path restrictions and focused HTTP/configuration tests; verify Java tests and document runtime configuration.
- [x] Verify the configured CORS policy through the real browser/API smoke, preserving bearer requirements and default-disabled behavior.

## Application startup migration correction — 2026-10-15

- [x] Replace bare liquibase-core with the Boot 4 Liquibase starter; verify automatic migration and reopening through the actual application context against fresh PostgreSQL, then rerun the bounded browser smoke.

## Independent image verification — 2026-10-15

- [x] Exclude local credentials/account/agent directories from Docker contexts and verify the exported context omits them while retaining build inputs.
- [x] Build the existing backend and CPU worker Dockerfiles; repair packaging defects and record exact build evidence without LocalStack.
- [x] Verify non-root migration/API operation against disposable PostgreSQL and one bounded training child in the worker image; document repeat commands and retain full storage/Compose gates as open.
- [x] Replace the worker image's legacy multi-index install with a complete Linux CPython 3.12 CPU wheel/hash lock, sourcing torch explicitly from its official wheel and other packages from PyPI; verify a clean hash-enforced install, dependency consistency and numerical/recovery checks.
## Final-boundary stop source continuation — 2026-10-16

- [ ] Final/chunk checkpoint-boundary stopping, safe missing-checkpoint resume rejection and regression source are written; read/review and verify after authorization. No runtime check has executed while the user's independent GPU model runs.
- [ ] After execution authorization, verify exact stop/resume numerical behavior, worker/child compatibility and broader research regressions; retain full Compose/LocalStack gates and durable service-resume limitations.
## Immutable publication source continuation — 2026-10-17

- [ ] Conditional create-only result/index writes and missing-report/reserved-index preflight plus fake-storage write-option/collision/no-write regression source are written 2026-10-17; verify after authorization. No storage access or project execution occurred.
- [ ] After authorization, run worker regressions and separately verify conditional-write/readback/collision behavior with the selected LocalStack under the existing Compose/storage gates. Keep current storage exclusion and full acceptance limitations.
