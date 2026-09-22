# Portfolio Lab — technical specification

Version 0.2, corrected 2026-09-21. This is the **planned** technical contract. Only the A0 prototype listed in section 4 exists. New schema validation, worker orchestration and replay behavior require implementation and tests before being described as working.

## 1. Stack

Python/PyTorch research worker; Java 21/Spring Boot API; PostgreSQL/Liquibase; LocalStack S3; React Native/Expo/TypeScript client (physical Android first, web target); Docker Compose independently of Kubernetes; additional K3s path later. ONNX Runtime Java is the planned inference extension, conditional on parity tests. See [TOOLCHAIN.md](TOOLCHAIN.md) for installed versions versus candidates.

## 2. Architecture and durable jobs

API and worker communicate through a documented PostgreSQL job contract and immutable S3 artifacts. Java does not train; Python does not serve HTTP. Liquibase owns migrations. A PostgreSQL queue is the implementation default: it keeps job state and result registration in one transaction boundary without introducing another service.

Compose starts API, Python worker, PostgreSQL and LocalStack, with persistent volumes, health checks, migration/initialization ordering and bounded connection retries. LocalStack initialization creates required buckets idempotently. A synthetic job without live market data demonstrates the whole path. Database and S3 ports stay internal unless a development override explicitly exposes them.

Setup clarification: synthetic jobs need no live market feed, but the full stack is not guaranteed offline. Current LocalStack images require LOCALSTACK_AUTH_TOKEN and applicable plan access. Provision this privately before Compose startup; fail with a clear prerequisite message if missing. Do not commit tokens, auto-enroll in trials, or substitute an obsolete image to avoid authentication. Verify restart persistence with the selected image/plan; a mounted volume alone is not evidence of restored S3 state. Downloads and vendor authentication can require internet access.

Compose initialization uses healthy-service dependencies and a successful one-shot Liquibase migration before API/worker readiness. Applications still retry transient dependency failures after startup. On Windows use a Linux-container runtime. The later K3s path uses k3d on that runtime as a local implementation default; it does not require or replace Compose.

### Submission and lifecycle

- POST run/verification requests require an Idempotency-Key scoped to the authenticated operator. Persist its canonical request hash and job ID atomically. Same key/body returns the original ID; same key/different body returns 409. Keep the mapping for the run's retained lifetime.
- States: QUEUED -> RUNNING -> COMPLETE or FAILED. QUEUED can become CANCELLED immediately. RUNNING can become CANCEL_REQUESTED -> CANCELLED; a completed job cannot be retroactively cancelled.
- Claim using a short transaction with row locking and SKIP LOCKED; issue a unique attempt ID and monotonically increasing fencing token. Never hold a DB transaction throughout training.
- Default: one worker, one concurrent job, heartbeat every 10 seconds, lease 60 seconds, three total attempts, two-hour wall-clock limit per attempt. These are configurable bounded operational defaults; changes are recorded.
- Expired RUNNING leases requeue if attempts remain, otherwise fail. A CANCEL_REQUESTED expired lease becomes CANCELLED. Validation/model numerical errors are permanent; transient infrastructure errors may retry with bounded backoff.
- Worker checks cancellation between epochs and before publication. For unresponsive compute, terminate the child process within 30 seconds of observed cancellation; keep checkpoints but publish no completed result. Hard deadline enforcement must not depend on the training loop cooperating.
- Heartbeats, checkpoints and terminal DB writes require the current attempt/token. A worker that loses ownership stops; stale owners cannot complete or overwrite a run.
- A supervisor outside the training child polls cancellation and renews ownership independently. Database time governs lease expiry; all state-changing writes require both matching token and unexpired lease. A token alone is insufficient after expiry. On lost database access the supervisor stops work before its last confirmed lease expires; it cannot renew an expired lease. Attempt-specific immutable checkpoint objects are registered by a fenced database update.
- Resume only a completed-epoch checkpoint with matching code, data, configuration, environment and hashes. Otherwise fail explicitly; do not silently restart and report a successful resume.
- Write attempt-scoped objects under runs/{run_id}/attempts/{attempt_id}/. Upload all artifacts, verify hashes/readability, then atomically register the manifest and COMPLETE state with a conditional current-token/non-cancelled update.
- S3 and PostgreSQL do not share a transaction. A crash before DB commit leaves unreferenced objects, never a completed run. Retries use new attempt paths. Clean orphan objects only after lease expiry and a retention grace period; never delete registered artifacts.
- Completion and cancellation race through conditional DB transitions: whichever commits first wins. Failed runs expose sanitized errors and retained checkpoint availability.

Required tests: duplicate submission; key/body conflict; worker crash and lease expiry; stale-token publication rejected; upload-before-commit crash; cancellation versus completion; incompatible resume; API/worker restart with durable state intact.

## 3. Run manifest and verification

A0 uses its existing schema_version=1 local manifest. The following v2 contract is not wire-compatible; reject unsupported versions rather than guessing a migration. Implement a machine-validated JSON Schema and a CLI verifier in A1 before accepting external manifests; API verification reuses them in B.

Required groups (unknown fields rejected within each version):
- identity: schema version, run ID, created_at, method label, immutable input-identity digest.
- code: Git commit/dirty status when available; source snapshot SHA-256, dependency lock hash, Python/library versions, platform/device/determinism scope. Missing Git is explicit, never a fabricated commit.
- data: exact snapshot hashes, provider and retrieval time, adjustment recipe/version, source action hashes, access/redistribution notes, ordered asset identifiers/classes, date range and missing-data policy.
- features: ordered feature names/units, shape, lookback, price/return timing, normalization method and serialized preprocessing hash.
- configuration: objective/stabilization, optimizer settings, seeds, budgets, execution/cost convention, volatility policy and annualization.
- protocol: tier, training/validation/test dates for every fold, retrain schedule, common evaluation window and reasons for exclusions.
- artifacts: per-fold model, scaler and checkpoint identifiers/hashes; allocations, returns, report and parity-evidence hashes. Every fold has its own trained model/scaler. Identify the exact fold/model chosen for serving; never silently choose a file named latest.
- results: per-fold and aggregate metrics, same-condition baselines, null reasons, complete seed/cost results, deviations and limitations.

Only immutable inputs belong in the input-identity digest. Timestamps, elapsed time, metrics, run IDs and artifact locations are output metadata. Hash the actual consumed data and preprocessing, not just a provider label. A local content fingerprint proves identity but cannot supply missing source bytes to a third party.

### Verification semantics

Verification first validates schema, budgets, artifact identifiers and availability, then compares input identities, then reruns in the declared environment:
- UNVERIFIABLE: missing data/source/preprocessing, unsupported schema, unsafe or invalid request, or unavailable compatible runtime; return a specific reason, no MATCH.
- INPUT_MISMATCH: code/data/config/seed/environment differ; enumerate differences. Any exploratory rerun remains a separate experiment, even if its metrics happen to match.
- EXECUTION_FAILED: inputs are available and matched but replay fails or times out.
- MISMATCH: identical supported inputs replayed successfully, but a metric, evaluation date, strategy set or null reason disagrees.
- MATCH: matched inputs and successful replay with all required comparisons passing.

A dirty or non-Git tree is eligible only if its complete source snapshot and dependency lock are retained and retrievable; otherwise UNVERIFIABLE. Public reproduction releases should use clean commits plus snapshots. Existing A0 fingerprints alone do not meet this v2 replay contract.

Store comparisons and tolerances in the verification report:
- Counts, dates, ordering, config values, hashes, null presence and null reasons: exact.
- Weights, daily returns and metrics: abs(error) <= 1e-7 + 1e-5 * abs(reference).
- Both undefined with the same reason passes; undefined versus finite fails. JSON NaN/Infinity rejected.
- A looser research comparison (for example a paper's rounded Sharpe) is a labelled analysis, never v2 MATCH. Cross-hardware differences outside tolerance are reported, not silently relaxed.

ONNX parity is separate: identical ordered raw features through each model's recorded preprocessing, then PyTorch versus Java runtime; allocation absolute tolerance 1e-5, nonnegative weights and sum within 1e-5. Also compare portfolio metrics under the v2 metric tolerance. Test each exported fold's artifacts on fixed and held-out windows. Registration requires retained parity evidence and verified hashes, not a client-supplied boolean.

## 4. Implemented versus planned research

Existing modules:
- data.py: validated CSV manifests, synthetic fixtures, chronological windows and train-only standardization. No market-data fetching or corporate-action reconstruction.
- metrics.py: cumulative return, volatility, Sharpe, drawdown, turnover/costs, equal-weight and stock/bond baselines. No Sortino or complete paper baseline suite.
- model.py: LSTM/softmax allocator and stabilized negative Sharpe.
- runner.py: fixed holdout, validation selection, local artifacts and completed-epoch recovery.
- cli.py: synthetic/run commands.
- Three test modules; 17 passed in the review.

A0 remains owned by reproduce-portfolio-learning. A1 adds walk-forward, seven paper baselines, volatility scaling, tier/seed/cost experiments, the v2 schema and CLI verifier. B adds distributed jobs and HTTP replay. See [REPRODUCTION.md](REPRODUCTION.md) for current deviations.

### Causality and metric contract

Daily allocation is inference, not retraining. Within an A1 fold, the trained model and fitted preprocessing remain frozen while each trading day's trailing 50-observation input changes. Apply the resulting weights only to the following return. Retrain at 24-month fold boundaries using data available before that fold; record every model version and boundary. This is historical simulation, not an automatically scheduled live trading service. A0 currently uses one fixed train/validation/test split and does not implement two-year retraining.
Decision features end before the target return. Fit each fold's preprocessing only on training data; validation selects models, never test results. A fixed chronological holdout can be causal but is not the paper's walk-forward protocol.
All strategies use identical dates, assets and cost conventions within each comparison. Annual rebalancing versus constant daily target weights is an explicit research mode; reconcile it before claiming table agreement. Population standard deviation, 252 trading days and zero risk-free rate are defaults, not recovered author settings. Initial entry, terminal liquidation, weight drift, cash and leverage conventions must be recorded.
A1 must define Sortino/downside denominator, return threshold and zero-loss handling with hand-calculated fixtures before reporting those metrics. No undefined ratio is replaced with zero.

## 5. Canonical API and database contract

All routes are planned. JSON errors use application/problem+json with stable codes and no internal paths. Authentication is required for compute-triggering routes before network access. Paginate run lists; enforce bounded request sizes and numeric budgets.

| Route | Behavior |
|---|---|
| GET /api/v1/runs | Paginated status/config summary |
| GET /api/v1/runs/{id} | State, attempt, progress, sanitized error and result links |
| GET /api/v1/runs/{id}/manifest | Completed immutable manifest |
| GET /api/v1/runs/{id}/equity-curve | Model and baselines on common dates |
| GET /api/v1/runs/{id}/allocations | Ordered assets, raw/scaled weights with conventions |
| POST /api/v1/runs | Validated job; 202 with ID and Location; idempotent retry |
| POST /api/v1/runs/{id}/cancel | Idempotent cancellation request; report actual state |
| POST /api/v1/verify | Bounded asynchronous verification job, 202 and Location |
| GET /api/v1/verifications/{id} | Progress and input/metric comparison outcome |
| GET /api/v1/sweeps/{id} | All requested seeds/costs, including failed members |
| GET /api/v1/deviations | Versioned assumptions and evidence |
| GET /api/v1/models | Explicit registered model/fold versions |
| POST /api/v1/models/{id}/infer | B extension only; bounded input, validated parity |
| GET /actuator/health | Minimal service health |

Logical tables, finalized through Liquibase migrations and API schemas before implementation:
- run: UUID, kind, created_at, state, validated config/protocol JSON, seed, input digest, attempt counter, cancellation/deadline fields, current fencing token, completed manifest key/hash, sanitized error.
- run_attempt: run FK, attempt ID, fencing token, worker owner, heartbeat, lease expiry, start/end, checkpoint key/hash, failure classification. Unique token per run.
- submission: operator identity + idempotency key unique, canonical request hash, run FK.
- run_result: run FK + strategy + fold/aggregate scope unique; nullable metrics and null reasons.
- model_version: UUID, run/fold FK, model/scaler/feature-schema keys and hashes, parity report hash, registration time. No registration for unverified artifacts.
- sweep / sweep_run: config, requested seed/cost members, child run FKs.
- verification: request/run FK, reference input identity, status, comparisons and reasons.
- deviation: version, gap identifier, paper statement, choice, rationale, evidence link.

SQL constraints enforce legal identity/uniqueness; transactional transitions enforce state ownership. Publish complete API/JSON schemas before client integration. Liquibase changesets are append-only once applied; document rollback or forward recovery for destructive changes, never promise lossless rollback of data deletion.

## 6. Client and connectivity

Expo/TypeScript client: run list/detail, launch, comparison, provenance/verification. Confirm charts on Android and web before adopting a library. Shared source does not eliminate platform-specific testing.
Offline mode is read-only cached results with fetch timestamp. Disable submit/cancel/verify while offline; no automatic mutation replay. Network retries reuse the original idempotency key.
Tailscale is disconnected; phone enrollment/HTTPS comes later. Bind host published API port to loopback; container API listens on its container interface so Compose can reach it. Never expose PostgreSQL or LocalStack publicly. No public Funnel.

## 7. Required verification by milestone

A0: existing numerical/recovery tests plus measured CPU smoke and documented data-access outcome.
A1: fixed-answer metrics; fold boundaries; future-mutation invariance; known-answer synthetic learning; all baselines; seed/cost completeness; v2 schema rejection and replay outcomes.
B: Testcontainers integration and full Compose synthetic submit -> recover -> complete -> verify; failure scenarios in section 2.
B extension: Python/Java ONNX parity before inference registration.
C: Android and web components, cached-state labels, retry behavior and eventual physical-phone test.
D: same contract on K3s with worker restart/persistence evidence.

## 8. Numerical defaults and instrument tiers

Defaults are explicit engineering starting points, not an assertion of exact author behavior. Freeze choices before held-out evaluation; preserve post-hoc changes and all prior results.
- A0: 50-day window, 64-unit LSTM, Adam 0.001, batch 64, 100 epochs by default, train-only standardization, gross batch Sharpe, seed 7, cost 1bp.
- A1 initial sweep: seeds [7,13,42,101,2024], costs 1 and 10bp; chronological final 10% of pre-test targets for validation; expanding retraining every 24 months, reinitialize each fold.
- Rolling normalization, raw inputs, costs-in-loss and EWM decay are training/validation experiments. Paper volatility target 0.10 is not enabled in A0. EWM parameter, exposure cap and DWP definition remain research implementation decisions requiring explicit scope and tests before A1 completion.
- No assertion that a small seed spread or a static optimum proves or disproves the paper.

| Tier | Data proposal | Planned evaluation |
|---|---|---|
| 1 fidelity hypothesis | VTI/AGG/DBC plus raw VIX index, earliest common date on/after 2006-02-06 | First eligible trading date on/after 2011-01-01 through 2020-04-30; explicitly NOT INVESTABLE |
| 2 tradable extension | VTI/AGG/DBC plus VIXY throughout; data only from actual common availability in 2011 | First eligible trading date on/after 2013-01-01 through 2020-04-30 |
| 3 diagnostic | VTI/AGG/DBC | Same training/test dates as Tier 2 for paired comparison |

Use first/last available common trading dates within declared bounds; never synthesize pre-inception observations. Require lookback context plus at least 252 training targets and 63 validation targets for the first A1 fold; if unavailable move the test start forward and report it. Validation count is max(63, ceiling(10% of pre-test targets)); remaining training targets must meet the minimum.
Report full Tier 1 separately, and a matched-window Tier 1 rerun using Tier 2 training/test boundaries before comparing volatility sleeves. Instrument choice remains a deviation, not proof of author inputs.
VXX/VIXY splicing is removed from the default to avoid an unnecessary series break. A later extension must compound aligned daily returns into a rebased index and record overlap, switch date, fees and source hashes; never concatenate price levels.
Data provider and corporate-action recipe remain provisional until provenance/access tests are saved. See [data note](FINDING-DATA-SOURCING.md).

## 9. Remaining implementation decisions

A1 must resolve baseline estimators, EWM decay/exposure treatment and exact data access with recorded experiments. Public licensing is undecided. These do not block A0 synthetic development. Job and manifest defaults above are now planning requirements; they are not implemented by this document.
