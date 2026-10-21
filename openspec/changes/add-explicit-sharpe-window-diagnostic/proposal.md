## Why

Approved A1 task3.6 calls for a Sharpe-window experiment. Current local training computes stabilized gross-return Sharpe independently within each chronological minibatch. Add an explicit fixed-holdout full-training-window control without selecting a method or running an experiment under the user's file-only constraint.

## What Changes

- Add local RunConfig objective_window choices minibatch/full-training, preserving the current minibatch default and operations.
- Full-training mode performs one update per epoch using all training targets; validation selection still uses all validation targets.
- Bind the actual window/scope to identity/report/model metadata and retain optimizer-step counts in history.
- Keep service/group/direct-fold execution explicitly on the current minibatch method; do not expand request or sweep schemas.
- Add unrun arithmetic/control/artifact/repeat/resume regression source and document study confounds/limitations.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `portfolio-research`: explicit local objective-window diagnostic controls and auditable update scope.

## Impact

Local research model metadata/runner/repeat, narrow fixed service/fold pins, regression source and documentation. No new dependency, loss formula/stabilization, seed/cost preset, cost-aware objective, historical finding or preferred window. No project import, model/test/CLI/GPU/service process is authorized.
