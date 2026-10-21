## Why

Approved A1 task3.4 in define-product-and-stack requires a synthetic check with a known preferred allocation. Existing source checks gradients, accounting, determinism and recovery, but does not establish that the end-to-end runner learns a controlled allocation. Add a bounded future verification gate without running a model under the current file-only instruction.

## What Changes

- Construct a test-owned two-asset synthetic dataset with one constant positive-return asset and one constant negative-return asset, reversing their column positions in a second case.
- State the analytic gross-objective bound and distinguish its stabilized objective from the evaluator's undefined constant-return Sharpe.
- Exercise the actual chronological runner with explicit CPU-only fixture settings and a frozen 95% mean preferred-asset threshold on held-out dates.
- Retain normal run artifacts and compare against equal weight; record all checks as unrun until execution is authorized.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `portfolio-research`: add a bounded controlled learnability verification requirement.

## Impact

Research regression source and documentation only. No production loss, model, defaults, dataset acquisition, dependencies, service/UI behavior or historical claim changes. The test constants are fixture controls, not accepted research presets. No CLI, Python import, training, GPU, shell or test process is authorized for this continuation.
