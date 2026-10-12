## Sequence

1. Lock a compatible Java 21/Spring Boot build and establish contract parsing/canonical SHA-256 agreement with the Python fixture. Add a small API build/test shell first.
2. Add append-only Liquibase migrations and PostgreSQL transactional submission, claim, heartbeat, cancellation and conditional publication. Use a single worker, attempt-scoped fencing tokens and bounded retries.
3. Add a Python worker that shares the existing local request adapter, copies finished artifacts to attempt-scoped LocalStack S3 keys, verifies hashes/readability, then commits manifest key/hash and completion only if its token still owns the run.
4. Package the API/worker and standalone Compose dependencies. Run a submit-to-result smoke and failure/restart checks before marking the change complete.

## Contracts and safety

`contracts/synthetic-run-request.v1.schema.json` is the only accepted compute body for this slice. Java must reject duplicate fields/keys, non-integer numerics, unsupported versions and over-budget values before database insertion; match the Python canonical request fixture. `Idempotency-Key` is scoped to an authenticated local operator. A repeated key and same canonical body returns the same run, while a conflicting body returns 409. The API requires a configured operator bearer secret even on loopback; do not log it. Problem responses have stable codes and no internal paths. Request size is bounded.

Postgres is the queue. Liquibase alone changes schema. Worker claims use short transactions and `FOR UPDATE SKIP LOCKED`, lease and token checks; no S3 object makes a run COMPLETE by itself. Cancellation wins unless a valid publication commits first. Final objects use `runs/{run_id}/attempts/{attempt_id}/...`; orphan uploads are not active results. A stable manifest key is published in PostgreSQL after hash checks.

Compose must start without K3s. The host publishes only `127.0.0.1:8080` for the API. PostgreSQL and LocalStack remain on its internal network. Require `LOCALSTACK_AUTH_TOKEN` and an operator secret through ignored environment configuration; use a pinned image and document account/prerequisite limits. No public network or Tailscale reconnection occurs here.

## Verification gates

Java contract and HTTP tests must run without Docker. Database state tests, worker failure tests, and Compose round trip need a working Docker engine and LocalStack token. This host currently lacks the Docker Desktop Linux engine; do not claim container checks passed until they run. A source-only scaffold remains an active change if those checks cannot run. Spring Boot 4.1.1 is the currently documented stable release with Java 21 compatibility; its actual Maven dependency resolution still needs a local build.
