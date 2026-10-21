## Context

See proposal.md. The archived planner supplies validated expanding 24-month folds and train-only samples, including a one-target final fold. The existing runner owns seeded optimization, validation-only selection, immutable model/scaler artifacts and epoch recovery. Its evaluation currently rejects fewer than two observations. A1 training orchestration is already approved in define-product-and-stack task3.11; historical data and full replay remain separate.

## Goals / Non-Goals

Execute the existing research method on explicit planned folds, retaining every model/scaler and a continuous chronological evaluation. Preserve the fixed-holdout A0/service default. No new estimator, optimization claim, parameter sweep, group resume, external manifest import, historical study or v2 verifier is delivered.

## Decisions

- Add explicit fold context to the existing runner; validate lookback/split identity before training and use the bounded fold sample adapter. Record fold identity in the run identity/manifest so incompatible resume cannot silently reuse a fixed-holdout checkpoint.
- Retain the existing optimization and validation selection. Freeze the selected model/scaler within a fold; expand/retrain only at the next planned boundary. Use caller-declared seed/model settings unchanged for each fold, documenting that choice rather than adopting a new seed policy.
- Require explicit integer counts/seeds and finite numeric learning-rate/cost values, rejecting booleans and fractional counts before group creation. Reuse the existing RunConfig budgets for bounds; this stricter new local configuration does not change A0 defaults.
- Share strict setting-type checks between group configuration and direct fold runner calls. Reject malformed fold identity, mismatched split settings and non-integer fold stop budgets before dataset/device access; direct calls must not bypass the group wrapper's contract.
- Orchestrate under a unique local group directory with immutable config/plan/dataset identity and owned child runs. Preserve partial artifacts and record failure instead of publishing a completed group. Group-level resume is out of scope.
- Verify returned child directories are within the current fold's owned root before artifact reads, and check typed provenance/report context and the current baseline strategy order before aggregation. Keep stored references relative to the resolved group even when the caller supplied a relative output root.
- Match the inspected public dataset loader's filename-only CSV contract when snapshotting; nested directories are not supported. Reject prefixes, absolute/drive-qualified/traversing paths, manifest collisions and Windows aliases before snapshot creation. Earlier nested-path wording was a stub assumption, corrected by source inspection.
- Recompute aggregate metrics from concatenated chronological allocations and aligned returns. Apply the existing target-turnover convention continuously across model boundaries; never concatenate per-fold wealth or repeatedly charge an initial cash position. Per-fold reports remain explicitly local fold evaluations.
- Read aggregation targets directly from adjacent owned prices with the runner's existing float32 return conversion. Do not rebuild training/validation input windows or scalers just to recover evaluation returns. Keep the learned-model/sample path unchanged.
- Recompute each owned fold's complete local-entry accounting from its serialized allocations and aligned returns before accepting it. Require the current evaluator's typed JSON shape/values, then separately recompute continuous group accounting. This proves local report consistency only, not that model replay produces those allocations or that imported evidence is authentic.
- Permit one-observation metrics only through an explicit opt-in. Preserve A0's two-row minimum; one-row Sharpe is null with its reason. This unlocks the planner's short final fold without fabricating an extra observation.
- Preserve the existing finite-input accounting formulas, rejecting nonfinite derived results and invalid scalar costs explicitly instead of returning invalid report values or incidental numeric exceptions.
- Reject fold/group references in the existing A0 local repeat path before training. Group replay remains unsupported until its own validated protocol exists.

## Risks / Trade-offs

- Optional fold support changes the source fingerprint: retained A0 runs become prior-code evidence, while default numerical behavior must remain regression-tested.
- Different fold models can produce boundary turnover: compute it from actual adjacent weights and test a fixed-answer boundary case.
- Future data changes whole-input identities: compare learned weights/scalers and earlier predictions for causality, without expecting identity hashes to remain equal.
- Synthetic tests prove mechanics, not a historical finding or paper reproduction. Full baseline/tier/cost studies remain open.

## Migration Plan

Additive local CLI and runner options. Preserve existing run/service commands. Revert orchestration and fold opt-in to roll back; retain generated artifacts and documentation as historical evidence.
