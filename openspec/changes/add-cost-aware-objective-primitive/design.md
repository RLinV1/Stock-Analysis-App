## Context

Current metrics compute gross target-weight returns minus cost_rate times two-sided L1 target change, with an initial cash entry; they explicitly do not model drift or execution slippage. Current training uses gross returns. A1 task3.7 is approved, but a cost-aware training-window boundary policy has not been selected or empirically checked.

## Decisions

- Put unverified tensor primitives in a separate cost_objective module; do not alter current model/runner objective selection or artifacts claiming evaluation-only costs.
- Require previous_target explicitly. It must be an all-zero cash vector or normalized long-only target matching asset count, dtype and device. Do not silently reset at minibatch/fold boundaries or choose a carried/detached model state.
- Within the supplied window, compare each row to the previous row's target, preserving autograd through current-window adjacent weights. The first row uses the caller's explicit prior target. This is idealized target-turnover accounting, not drift-aware/self-financing transaction execution.
- Compute gross=(weights*returns).sum, cost=cost_bps/10000*L1 difference and net=gross-cost, rejecting nonfinite outputs or net<=-1. Require matching floating tensors with at least two rows, no implicit conversion, finite returns above -100% and normalized nonnegative weights.
- Accept only finite real scalar costs in the existing 0..100bps range, rejecting booleans/strings/tensors/oversized values. Keep the existing stabilized loss formula/epsilon when using net returns.
- Add explicit metadata for the primitive's formula/limitations in its module/guide, not in current run artifacts. The future caller must define window boundary policy and retained declarations before any runner integration.

## Verification plan and limitations

Compare initial-cash net paths with the existing evaluator and fixed hand answers. Check carried target avoids a second initial entry, splitting/joining a window preserves accounting with explicit handoff, and zero cost matches gross loss/gradient. Use smooth softmax targets away from turnover kinks for finite-difference autograd checks. All checks are unrun. No cost-aware training, batch-boundary policy, model-selection experiment, historical evidence or paper interpretation is delivered.
