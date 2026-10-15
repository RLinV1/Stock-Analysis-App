# Readiness and milestone gates

Updated 2026-10-15. **The local research runner, bounded synthetic adapter, API/worker source and connected Android/web client have automated checks in their stated scopes.** The full stack has not passed runtime acceptance; LocalStack/S3 publication, Compose, completed-result integration and physical-device checks remain.

## Current evidence

Independent architecture and research reviews found no reason to replace the approved stack. Retained synthetic repeat and interrupted/resumed outputs matched exactly; [A0 evidence](A0-EVIDENCE.md) records measurements and limitations. The [UI plan](UI-DESIGN.md) adopts the supplied apple-design skill. Connected run/report/equity/allocations source has 91 passing mobile tests, clean TypeScript/lint and Android/web exports. Rendered light/dark/narrow/doubled-browser-text Results checks use fixtures. Java passes 76/76, including automatic startup/reopen and repository PostgreSQL cases; worker SQL passes 40/40 PostgreSQL cases. A real browser/API/PostgreSQL connect/list/submit/status/cancel smoke passes. [Evidence](evidence/mobile-web-2026-10-15/README.md) distinguishes these scopes; the [handoff](../openspec/HANDOFF.md) records detailed checks. No historical reproduction, service/client deployment, physical Android flow or ONNX parity has passed. Tailscale is disconnected and deferred.

Host observations from 2026-09-21, updated with bounded 2026-10-15 verification:

| Item | Observed | Required next |
|---|---|---|
| Python research | Python 3.12.14 / PyTorch 2.8.0+cpu; CPU smoke, 111 research tests, bounded local request, causal fold planning and retained repeat/resume checks pass | Historical seed/cost evidence and full dependency locks remain |
| Java | Java 21.0.2, Maven 3.9.10 and Spring Boot 4.1.1; current source/unit evidence in handoff includes authenticated list and artifact/result routes | Maintain Java 21 patch, lock transitive dependencies, verify full S3/worker result publication and Compose startup; shell PATH still selects Java 24 |
| Node/client | Node 22.23.2 installed and selected explicitly; fresh shells still select 22.12.0. Expo 57.0.27; connected client 91 tests/TypeScript/lint and Android/web exports pass; rendered fixture and bounded real API browser checks pass | Select supported Node in each shell; physical Android/TalkBack, full accessibility and real completed-result checks remain. npm advisories were accepted for local tooling use on 2026-10-12; recheck before release |
| Docker | Client 28.3.2 and Compose 2.38.2-desktop.1; engine and disposable PostgreSQL verified after explicit startup authorization | Images build and independent non-root migration/API/database restart/offline worker-child checks pass; full Compose/S3 remains open because LocalStack checks are excluded |
| LocalStack | User explicitly skipped LocalStack checks on 2026-10-15; no token/persistence verification | Retain S3/full Compose acceptance as open; do not enroll or request a token for independent local checks |
| Project identity | Updated 2026-09-23: local Git history exists and source-revision metadata/local repeat are implemented; complete transitive locks absent | Retain source snapshots and tested locks before third-party reproducibility claims |

Installed binaries and successful imports do not prove cross-service compatibility. Version choices and source references are in [TOOLCHAIN.md](TOOLCHAIN.md). Authorized local Docker/API/Expo startup and bounded dependency additions are documented in the active change records; no account enrollment or Tailscale reconnection occurred.

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

**Next concrete work:** continue worker lifecycle/recovery or A1 work after the independently verified container packaging/runtime slice. LocalStack checks are excluded by the user, so full Compose/publication acceptance remains open. Continue independently testable work while physical Android/private transport stays deferred. Implement retrievable inputs and executable v2 replay separately; the bounded request/local repeat do not satisfy that contract. Keep historical seed/cost comparison and physical Android checks open. Do not repeat broad stack review without new evidence.

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
