# Synthetic learnability implementation history

## Planned source-only gate — 2026-10-17

Read the current roadmap, A1 task3.4, portfolio-research spec, model objective and existing numerical/group test source. The known-allocation check is approved roadmap work; this change defines its narrow verification scope before implementation. All artifacts were written manually under the file-only constraint; no OpenSpec CLI validation ran. Implement only source and documentation, with no project imports, test/training/GPU/shell execution. Analytic constants, CPU fixture settings and thresholds are frozen in design.md before the first run.
## Controlled fixture and real-run gate source written — 2026-10-17

Added test_learnability.py with project-generated, serialized/public-loader two-asset fixtures in both preferred-column orderings. Analytic cases check rounding, constant-mixture losses, the stabilized optimum and varying weights. Real CPU runner cases freeze the design's settings/thresholds, use chronological validation selection and held-out allocations, compare equal weight, and require ordinary model/checkpoint evidence. Added a source guide with the exact constants, limitations and deferred verification. No project import, test/model/GPU/process execution occurred. Source assertions do not establish that either learning gate passes. All tasks remain unchecked.
## Planned explicit normalization fixture pin — 2026-10-17

The new local normalization control adds a configurable RunConfig field after this gate was authored. Before any execution, explicitly freeze the gate to its original train-only preprocessing in config/design/guide rather than relying on an implicit default. All other fixture settings/thresholds remain unchanged. This records intended existing semantics; no model/test/process will run.
## Normalization fixture pin source written — 2026-10-17

The controlled runner gate now explicitly passes/asserts train-only normalization; design and source guide record that setting. No thresholds, data, optimizer or split controls changed, and no held-out result exists to tune against. Source only; all gates remain unrun and unchecked.
## Objective-window fixture pin source written — 2026-10-17

The newly configurable local objective window is explicitly pinned to the gate's original minibatch method in config/assertion/design/guide. Its batch128 already contains all71 training targets, so the intended original computation is unchanged by design. No thresholds or optimizer budgets were tuned; no run/test/import/GPU work occurred. The gate remains unverified.
