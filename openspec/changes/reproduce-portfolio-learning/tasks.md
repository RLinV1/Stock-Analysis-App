## 1. Research contract and environment

- [x] 1.1 Audit paper data, VIX mapping, objective, costs, and evaluation assumptions; deliver a reproduction/deviation matrix with sources and an explicit unresolved-data label where necessary.
- [x] 1.2 Create an isolated Python research module with pinned compatible numerical dependencies; verify a CPU import/tensor smoke command and record versions without changing global Python.
- [x] 1.3 Define dataset/run manifests and synthetic fixtures; verify checksum validation, duplicate timestamps, nonfinite values, invalid prices, and missing-data policy handling.

## 2. Numerical implementation

- [x] 2.1 Implement chronological windows and lagged return alignment; verify known-date fixtures, disjoint target splits, train-only preprocessing, and future-mutation invariance.
- [x] 2.2 Implement equal-weight and fixed stock/bond baselines plus disclosed turnover/cost accounting; verify returns and drawdown against hand-calculated examples and unsupported-universe errors.
- [x] 2.3 Implement the 64-unit single-layer LSTM with allocation constraints and stabilized negative-Sharpe objective; verify finite gradients, normalized nonnegative weights, and zero-variance handling.
- [x] 2.4 Implement seeded bounded training, validation-only selection, and held-out reporting; verify test data cannot affect preprocessing, tuning, or fitted weights.

## 3. Reproducibility and recovery

- [x] 3.1 Save immutable manifests, configuration, versions, allocations, returns, metrics, model artifacts, and checkpoints; verify round-trip loading and distinct run outputs without overwrite.
- [x] 3.2 Restore model, optimizer, progress, and random state from completed-epoch checkpoints; verify interrupted/resumed CPU training against an uninterrupted run within a declared tolerance and reject incompatible checkpoints.
- [x] 3.3 Run the small CPU end-to-end fixture and record runtime and memory-measurement availability; optionally verify CUDA separately, explicitly recording skips and avoiding unsupported GPU claims.
- [x] 3.4 Repeat a saved A0 experiment on matching inputs/settings and report numerical differences under a documented same-environment tolerance, satisfying the existing repeat-experiment spec scenario. Checkpoint-resume equivalence alone is insufficient; full v2 third-party verification remains A1 scope.
- [x] 3.5 Verify local repeat rejects unsupported/incomplete/changed inputs before training, detects changed results including allocation/date/null differences, retains comparison failures, and preserves original artifacts.

## 4. Historical evidence and handoff

- [x] 4.1 Run a bounded chronological historical comparison if a documented dataset is available; otherwise deliver the data-access limitation and synthetic-only report without declaring historical reproduction complete.
- [ ] 4.2 Repeat available historical experiments across a declared small seed set and costs; deliver baseline comparisons, limitations, and measured results without selecting only favorable runs.
- [x] 4.3 Document execution commands and update implementation.md and HANDOFF.md after each logical change; verify referenced artifacts and reported task status against actual outputs.
- [x] 4.4 Run strict OpenSpec validation and applicable numerical/integration checks; archive only when required work is complete, preserving unfulfilled historical tasks if data remains unavailable.

## 5. Final-readiness cleanup — 2026-09-21

- [x] 5.1 Declare filelock in runtime dependencies and CPU requirements at the already installed version; correct the CLI's stale Quarkus reference. Verify dependency declarations, installed consistency and CLI startup without upgrading packages or changing numerical behavior.
- [x] 5.2 Reconcile Python/PyTorch approval and the raw-row validation default in the A0 planning and reproduction documents; record remaining evidence and replay gaps explicitly.

Scope/rationale: final independent review found a direct dependency supplied only transitively, obsolete stack wording, and a target-versus-row description mismatch. This cleanup makes the existing prototype accurately documented and packaged; it does not complete the broader A0 tasks.
