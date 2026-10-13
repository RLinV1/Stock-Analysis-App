# Readiness and milestone gates

Updated 2026-10-11. **The local research runner, bounded synthetic request adapter and Android/web client preview are implemented and tested in their stated scopes.** The full application is not yet runnable; service/container work, live client integration and their acceptance tests remain.

## Current evidence

Independent architecture and research reviews found no reason to replace the approved stack. The current Python suite passed all 74 tests in 40.35 seconds, including 15 bounded synthetic-request checks. Retained synthetic repeat and interrupted/resumed outputs matched exactly; [A0 evidence](A0-EVIDENCE.md) records measurements and limitations. The [UI plan](UI-DESIGN.md) adopts the supplied apple-design skill; the preview has 13 passing component tests (2026-10-13), earlier web/Android exports and a dark web visual review at desktop and phone width. No historical reproduction, service/client deployment, physical Android flow or ONNX parity has been verified. Tailscale is disconnected and deferred.

Read-only host checks on 2026-09-21:

| Item | Observed | Required next |
|---|---|---|
| Python research | Python 3.12.14 / PyTorch 2.8.0+cpu; CPU smoke, 74 tests, bounded local request and retained repeat/resume checks pass | Historical seed/cost evidence and full dependency locks remain |
| Java | Java 21.0.2, Maven 3.9.10 and Spring Boot 4.1.1 source; six contract/MVC tests pass against the Python fixture and HTTP controls | Maintain Java 21 patch, lock transitive dependencies, run PostgreSQL migration/state and live API checks; shell PATH still selects Java 24 |
| Node/client | Node 22.23.2 installed and used explicitly; fresh shells still select 22.12.0. Expo 57.0.27 client, 13 tests and earlier Android/web exports pass | Select supported Node in each shell; physical Android, light theme, browser accessibility and live API checks remain. npm audit advisories (35, four root packages, all build/test tooling) triaged 2026-10-12 as accepted for local use; recheck on Expo upgrades and before release |
| Docker | Client 28.3.2 and Compose 2.38.2-desktop.1 installed; desktop-linux engine pipe unavailable even in elevated inspection | Start Docker Desktop's Linux engine and verify container access when implementing Compose |
| LocalStack | No account/token or S3 persistence check performed in this review | Configure a private token and verify selected image/plan behavior before the Compose demo |
| Project identity | Updated 2026-09-23: local Git history exists and source-revision metadata/local repeat are implemented; complete transitive locks absent | Retain source snapshots and tested locks before third-party reproducibility claims |

Installed binaries and successful imports do not prove cross-service compatibility. Version choices and source references are in [TOOLCHAIN.md](TOOLCHAIN.md). No dependency upgrade, service startup, account setup or network reconnection was performed by this review.

## Gates apply to the action they protect

| Action | Required beforehand | Does not block unrelated work |
|---|---|---|
| Continue A0 local numerical work | Isolated environment, synthetic fixtures, documented scope and tests | No phone, JDK, public license or author-data resolution needed |
| Claim a historical result | Provenance/access notes, validated adjustments, causal evaluation, comparable baselines, reproducible outputs | Missing data allows explicitly synthetic-only progress |
| Complete A0 | Its existing OpenSpec tasks, CPU measurements and documented historical availability outcome | Does not require full A1 |
| Complete A1 research | Walk-forward, seven baselines, explicit tiers, seeds/costs, deviations, executable v2 schema and CLI verification | No API or UI needed |
| Install/upgrade dependencies | Package-specific trusted indexes, full lock/hashes and clean-environment test | Version existence alone is insufficient |
| Expose B compute over a network | Validated bounded requests, authentication, job limits/recovery, safe artifact handling | Can implement/test locally first |
| Serve ONNX inference | Per-fold preprocessing/model hashes and Python/Java parity | Does not block results-only API |
| Connect phone | Working API plus private HTTPS/access policy and Android test | Deferred at user's request |
| Publish repo/results | Chosen code license, secret/data scans, artifact-specific permissions and substantiated claims | Not a prerequisite for synthetic code |
| Deploy K3s | Compose demonstration and equivalent persistence/recovery checks | Public or paid deployment needs separate authorization |

## Next implementation steps

The sequence below stages existing milestone requirements; it does not mark a partial milestone complete or remove the fuller A1 research plan.

| Step | Deliverable | Acceptance evidence |
|---|---|---|
| 1. Bounded research runner (A0) | One PC experiment with the LSTM, equal-weight and 60/40 comparisons | Causal/numerical tests; saved report, inputs, runtime and memory; interrupted/resumed equivalence; saved-run comparison; bounded historical evidence or explicit data limitation |
| 2. Shared contract | Versioned requests, dataset/run schemas, locked environment and retrievable source/data identities | Valid/invalid fixtures; artifact hash checks; supported replay comparison; reject unsupported schema versions. This stages the necessary A1 contract work before B. |
| 3. First service slice (B) | Spring API + Python worker + Postgres/Liquibase + LocalStack under standalone Compose | One-command startup after prerequisites; submit/status/result works; duplicate requests retain one job; killed worker recovers; stale completion rejected; cancellation bounded; DB/S3 restart persistence verified |
| 4. First Android slice (C) | Choose an experiment, start it, monitor progress and compare allocations/equity/metrics with both baselines | Results agree with saved artifacts; errors/cached state visible; offline mutations disabled; physical phone/private access test when resumed; web render checks before full C completion |
| 5. Full research and app scope (A1/B/C) | Daily decisions with 24-month walk-forward retraining, all seven baselines, tier and seed/cost comparisons, deviations and verification workflows | Complete A1 checklist below and remaining API/client stories; include negative findings and failures; no held-out tuning |
| 6. Deployment and demonstration (D) | Additional k3d/K3s path, measured recovery demo and resume evidence | Repeat equivalent migrations, state/artifact persistence and recovery checks in K3s; document resource usage and delivered behavior |

ONNX export/Java inference follows per-fold parity validation and is not needed to view completed experiments. Tailscale remains deferred until the phone milestone. All services run on this PC; the Android app is installed separately. Later paid/public deployment or publication choices are not prerequisites to local implementation.

**Next concrete work:** lock the service environment and implement the Spring/PostgreSQL/Python/LocalStack Compose slice. The 74-test research suite and local request CLI pass, but the request adapter does not satisfy the planned v2 replay contract or cross-language job contract. Keep historical seed/cost comparison open in reproduce-portfolio-learning and physical Android checks open for the client. Do not repeat broad stack review without new evidence.

A1 experiments must freeze choices before viewing test outcomes. The annual-rebalancing discrepancy blocks attributing a specific implementation to the paper, not unrelated source development. Normalization experiments belong to training/validation, with all choices recorded.

## A1 completion checklist

- [ ] Walk-forward folds, minimum history and causality tests
- [ ] Seven baselines with documented estimator and execution conventions
- [ ] Tier 1 result with discrepancy analysis; no requirement to force a numerical match
- [ ] Tier 2/3 and matched-window comparisons, or explicitly scoped inaccessible-data limitation
- [ ] Complete seed/cost results, including failures and undefined metrics
- [ ] Versioned schema and CLI verification round trip under SPEC outcomes
- [ ] Evidence for every claimed measurement and unresolved assumptions labelled
- [ ] Artifact-specific publication checks before public release

Unfinished or inaccessible work is not marked complete. Resume wording follows the milestone actually delivered.
