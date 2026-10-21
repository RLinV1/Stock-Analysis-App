# Walk-forward source draft

Status 2026-10-17: this implementation and its tests were written under a **code-only, no-process instruction**. They have not been imported, run, tested or built. The archived causal planner has earlier evidence; that evidence does not validate this new runner/orchestration source. Do not claim trained walk-forward models, historical findings or replay support from this draft.

The draft adds optional validated fold context to the existing runner and a separate local group command. Each fold uses prior training/validation targets, a train-only scaler and a validation-selected model frozen during evaluation. Every selected model/scaler, child manifest/report hash and planned date is retained. The aggregate recomputes one continuous account from recorded allocations/returns, preserving target turnover across fold boundaries rather than resetting from cash each time.

The proposed local entry point is `portfolio-lab walk-forward DATASET --config SETTINGS --output OUTPUT`. It requires a complete configuration object; no new project defaults are accepted implicitly. Example explicit **synthetic verification settings**, not a research recommendation:

```json
{
  "test_start": "2015-01-01",
  "test_end": "2018-12-31",
  "lookback": 10,
  "hidden_size": 8,
  "epochs": 1,
  "batch_size": 64,
  "learning_rate": 0.001,
  "seed": 7,
  "cost_bps": 1,
  "device": "cpu"
}
```

Use dates supported by the actual validated dataset. The planner records any effective-start shift needed for its minimum history. The new source supports a one-target final fold through explicit metric opt-in; default A0 evaluation keeps its two-target minimum. Undefined Sharpe retains its reason.

Draft regression coverage includes hand-calculated boundary fees, exact planned coverage, model/scaler retention, later-fold failure evidence, local-repeat rejection, strict configuration guards, on-disk future-price mutation and snapshot isolation. All are unrun. Existing A0/service commands remain the intended defaults; this draft does not route the worker through multi-fold training.

Group-level resume, external v2 replay, the full paper baseline suite, historical acquisition/tier/seed/cost studies, service/UI integration and physical-device acceptance remain separate work. Prior A0/container evidence records prior source; these edits change the research fingerprint. See the [active tasks](../openspec/changes/add-walk-forward-training/tasks.md) and [implementation history](../openspec/changes/add-walk-forward-training/implementation.md). Resume verification only after process execution is authorized.
## Snapshot source continuation — 2026-10-16

The unverified group source now uses a shared dataset snapshot helper. It requires
a fresh destination, retains exact manifest bytes, compares manifest content with
the validated preflight inputs, copies only the declared CSV filename alongside the manifest, and validates
the copied data before training. A changed source manifest is rejected rather than
silently changing the experiment. Absolute/drive-qualified/parent paths and paths
colliding with the snapshot manifest are rejected. Existing snapshot directories
are never replaced. A failed copy or validation may retain a partial new directory;
the group's failure status must be respected.

Snapshot regression source is written but unrun. Its isolated copy cases use a
small fake validator; actual public-loader integration and complete walk-forward
execution remain unverified under the user's instruction to start no processes.

## Finite accounting source — unverified

The shared evaluator now has source guards for invalid scalar costs,
complex/unrepresentable matrices and nonfinite derived arithmetic. Boolean, string
and array costs are rejected rather than coerced; complex matrices are rejected
before any cast can discard imaginary data. Compounding/variance overflow
raises an explicit validation error instead of returning an invalid report or
mislabeling numeric overflow as undefined Sharpe. Normal finite accounting
formulas and A0's observation minimum remain unchanged by design. The focused
numeric regression source and broader A0 compatibility checks are unrun; no
model, test or GPU execution was started for this source change.

## Objective disclosure source — unverified

A0-default and fold/group identities and reports now retain the actual `objective`
declaration: stabilized negative gross-return Sharpe, the existing variance
epsilon, chronological minibatch training and full-validation model selection.
Configured transaction costs affect evaluation only. This metadata records
existing behavior; it does not add a cost-aware objective or a new numerical
default. Objective declaration mismatch cases and the hand-calculated loss
regression are written but unrun.

Explicit local fixed-holdout [objective-window controls](SHARPE-WINDOW-DIAGNOSTIC.md)
now have separate unverified source for full-training scope. Fold/group/service
execution stays on the existing minibatch method; no full-training fold support
or empirical comparison is claimed.

Current-source A0 repeat preflight also includes the objective declaration and
uses the same identity field registry as the runner. Immutable inputs and
objective/convention/cost metadata compare exactly; ordinary float outputs retain
the existing 1e-7 absolute bound. References missing required objective metadata
are explicitly unavailable rather than silently migrated or trained. These
compatibility changes and regressions are unrun, including fresh local repeat.

Repeat diagnostic source now handles large integer outputs exactly, labels numeric
type mismatches and retains an explicit overflow flag when an absolute difference
cannot be represented finitely. In that case `max_absolute_difference` is null.
Reference observation counts must be integers matching recorded dates before any
repeat training. Regression source covers retained finite JSON reports; it is unrun.

## Owned accounting and resume source — unverified

Aggregation now reads only planned evaluation returns, preserving the runner's
float32 target conversion without rebuilding training windows/scalers. It checks
each fold's complete local-entry accounting against its saved allocations and
owned returns before accepting the fold; the final account still carries turnover
continuously across boundaries. This is local result consistency, not model replay.

Local fixed-holdout/direct-fold resume also checks actual recorded typed identity,
schema, protocol, method and conventions before training. A matching saved hash
alone cannot mask edited manifest fields. Strict JSON and unfinished-state checks
reject ambiguous/incompatible controls while preserving existing evidence. These
guards and source regressions remain unrun, including ordinary A0/fold resume.
