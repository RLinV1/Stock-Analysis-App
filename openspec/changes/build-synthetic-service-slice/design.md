## Sequence

1. Lock a compatible Java 21/Spring Boot build and establish contract parsing/canonical SHA-256 agreement with the Python fixture. Add a small API build/test shell first.
2. Add append-only Liquibase migrations and PostgreSQL transactional submission, claim, heartbeat, cancellation and conditional publication. Use a single worker, attempt-scoped fencing tokens and bounded retries.
3. Add a Python worker that shares the existing local request adapter, copies finished artifacts to attempt-scoped LocalStack S3 keys, verifies hashes/readability, then commits manifest key/hash and completion only if its token still owns the run.
4. Package the API/worker and standalone Compose dependencies. Run a submit-to-result smoke and failure/restart checks before marking the change complete.

## Contracts and safety

### Lease fencing continuation — 2026-10-14

Canonical SPEC §2 requires an unexpired database lease for every owned mutation, including cancellation acknowledgement, failure and shutdown release. Heartbeat/publication already check expiry, but those three transitions currently check only the token. Add the missing database-time guards before implementing supervisor work; stale owners must leave the run and attempt untouched for the claim-time expiry sweep. Check affected attempt-row counts so a missing attempt rolls back the run transition. Unit SQL-guard checks and optional PostgreSQL regressions cover this logical change; actual PostgreSQL execution remains required and unrun.

### Training supervision continuation — 2026-10-14

Execute training in a separate Python child with a parent-owned stop sentinel and result file. The existing lease thread runs in the parent; the parent monitors the child every 100 ms, requests epoch-boundary cancellation when ownership is lost and terminates unresponsive compute after a five-second grace (within the canonical 30 seconds). A two-hour monotonic deadline terminates compute independently of the training loop. Bound PostgreSQL connection/statement/lock waits so loss of database access stops compute before the last confirmed 60-second lease. Preserve SIGTERM semantics: stop before training releases; stop during training lets owned work finish within its hard deadline. Child stdout/stderr contain no service responses; sanitized exception classes propagate to the parent failure path.

Retain a completed-epoch checkpoint on stopped training only while ownership/lease still permits registration. Upload an immutable attempt-specific checkpoint object, verify readback, then update existing run_attempt checkpoint columns under a locked, current-token/unexpired run. Durable automatic resume with compatibility identity validation remains a distinct unfinished requirement; the local runner already verifies resume identity, but service attempts do not yet reconstruct its run directory from object storage. UUID token equality plus increasing attempt_no currently supplies unique fencing identities, not the canonical monotonically increasing numeric token; that discrepancy remains explicit.

`contracts/synthetic-run-request.v1.schema.json` is the only accepted compute body for this slice. Java must reject duplicate fields/keys, non-integer numerics, unsupported versions and over-budget values before database insertion; match the Python canonical request fixture. `Idempotency-Key` is scoped to an authenticated local operator. A repeated key and same canonical body returns the same run, while a conflicting body returns 409. The API requires a configured operator bearer secret even on loopback; do not log it. Problem responses have stable codes and no internal paths. Request size is bounded.

Postgres is the queue. Liquibase alone changes schema. Worker claims use short transactions and `FOR UPDATE SKIP LOCKED`, lease and token checks; no S3 object makes a run COMPLETE by itself. Cancellation wins unless a valid publication commits first. Final objects use `runs/{run_id}/attempts/{attempt_id}/...`; orphan uploads are not active results. A stable manifest key is published in PostgreSQL after hash checks.

Compose must start without K3s. The host publishes only `127.0.0.1:8080` for the API. PostgreSQL and LocalStack remain on its internal network. Require `LOCALSTACK_AUTH_TOKEN` and an operator secret through ignored environment configuration; use a pinned image and document account/prerequisite limits. No public network or Tailscale reconnection occurs here.

## Verification gates

### Explicit browser origins — 2026-10-15 continuation

For the authorized local browser/API smoke, add opt-in CORS using Spring's built-in `CorsFilter`, registered deterministically before bearer authentication. `PORTFOLIO_CORS_ALLOWED_ORIGINS` defaults empty and accepts comma-separated exact HTTP(S) origins only; wildcards, credentials, paths, query/fragment components and invalid ports fail startup without echoing configuration. CORS applies only to canonical raw `/api/v1/**` paths (no path parameters, encoded path characters, duplicate separators or traversal segments), GET/POST and Authorization/Content-Type/Idempotency-Key request headers. Only a validated preflight may complete without a bearer credential; every actual API request still reaches the bearer filter. Cookies/credentialed browser requests are not enabled. The exact public health path retains its current behavior. Unit HTTP tests cover valid preflight, actual bearer responses, forbidden origin/method/header/path variants and disabled/invalid configuration. Live browser acceptance remains a separate gate.

Java contract and HTTP tests must run without Docker. Repository/application-startup tests require Docker; worker SQL requires disposable PostgreSQL. As of 2026-10-15 these checks pass, along with bounded real browser mutations. Application startup uses the Boot 4 Liquibase starter so migrations run automatically rather than relying on manually constructed test migration beans. Worker failure/publication and full Compose gates still require real storage verification. The user excluded LocalStack checks; keep those gates and this change active. Spring Boot 4.1.1/Java 21 resolves and packages successfully.
