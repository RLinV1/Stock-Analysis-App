## Why

Approved A1 task3.5 calls for investigating input normalization rather than assuming it reproduces the paper. The current sampler always standardizes training inputs. Add an explicit local fixed-holdout raw-input control so a later declared experiment can compare the two methods, while preserving the existing service/fold path and making no empirical claim now.

## What Changes

- Add normalization mode `train-only` or `raw` to local RunConfig, preserving the existing train-only default and numerical path.
- Keep next-return alignment and chronological masks identical; raw mode retains identity-transform mean0/scale1 without fitting future data.
- Record mode in config/identity/model artifacts and describe its actual preprocessing deviation.
- Keep service requests explicitly on train-only normalization and reject raw direct-fold execution before runtime access; group/sweep configs do not gain a raw option.
- Add unrun sampler, local raw run/repeat/resume and rejection regression source. Do not run a normalization study or choose a preferred method.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `portfolio-research`: explicit bounded normalization diagnostic controls and auditable mode identity.

## Impact

Research sampler/runner, narrow service adapter pin, source tests and documentation. No new dependency, model/loss/cost/seed policy, accepted numeric default, request schema, worker routing, full A1 experiment result or historical claim. All implementation/verification is source-only under the user's no-project-process/GPU instruction.
