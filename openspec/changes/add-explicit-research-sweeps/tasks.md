## Source status — 2026-10-17

Planner, summaries, standalone offline summary/training entry points, sequential
executor and regression source are written. None has been run. Actual final
walk-forward report compatibility, real-loader/training integration and artifact
checks remain unverified. The user explicitly authorized the lightweight file-reading
helper; project tests/imports/training/builds/services remain stopped, and GPU work
is excluded while a separate model is running. The earlier inspection rejection
is resolved only for authorized file reading/editing.

## 1. Explicit planning and pure summaries

- [ ] 1.1 Verify strict caller-declared candidate planning and complete terminal coverage, including duplicate/boolean/budget/coverage regressions; source is written, checks unrun. Update implementation/handoff immediately with evidence and limitations.
- [ ] 1.2 Verify metric domains, null-aware descriptive statistics and tested-point cost comparisons using fixed-answer means/spread, failure/null counts, domain boundaries and unavailable intervals; source is written, checks unrun. Do not select favorable seeds or interpolate thresholds.
- [ ] 1.3 Require ordered list/tuple axes and budget checks before copying inputs. Lazy/unordered/no-copy rejection source cases are written 2026-10-17; verify only after execution authorization.

## 2. Local execution and evidence

- [ ] 2.1 Verify the sequential snapshot-bound executor with actual final walk-forward reports and real-loader synthetic runs. Source/stubs cover nested metric extraction, strict JSON/typed identity, objective/cost declarations, fold counts, parsed-byte hashes, mutation, failures and interruption. The unrun CPU integration case also checks same-seed model/scaler/history invariance under cost-only changes.
- [ ] 2.2 Verify standalone training CLI dispatch, explicit configuration, honest exit status and bounded real-loader synthetic integration. Source/docs/stub cases are written. Retain historical/default/replay limitations.
- [ ] 2.3 Validate the standalone offline summary contract, shared strict JSON input/artifact/status parsing (including exponent overflow), failure coverage and preservation of existing output; source and regression cases are written but unrun.
- [ ] 2.4 Check expected dataset-role baseline coverage/omissions for every returned candidate and root ownership before artifact reads. Missing/extra baseline, omission, available 60/40 and escaped-root regression source is written 2026-10-17; execute after authorization.

## 3. Verification and history

- [ ] 3.1 After authorization, run relevant/full regressions, strict OpenSpec validation and link checks; reconcile evidence, implementation and handoff, then commit locally. Sync/archive only after all required implementation and verification are complete. Do not push.
