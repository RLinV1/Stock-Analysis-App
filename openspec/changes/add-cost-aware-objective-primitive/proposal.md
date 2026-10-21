## Why

Approved A1 task3.7 requires a costs-in-loss versus evaluation-only experiment. Before selecting any training-window boundary policy, implement a small differentiable accounting/loss primitive with an explicitly supplied previous target. It reuses the current idealized target-turnover formula without silently enabling a cost-aware runner or claiming a study result.

## What Changes

- Add tensor-based net-return accounting with explicit prior target and finite 0..100bps cost, matching current evaluator arithmetic for initial cash.
- Add stabilized negative net-return Sharpe using the unchanged existing epsilon.
- Validate dimensions/dtypes/devices/long-only targets, finite returns and bankruptcy rather than silently converting/clipping.
- Add hand-calculated evaluator-equivalence, cross-window boundary, zero-cost loss/gradient and finite-difference gradient regression source.
- Keep every current runner/service/fold/sweep control on gross-return training with evaluation-only costs; boundary selection and actual paired study remain separate work.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `portfolio-research`: explicit cost-aware objective math prerequisite without enabling a new training method.

## Impact

Research tensor math, source tests and documentation only. No dependency, CLI/config/request schema, optimizer, training default, replay/worker/UI, historical conclusion or accepted boundary policy. No project import, tensor/model/test/GPU or process execution is authorized.
