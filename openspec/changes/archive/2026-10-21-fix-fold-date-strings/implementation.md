# Implementation record

## Plain string fold dates - 2026-10-21

Root cause: `protocol._dates` accepted `numpy.str_` (a `str` subclass) from `Dataset.dates` and returned it unchanged, so `Fold.train_end`, `validation_end` and related fields were NumPy scalars. `runner` saves `asdict(config)` into `model.pt`; `torch.load(..., weights_only=True)` then failed with "Unsupported global: GLOBAL numpy._core.multiarray.scalar". Fixed once in the shared validator: validation is unchanged and the function now returns `tuple(str(value) for value in result)`. All callers (walk_forward and sweep_runner) pass through it.

Verification: before the fix, the first complete suite run was 5 failed / 694 passed (test_fold_runner x2, test_sweep_integration, test_walk_forward_causality x2). After it, the targeted fold/planner/walk-forward/sweep set passed 84/84 and the full research suite passed 699/699 (CPU, torch 2.8.0+cpu). All four Yahoo walk-forward runs then completed with this fix.
