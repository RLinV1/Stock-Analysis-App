## Why

The approved A1 task3.11 remains unimplemented: the causal fold planner exists, but the runner trains only a fixed holdout. Connect those tested building blocks without changing the service's bounded A0 default or claiming historical reproduction.

## What Changes

- Add explicit fold-aware training with a frozen train-only scaler and validation-selected model retained for every fold.
- Add local walk-forward orchestration/CLI with requested/effective dates, retained fold identities and honest partial/failure state.
- Recompute continuous portfolio turnover/costs from stitched allocations rather than charging another initial position at each fold boundary.
- Support a one-observation final fold through explicit metric opt-in; preserve A0's two-observation default.
- Reject invalid scalar costs and nonfinite derived accounting explicitly while preserving ordinary finite accounting formulas.
- Retain the actual gross-return objective/stabilization and evaluation-only cost treatment in local identities/reports without changing the algorithm.
- Reject nonfinite objective moments explicitly so overflowing variance cannot appear as a finite zero training/validation loss; preserve ordinary loss arithmetic.
- Cover full future-mutation causality, retained model/scaler identities, costs across boundaries and unsupported local-repeat behavior.
- Snapshot validated preflight inputs into a fresh owned directory using the existing filename-only CSV contract, preserving partial evidence and protecting existing output.

## Capabilities

### New Capabilities

- `research-dataset-snapshots`: bind owned local copies to preflight manifest content, validate the copied dataset and reject invalid/colliding paths without replacing existing evidence.

### Modified Capabilities

- `portfolio-research`: execute frozen fold models and retain a continuous causal evaluation with explicit scope.

## Impact

Research runner/metrics, new local orchestration, CLI and tests/docs. No dependency upgrade, historical acquisition, new baseline estimator, service contract, worker routing, LocalStack, phone or v2 replay change. User-approved A1 scope authorizes implementation; proposed numerical defaults/licensing remain unresolved.
