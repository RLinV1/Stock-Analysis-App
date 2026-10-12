## ADDED Requirements

### Requirement: Accept bounded authenticated synthetic jobs
The API SHALL accept only the versioned synthetic request contract with a configured operator credential, bounded body and Idempotency-Key. It SHALL persist a new job and canonical request hash atomically. Same key and request SHALL return the existing job; same key and different request SHALL return a conflict.

#### Scenario: Retry a submission
- **WHEN** an authenticated operator repeats a valid POST with the same idempotency key and canonical body
- **THEN** the API returns the original run ID and does not enqueue another run

### Requirement: Execute and publish only owned attempts
The worker SHALL claim queued or expired work using a lease and unique fencing token, execute at most one job concurrently, upload attempt-scoped artifacts with hashes, and publish completion only while its token owns the uncancelled run.

#### Scenario: Worker dies after upload
- **WHEN** a worker uploads artifacts but dies before a conditional completion update
- **THEN** those objects do not appear as a completed result and a later valid attempt can recover the job

### Requirement: Support cancellation and readback
The API SHALL expose run status and idempotent cancellation. A queued run SHALL cancel immediately; a running run SHALL request cancellation and SHALL not later publish COMPLETE if cancellation wins. Completed runs SHALL expose their immutable manifest/report references.

#### Scenario: Cancel running work
- **WHEN** cancellation commits before a worker's completion update
- **THEN** the worker's stale or cancelled attempt cannot publish completion

### Requirement: Run standalone under Compose
After documented private prerequisites, Compose SHALL start the API, worker, PostgreSQL, Liquibase migration, LocalStack and bucket initializer without Kubernetes or manual bucket/schema creation.

#### Scenario: Start local stack
- **WHEN** the operator supplies the required private secrets and runs `docker compose up`
- **THEN** health checks, migration and bucket initialization reach readiness and one synthetic request can complete end to end
