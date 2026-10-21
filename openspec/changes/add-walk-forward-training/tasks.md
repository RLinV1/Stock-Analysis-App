## 1. Fold evaluation prerequisite

- [ ] 1.1 Add explicit one-observation metric opt-in, preserving default rejection and invalid-input guards; verify hand-calculated cost/wealth/null-Sharpe cases and existing metrics tests, then update implementation/handoff immediately.
- [ ] 1.2 Invalid scalar cost, complex/unrepresentable matrix and nonfinite derived result rejection source/regression cases written 2026-10-16; run numerical/A0 compatibility checks only after authorization. No cases have run.

## 2. Frozen fold execution

- [ ] 2.1 Add validated fold context to runner samples, identity/checkpoint and retained model/scaler metadata; verify shared strict group/direct-call preflight, default A0 regression, split mismatch, short final fold and future-mutation model/scaler invariance. Source cases forbidding runtime/device access on invalid direct calls are written but unrun.
- [ ] 2.2 Guard existing A0 local repeat against unsupported fold/group references before training; verify a retained unavailable comparison and zero training calls.
- [ ] 2.3 Verify retained objective/stabilization/evaluation-only-cost metadata, hand-calculated loss and run/resume/fold/repeat consistency. Shared A0 identity fields, strict reference preflight and zero-tolerance metadata comparisons are written with regression source, all unrun; the algorithm/epsilon and ordinary numeric output tolerance remain unchanged by design.
- [ ] 2.4 Verify finite retained repeat diagnostics: exact large integers, mixed numeric types, overflowing differences with null maximum, and reference observation counts matching dates. Source/regression cases written 2026-10-17; all unrun.
- [ ] 2.5 Validate actual saved resume identity/schema/protocol/method/conventions and strict manifest/status JSON before training, preserving evidence on rejection. Stale-digest/typed/ambiguous-control source cases are written 2026-10-17; run current A0/fold resume compatibility after authorization.
- [ ] 2.6 Reject nonfinite objective moments/final loss through a shared stabilized-loss guard, preserving ordinary value/gradient arithmetic; add gross/net overflow and equality source cases, then run after authorization.

## 3. Continuous local orchestration

- [ ] 3.1 Add immutable local group plan/config and sequential fold execution with retained partial/failure state; verify owned child boundaries before reads, strict JSON/typed artifact context, dataset-derived baseline omissions, captured-byte hashes, relative-root references, explicit multi-fold runs/model hashes and no false completion. Guard/regression source is written but unrun.
- [ ] 3.2 Stitch allocations/returns chronologically and recompute continuous costs/wealth; verify exact date coverage and hand-calculated boundary turnover without repeated cash entry.
- [ ] 3.4 Avoid rebuilding training windows during aggregation; verify direct owned-price target returns exactly match existing float32 fold targets, including one-target folds, with feature construction forbidden. Preserve aggregate/child gross-return agreement. Source/regressions written 2026-10-17; all unrun.
- [ ] 3.3 Expose an explicit local CLI and document run/evidence commands; execute a bounded synthetic CLI smoke and preserve A0/service defaults.
- [ ] 3.5 Reconcile complete owned-fold report accounting against allocations/owned returns before accepting a fold. Model-free valid/tampered nested-result regression source is written 2026-10-17; run it and actual runner/group compatibility after authorization. No external/model replay claim.

## 4. Verification and history

- [ ] 4.1 Run relevant/full research regressions and end-to-end future-mutation checks; reconcile requirements/context and implementation/handoff after every logical change.
- [ ] 4.2 Validate OpenSpec and links, sync completed deltas and archive only after all required scope/verification is complete, preserving partial/failure history and historical/replay limitations.
- [ ] Supplemental snapshot gate: shared fresh-directory dataset copying and mutation/path/collision/existing-directory regression source written 2026-10-16, including Windows aliases; verify it with the real loader and full group after process authorization. Verify oversized numeric configuration rejection too. No checks run.
