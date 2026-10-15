# Implementation record

## Final verification — 2026-10-15

Full research regression passes **111/111 in 52.12 seconds** on the existing Python/PyTorch environment. The earlier post-edge run had 110 passes/one legacy diagnostic mismatch; restoring the original default diagnostic resolved it. Independent read-only subagent review found no actionable blockers in calendar/gap coverage, minimum history, partition validation, causal scaling or the single-target opt-in. No A0 runner/CLI or metric default changed.

The two implemented protocol requirements are synced to the new main `portfolio-research` spec; active A0/A1 deltas retain their non-overlapping requirements. Rephrased the archive checkbox to separate verified spec synchronization from the subsequent archive operation, avoiding a self-referential completion gate. Strict main/change validation and archive follow; full per-fold training/model retention, historical studies, v2 replay and baselines remain open.

Strict OpenSpec validation passes **11/11**, including the new main spec and all active changes. The synced main requirements/scenarios were compared to the delta and agree. All five bounded tasks are complete; archive housekeeping follows. Other A1 requirements remain in their active changes, without being promoted to implemented behavior.

Archived on 2026-10-15 after exact requirement/scenario sync comparison and completed tasks. The implementation history is preserved here; full A0/A1 research changes remain active. Adding only these two independently completed protocol requirements to main does not sync or imply completion of the other active research requirements.

## Review continuation — 2026-10-15, before correction

The previous full-suite process ended without retained output when the session ended; do not infer it passed. Fresh full research checks are running. Source review found two adapter mismatches: protocol accepted lookback 1 although the builder requires >=2; final folds could contain one target although the builder defaults to two. Scope/task/spec updated before correcting these boundaries. Preserve A0 defaults and introduce an explicit fold-only single-target option with regression coverage.

Fresh pre-correction full research regression passed **106 tests in 58.43 seconds**. Implemented the explicit boolean `allow_single_test=False` sample-builder opt-in, used only by fold construction, plus lookback>=2 and single-final-date/coercion tests. The first follow-up run caught an existing test's required “at least two” diagnostic; restored the legacy default diagnostic. Final edge-case/full regression is pending. Docker Desktop and app/Playwright tests are now explicitly authorized by the user; these do not change this module's synthetic evidence scope.

## Planned — 2026-10-14, before source edits

User requested all remaining project tasks with subagents. Parent implements the existing A1 fold-generation requirement as a separate bounded change while agents own mobile/worker/Git safeguards. Reviewed SPEC sections 4/8, active research deltas, Dataset/Samples/make_samples and causality tests. Use actual ordered ISO dates, immutable index partitions and a truncated Dataset view; keep A0 runner/CLI unchanged. No historical data, model training, dependency install, service, Docker or phone work is included. All checks are pending.

## Protocol source — 2026-10-14

Added immutable `Fold`/`FoldPlan`, strict calendar/date/range/lookback validation, anchored 24-month boundaries and minimum-history start adjustments. Added `make_fold_samples`, which revalidates partitions/date identity and truncates at fold end before reusing the existing scaler/alignment. No A0 source path changed. Verification and task completion remain pending the new synthetic fixtures/full research suite.

## Targeted verification — 2026-10-14

All **28 protocol tests pass in 3.67 seconds** on the existing environment. Fixtures verify expanding history, contiguous evaluation targets, Sunday/leap-day/long-gap boundaries, explicit unsupported-start adjustment, invalid dates/lookbacks/ranges, next-period alignment, training-only scaler fit and invariance beyond fold end. Deliberate overlapping/future/reordered indices and forged date/lookback/schedule identities are rejected. Full research regression and strict validation remain next. The module is not connected to training orchestration; no model/historical A1 result is claimed.
