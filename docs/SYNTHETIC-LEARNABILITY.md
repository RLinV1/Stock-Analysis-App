# Synthetic learnability source gate

Status 2026-10-17: **unrun source only**. No model, test, project import or GPU
operation was started. This does not complete A1 task3.4 or establish learning
quality on market data. See the [active change](../openspec/changes/add-synthetic-learnability-gate/tasks.md)
and [implementation history](../openspec/changes/add-synthetic-learnability-gate/implementation.md).

The future gate uses the actual local runner with two deliberately artificial
assets. One has ideal constant daily return +0.002, the other -0.001; both column
orderings are tested. Dataset files disclose their generated provenance, calendar
days and CSV rounding. There is no historical acquisition or accepted preset.

For this ideal fixture every long-only gross return is at most +0.002. The
implemented stabilized loss has denominator at least `sqrt(variance_epsilon)`;
its minimum is `-0.002 / sqrt(variance_epsilon)`, attained by allocating fully to
the preferred asset on every row. This is a bound for the recorded stabilized
objective. Conventional zero-volatility Sharpe remains undefined.

That analytical bound describes the ideal constant-return array. Serialized CSV
prices approximate it; a separate source case checks the recovered returns
against the ideal path before the runner gates. Neither the analytical statement
nor the presence of these assertions establishes a measured training outcome.

The source freezes these controls before the first run:

| Control | Fixture value |
|---|---|
| Observations | 120 synthetic calendar days |
| Train / validation endpoints | Rows75 / 95, zero-based |
| Held-out targets | Rows96 through119 |
| Lookback / hidden size | 5 / 8 |
| Epochs / batch size | 64 / 128, full training batch |
| Learning rate / seed | 0.02 / 19 |
| Device / evaluation cost | CPU / 0bps |
| Normalization | Explicit train-only standardization |
| Objective window | Explicit minibatch control; this fixture has one training batch |
| Held-out preferred mean weight | At least0.95 |
| Best validation loss | At most-18 |
| Comparison | Held-out cumulative return exceeds equal weight |

Analytic/fixture cases precede the real-run gates. Both orderings must be reported;
an unfavorable case must not be discarded or the threshold silently weakened.
Ordinary dataset, scaler, model, checkpoint, manifest, history and allocation
artifacts remain in test-owned temporary run directories.

After process execution is explicitly authorized, run the focused
`research/tests/test_learnability.py` suite in the configured Python3.12 CPU
environment, then relevant/full compatibility and OpenSpec checks. Record actual
outcomes before checking tasks off. Even a passing result would demonstrate only
this easy pipeline check, not historical prediction or paper reproduction.
