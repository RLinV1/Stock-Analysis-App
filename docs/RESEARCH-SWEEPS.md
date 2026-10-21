# Explicit research sweeps (unverified source)

The pure planner and summary helpers in `research/src/portfolio_lab/sweep.py`
are a draft implementation of part of `add-explicit-research-sweeps`. They have
not been executed or validated. They do not launch training or authenticate
caller-supplied artifact claims. A standalone offline summary entry point is
also present as unverified source. Sequential training orchestration source exists
in `sweep_runner.py` and a standalone training entry point in `sweep_train_cli.py`;
neither is verified. There is no service route for sweeps.

Callers must provide every seed, every transaction cost, and a maximum candidate
count. There is no adopted seed list or cost grid. The planner preserves caller
order, rejects duplicate values and invalid types, and checks the entire grid
against the candidate budget before returning any work. This budget counts
seed/cost candidates; it is not a bound on epochs, walk-forward folds, or time.

Each requested candidate must have exactly one terminal record: `completed`,
`failed`, or `invalid`. Failed and invalid records require a reason and remain
visible in the output. Missing candidates, extra candidates, duplicates, and
running records prevent a complete summary. Complete coverage can include
failures; `all_successful` is reported separately.

Completed records contain `strategies`, including `lstm`, and a common `context`:

- `dataset_sha256`: a lowercase SHA-256 identifying the common dataset.
- `settings_sha256`: a lowercase SHA-256 identifying common experiment settings
  **excluding seed and cost**, which intentionally vary across candidates.
- `test_dates`: the same ordered, unique ISO calendar dates for every candidate.
- `method_label`: the same explicit research method label for every candidate.

The strategy set must match across completed candidates. Every strategy provides
the current evaluator metrics and an observation count matching the test dates.
Only Sharpe can be null, with a nonempty explanation; a numeric Sharpe must not
carry a null explanation. Nonfinite metrics and nonfinite derived comparisons
are rejected. Cumulative return must be at least -1, maximum drawdown must be in
[0,1], and volatility, turnover and cost must be nonnegative. Finite negative
Sharpe values remain valid. These are range checks, not proof that supplied
metrics were computed from authentic return paths.

Per-cost summaries include completed, failed, and invalid counts. Metric means,
population standard deviations, minima, and maxima use completed numeric values
only. Null Sharpe values have a separate count and explanation distribution;
they never become zero. A cost with no numeric result has null statistics.
An entirely failed grid has no invented strategy metrics or common context.

For each seed and baseline, the summary compares the LSTM's cumulative return
with that baseline at adjacent tested costs in ascending order. It reports a
tested tie, a sign change, no sign change, or an unavailable interval. A failed
middle cost is never skipped to compare its neighbors. These intervals are not
interpolated break-even estimates, significance tests, or claims of historical
performance. Different training seeds remain visible; no favorable seed is
selected.

The source regression cases cover arithmetic with fixed values, grid completeness,
null values, context drift, failed candidates, and numerical overflow. They are
unrun under the user's instruction to start no processes. Training orchestration
and child artifact checks now have source and stub regression cases, but actual
loader/training integration, CLI behavior, and validation remain open.

## Offline summary document

`portfolio_lab.sweep_cli` is an unverified standalone module for summarizing
supplied records. Its required arguments are `--input` and `--output`. Do not
run it until processes are permitted again. It starts no training itself.
The input is a JSON object with exactly three fields:

```json
{
  "schema_version": 1,
  "settings": {"seeds": [7], "costs_bps": [0], "max_runs": 1},
  "records": [
    {"seed": 7, "cost_bps": 0, "status": "failed", "reason": "training failed"}
  ]
}
```

This deliberately failed example illustrates a complete grid with no successful
run; it is a format example, not an adopted configuration or experimental result.
The shared loader rejects duplicate JSON fields, nonstandard `NaN`/infinity
constants and numeric float tokens that overflow finite representation. Owned
candidate artifacts and training completion status use the same parser policy.
The output parent must already exist, and an existing output is never replaced.
Validation and serialization happen before creating the output. An interrupted
or failed write can still leave a partial new file; consumers must parse and
validate it. A summary of supplied records does not authenticate their origin.
## Sequential executor source — unverified

`run_sweep` takes a dataset manifest, a complete `SweepModelConfig`, explicit
`SweepSettings`, and an output root. Common settings omit seed and cost; those
come exclusively from the declared candidate grid. The full candidate/fold plan
is checked before group creation. The group records both its candidate budget
and its planned number of fold runs. A candidate budget does not limit wall time.

The source copies one dataset snapshot for the sweep and passes it to sequential
walk-forward candidate groups. Every candidate has a persisted inventory entry.
Returned groups must match requested model settings, dataset manifest, source,
runtime, protocol, dates, method and conventions before contributing metrics.
The inventory retains hashes of the manifest, status and report bytes that were
parsed, alongside child paths. This is a local consistency check; it does not
provide external replay authentication or validate every model artifact.

The retained `objective` declaration describes the existing stabilized
gross-return loss, chronological training minibatches, full-validation selection
and variance epsilon. Transaction costs are applied only during evaluation.
Each requested grid cell still trains independently; the grid does not introduce
a cost penalty or model reuse. The unrun two-cost integration case is intended to
check model/scaler/history invariance for the same seed when only cost changes.

Ordinary execution errors are retained as `failed`; returned artifact validation
errors are `invalid`. Later requested candidates still run. A fully attempted grid
with failures has `completed_with_failures` status and `all_successful: false`.
An interruption retains completed/interrupted/pending inventory and produces no
complete summary. There is no sweep resume path. File-system failure while
persisting progress may prevent the latest status from being recorded; no crash
durability claim is made.

File-only inspection identified and corrected the report adapter: walk-forward
strategy entries contain nested `metrics` alongside returns and wealth. The
adapter extracts those metrics into sweep records and retains the full child
report by path and hash. Flat or malformed child strategy entries are rejected.
Completed fold counts, report context, and type-preserving manifest identity
must also match the requested candidate.

Runtime compatibility remains unverified. Orchestration stub cases and a small
actual-producer CPU integration case in `test_sweep_integration.py` are written
but unrun. Public-loader snapshot cases are also written and unrun. Lightweight
file reading/editing is authorized; tests, training, builds, services and GPU work
remain stopped while the user's separate GPU model is running.

## Training request source — unverified

The standalone `portfolio_lab.sweep_train_cli` module requires `--dataset`,
`--config`, and `--output`. Do not invoke it while the no-process instruction
stands. Unlike the offline summary module, invoking this entry point would train
the entire declared grid. Its config has exactly these top-level fields:

```json
{
  "schema_version": 1,
  "model": {
    "test_start": "2024-01-01",
    "test_end": "2024-01-03",
    "lookback": 10,
    "hidden_size": 8,
    "epochs": 1,
    "batch_size": 32,
    "learning_rate": 0.001,
    "device": "cpu"
  },
  "sweep": {"seeds": [7, 3], "costs_bps": [5, 0], "max_runs": 4}
}
```

These values illustrate the required format; they are not accepted project
defaults, a dataset-compatible recipe, or experimental evidence. Seed and cost
belong only in `sweep`; every common model setting must be supplied. Unknown and
missing fields are rejected. Dataset/protocol compatibility and full model
validation occur during executor preflight before the group is created.

The proposed command behavior prints the retained group directory and exits 0
for complete all-successful coverage, 1 for complete coverage with failed/invalid
candidates, and 2 for invalid input or inconsistent returned completion status.
Interruption is not success. The implementation and stub dispatch cases remain
unrun; actual end-to-end compatibility is still required.

## Baseline scope source — unverified

Sequential execution now checks each returned candidate against the learned
strategy and current baselines supported by the owned dataset asset roles. It
also checks the corresponding explicit omission declaration. A baseline missing
from every result cannot silently narrow the sweep's comparison scope. Returned
candidate roots must remain within the sweep before artifact reads. These guards
and their regression cases are source only and unrun; offline caller-supplied
summaries remain an unauthenticated separate contract.
