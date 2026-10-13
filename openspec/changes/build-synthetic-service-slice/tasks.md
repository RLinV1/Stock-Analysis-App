## Tasks

- [x] Add a Java 21/Spring Boot API build, strict synthetic-request validation and a cross-language canonical-hash test.
- [ ] Add Liquibase-owned PostgreSQL schema and transactional idempotent submission/status/cancel logic with state-transition tests.
- [ ] Add the Python PostgreSQL worker, attempt-scoped S3 publication, lease/fencing and recovery tests.
- [ ] Add an authenticated completed-manifest route that reads the registered S3 object with a size bound and verifies its SHA-256 before returning it.
- [ ] Add an authenticated, keyset-paginated run list (newest first) with a supporting append-only index migration.
- [ ] Let the worker stop on SIGTERM without claiming new work and release an owned run it has not published.
- [ ] Add a hash-verified completed report route that resolves `report.json` through the verified artifact index.
- [ ] Stop training at the next epoch boundary when a running run's cancellation wins, without publishing.
- [ ] Add PostgreSQL integration tests for repository and worker SQL that skip without Docker or a test database.
- [ ] Add standalone Compose images, health/init ordering and a full submit-to-result/restart/cancel verification.
- [ ] Reconcile docs/handoff after each step, validate OpenSpec, archive only after required runtime checks pass.

## Attempt lifecycle correction — 2026-10-13 continuation

- [x] Close an expired open attempt when claim rejects its invalid stored request; write a PostgreSQL regression test (not executed).
- [ ] Execute the regression against PostgreSQL when allowed; reconcile implementation evidence and validate OpenSpec.
