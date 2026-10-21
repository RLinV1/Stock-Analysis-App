## Context

The local allocator uses long-only softmax weights and the recorded stabilized gross-return objective. Existing tests cover finite gradients but not learnability through the real data/scaler/train/validation/held-out path. A1 task3.4 is approved; empirical verification is currently prohibited.

## Decisions

- Use 120 synthetic daily calendar observations, two declared other-role assets and exact ideal daily returns +0.002 and -0.001. Write/read through the existing dataset contract, retaining explicit synthetic provenance and rounding limitations.
- For ideal targets, every long-only gross return is at most +0.002. The stabilized denominator is at least sqrt(existing variance epsilon), so the minimum loss is -0.002/sqrt(epsilon), attained by the preferred asset on every row. This bound is about the implemented stabilized loss, not a finite conventional Sharpe for constant returns.
- Reverse asset order to detect a hard-coded preferred column. Use explicit fixed fixture settings: lookback5, hidden_size8, epochs64, full training batch128, learning_rate0.02, seed19, evaluation cost0, deviceCPU, train-only normalization and minibatch objective control. These are test controls, not proposed project defaults; this fixture's minibatch contains every training target.
- Use actual run_experiment, its train-only scaler and validation-selected model. Before execution freeze mean held-out preferred weight >=0.95, validation loss <=-18 and cumulative return above equal weight. Check both orderings independently; do not discard an unfavorable result or tune held-out thresholds afterward.
- Keep analytic/fixture checks separate from the actual learning gate so failures can distinguish invalid construction from optimization/selection issues. Save normal immutable run evidence in test-owned temporary directories.

## Risks and limitations

This deliberately easy signal is a wiring/learnability check, not a market model or demonstration of useful prediction. Numerical CSV rounding means serialized returns approximate the ideal constants. No runtime pass, memory/time measurement, historical generalization or research conclusion is available. If the frozen gate fails, record it and investigate rather than weakening the acceptance threshold silently.
