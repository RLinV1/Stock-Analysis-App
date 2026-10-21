# Explicit objective-window diagnostic controls

Status 2026-10-17: **unrun source only**. Control wiring and regression cases have
not been imported, executed or tested. No comparison, preferred method, measured
resource claim or completed A1 study is available. See the
[active tasks](../openspec/changes/add-explicit-sharpe-window-diagnostic/tasks.md)
and [implementation history](../openspec/changes/add-explicit-sharpe-window-diagnostic/implementation.md).

Local fixed-holdout RunConfig now records `objective_window`:

| Value | Training objective and updates |
|---|---|
| `minibatch` | Existing chronological minibatches, one update each; a final one-target remainder is merged into the preceding batch |
| `full-training` | One objective/update over all training targets each epoch, regardless of configured minibatch size |

Both use the existing stabilized negative gross-return Sharpe formula and epsilon.
Validation selection still uses all validation targets. `batch_size` continues to
control prediction/validation inference batching in both modes. Transaction costs
remain evaluation-only. Full-training retains a full training graph and may need
more memory; it is not gradient accumulation or a resource-saving implementation.

The shared loss now rejects a nonfinite mean, variance or final loss. Its ordinary
formula remains unchanged by design; numerical/gradient compatibility is unrun.
Preserving the default training schedule does not preserve malformed-input
acceptance or make artifacts from earlier source compatible with current identity
and resume/repeat checks.

The existing local `portfolio-lab run DATASET --config SETTINGS --output OUTPUT`
path reads this RunConfig field. There is no new CLI flag, request/sweep option,
accepted research preset or automatic paired study. The selected control and
actual objective scope are retained in config/identity/model/report metadata.
History records `optimizer_steps` for each epoch, and a changed-window resume
must reject while preserving evidence. Current-source local repeat validates
the actual configured objective declaration. These behaviors are unverified.

Service, walk-forward and sweep execution retain the current minibatch method;
the service/fold config adapters are explicitly pinned. Direct full-training
fold calls reject before dataset/device/training access. Local fixed-holdout
controls can combine with either [declared normalization mode](NORMALIZATION-DIAGNOSTIC.md).
The [known-allocation gate](SYNTHETIC-LEARNABILITY.md) explicitly keeps its original
minibatch control; its fixture batch already contains every training target.

Changing objective windows generally changes the optimizer updates per epoch.
That is a protocol difference to disclose, not an isolated batch-size experiment.
Even at fixed weights, mean minibatch Sharpe need not equal full-window Sharpe.
Before a later paired study, freeze data, normalization, seeds, budgets, update
accounting and validation/held-out protocol; retain all failures and outcomes
without held-out tuning or claims about the authors' unknown implementation.

After explicit execution authorization, run the hand-calculated distinction,
single-batch equivalence, small-batch update counts, metadata/no-runtime guards
and actual default/raw repeat/resume gates, then full compatibility and OpenSpec
checks. The controls alone do not complete the empirical study.
