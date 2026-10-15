## Why

A1 requires expanding 24-month walk-forward evaluation, but the existing runner only supports a fixed holdout. A tested fold planner and causal sample adapter can establish those boundaries without historical data or service startup.

## What Changes

- Add a pure date-based fold planner using observed trading dates, 24-calendar-month retraining and expanding prior history.
- Enforce lookback context, at least 252 training targets and validation of max(63, ceiling(10% of pre-test targets)); move an under-supported start forward with an explicit exclusion record or reject if impossible.
- Expose per-fold train/validation/test target indices and construct train-fitted samples restricted to that fold's end.
- Cover gaps/weekends, leap/month boundaries, insufficient history and future mutation/reordering attempts with synthetic tests.

## Capabilities

### New Capabilities
- `portfolio-research`: add the concrete fold-planning requirement alongside the same capability's non-overlapping active A0/A1 deltas.

### Modified Capabilities
None in current main specs.

## Impact

Research module/tests and documentation only; no dependency, A0 runner, CLI, trained-model or service behavior changes. Implements the fold-planning portion of define-product-and-stack tasks 3.1/3.2. Full A1 training, all baselines, historical tiers and replay remain separate tasks. These are engineering protocol defaults already specified in docs/SPEC.md, not recovered author settings.
