## ADDED Requirements

### Requirement: Exclude private local state from image builds
Docker build contexts SHALL omit environment credential files, local AWS/agent/account state and private key/credential files. Required application source and contract fixtures SHALL remain available for builds. Runtime secrets SHALL be supplied at execution time rather than copied into an image.

#### Scenario: Build with local runtime credentials present
- **WHEN** an operator builds API or worker images from a checkout containing ignored environment credentials and local account directories
- **THEN** those files are absent from the Docker context and images while the required application sources remain available

### Requirement: Install a closed CPU worker environment
The Linux x86_64 CPython 3.12 CPU worker image SHALL install exact wheel artifacts from a complete SHA-256 lock and reject missing or changed hashes. Torch SHALL use its explicit official CPU wheel; ordinary dependencies SHALL use PyPI without a global extra index. The clean image SHALL pass dependency consistency and synthetic numerical/recovery checks. This environment lock SHALL NOT imply Windows/GPU or full experiment replay support.

#### Scenario: An artifact differs from the worker lock
- **WHEN** a selected wheel's bytes differ from its recorded SHA-256 or a dependency lacks a required hash
- **THEN** image installation fails rather than accepting the artifact or resolving an unlocked substitute

### Requirement: Allow explicitly configured browser origins
The API SHALL disable cross-origin browser access by default. An explicit comma-separated exact HTTP(S) origin allowlist SHALL enable CORS only for canonical `/api/v1/**` paths, GET/POST methods and Authorization/Content-Type/Idempotency-Key request headers. Invalid or wildcard origin configuration SHALL fail startup. A valid preflight MAY complete without bearer authentication; actual API requests SHALL still require the operator bearer credential. CORS SHALL NOT make path-parameter or malformed path variants public or enable browser cookie credentials.

#### Scenario: Browser preflights an authorized submission
- **WHEN** a configured origin preflights POST on a canonical API path with only approved request headers
- **THEN** the API returns the exact allowed origin and preflight permission without requiring a bearer credential

#### Scenario: Allowed browser omits the credential
- **WHEN** a configured origin sends an actual API request without the bearer credential
- **THEN** the API returns 401 with the CORS origin response header and performs no repository access

#### Scenario: Reject unintended cross-origin access
- **WHEN** an origin, method, request header or raw path is outside the explicit policy, or no origins are configured
- **THEN** no cross-origin API permission is granted

### Requirement: Accept bounded authenticated synthetic jobs
The API SHALL accept only the versioned synthetic request contract with a configured operator credential, bounded body and Idempotency-Key. Every route except the exact minimal health path SHALL require that credential, including path-parameter or otherwise non-canonical spellings of API routes. It SHALL persist a new job and canonical request hash atomically. Same key and request SHALL return the existing job; same key and different request SHALL return a conflict.

#### Scenario: Retry a submission
- **WHEN** an authenticated operator repeats a valid POST with the same idempotency key and canonical body
- **THEN** the API returns the original run ID and does not enqueue another run

#### Scenario: Reject an unauthenticated path variant
- **WHEN** a client without the credential requests an API route spelled with a path parameter, such as `/api;x=1/v1/runs/{id}`
- **THEN** the API returns 401 before any repository access

### Requirement: Execute and publish only owned attempts
The worker SHALL claim queued or expired work using a lease and unique fencing token, execute at most one job concurrently, upload attempt-scoped artifacts with hashes, and publish completion only while its token owns the uncancelled run.

All owned state-changing writes SHALL require the matching current token and an unexpired database-time lease. An expired owner SHALL NOT renew, cancel, fail, release or publish its attempt; expiry recovery belongs to the claim transaction. An owned terminal transition SHALL roll back if its attempt row cannot be closed.

#### Scenario: Expired owner tries to end its attempt
- **WHEN** a worker retains the current token after its lease has expired and tries cancellation acknowledgement, failure or shutdown release
- **THEN** the run and attempt remain unchanged until the recovery sweep or a new claim handles them

### Requirement: Supervise bounded training independently
The worker SHALL execute training in a child process while its parent renews ownership and observes cancellation. The parent SHALL request cooperative stopping and terminate an unresponsive child within 30 seconds of observing lost ownership or cancellation. A two-hour monotonic attempt compute deadline SHALL terminate the child without requiring training cooperation. Loss of database access SHALL stop compute before the last confirmed lease expires. Every child SHALL be reaped before the worker moves to another attempt.

#### Scenario: Training ignores cancellation
- **WHEN** training does not respond to the parent's cooperative stop request
- **THEN** the parent terminates and reaps the child within the cancellation bound and publishes no completed artifacts

#### Scenario: Training ignores its time budget
- **WHEN** the attempt reaches its hard compute deadline
- **THEN** the parent terminates the child independently of epoch progress and cannot publish COMPLETE

### Requirement: Fence retained stopped checkpoints
After stopping and reaping training, the worker SHALL retain any available completed-epoch checkpoint as an immutable attempt-specific object, verify its readback SHA-256, and register the key/hash only while the matching run token and database lease remain valid. Lost ownership SHALL prevent checkpoint registration. This checkpoint registration SHALL NOT imply that durable service resume is implemented.

#### Scenario: Stop after a completed epoch
- **WHEN** a stopped child left a completed-epoch checkpoint and the parent still owns the cancellation-requested run under a valid lease
- **THEN** the parent registers the verified immutable checkpoint before acknowledging cancellation

#### Scenario: Worker dies after upload
- **WHEN** a worker uploads artifacts but dies before a conditional completion update
- **THEN** those objects do not appear as a completed result and a later valid attempt can recover the job

### Requirement: Support cancellation and readback
The API SHALL expose run status and idempotent cancellation. A queued run SHALL cancel immediately; a running run SHALL request cancellation and SHALL not later publish COMPLETE if cancellation wins. Completed runs SHALL expose their immutable manifest/report references.

#### Scenario: Cancel running work
- **WHEN** cancellation commits before a worker's completion update
- **THEN** the worker's stale or cancelled attempt cannot publish completion

#### Scenario: Read a completed manifest
- **WHEN** an authenticated operator requests the manifest of a COMPLETE run
- **THEN** the API returns the registered object only if its bytes match the registered SHA-256, and otherwise returns a stable error code without internal storage details

### Requirement: List runs newest first
The API SHALL list only the authenticated operator's runs, newest first, in pages of 1–50 items using an opaque-to-clients cursor, and SHALL reject an invalid limit or a cursor that does not name one of the operator's runs.

#### Scenario: Page through runs
- **WHEN** an operator with more runs than the page limit requests the next page with the returned cursor
- **THEN** the API returns the following older runs without repeating or skipping any

### Requirement: Stop the worker gracefully
On SIGTERM the worker SHALL stop claiming new work. A run it owns but has not started training SHALL return to the queue, or become FAILED when its attempts are exhausted, or CANCELLED when cancellation was requested. A run whose training already finished SHALL continue to conditional publication.

#### Scenario: Stop between claim and training
- **WHEN** the worker receives SIGTERM after claiming a run and before training starts
- **THEN** no artifact is published and the run becomes claimable again without waiting for lease expiry

### Requirement: Run standalone under Compose
After documented private prerequisites, Compose SHALL start the API, worker, PostgreSQL, Liquibase migration, LocalStack and bucket initializer without Kubernetes or manual bucket/schema creation.

#### Scenario: Start local stack
- **WHEN** the operator supplies the required private secrets and runs `docker compose up`
- **THEN** health checks, migration and bucket initialization reach readiness and one synthetic request can complete end to end

### Requirement: Close attempts when invalid recovered work fails
When recovery rejects an expired run because its stored request is invalid, the worker SHALL mark the run failed and close its previous unfinished attempt in the same transaction. It SHALL NOT create a new attempt for that invalid request.

#### Scenario: Expired running job has invalid stored request
- **WHEN** claim selects an expired RUNNING job whose stored request fails validation
- **THEN** the job becomes FAILED with invalid_request, its previous attempt has a finish time and failed outcome, and no new attempt is created
