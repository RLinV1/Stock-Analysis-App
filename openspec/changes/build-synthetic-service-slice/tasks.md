## Tasks

- [x] Add a Java 21/Spring Boot API build, strict synthetic-request validation and a cross-language canonical-hash test.
- [ ] Add Liquibase-owned PostgreSQL schema and transactional idempotent submission/status/cancel logic with state-transition tests.
- [ ] Add the Python PostgreSQL worker, attempt-scoped S3 publication, lease/fencing and recovery tests.
- [ ] Add an authenticated completed-manifest route that reads the registered S3 object with a size bound and verifies its SHA-256 before returning it.
- [ ] Add standalone Compose images, health/init ordering and a full submit-to-result/restart/cancel verification.
- [ ] Reconcile docs/handoff after each step, validate OpenSpec, archive only after required runtime checks pass.
