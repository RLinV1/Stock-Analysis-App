## Context

See proposal.md. `data.make_samples` already implements causal fixed-holdout samples and train-only scaling. A1's dates/history requirements are fixed in SPEC sections 4/8; no historical snapshot is available. This change supplies protocol building blocks and does not route A0 or the service through them.

## Goals / Non-Goals

Generate testable fold boundaries and safely reuse the existing sample builder. Do not add training orchestration, model selection, baseline estimators, historical claims or replay semantics.

## Decisions

- Accept ordered ISO calendar-date strings and explicit inclusive requested evaluation start/end. Store immutable index tuples and boundary dates; reject booleans/invalid lookback rather than coercing them.
- Use observed date indices for target history, excluding the first `lookback` rows. Validation is max(63, integer ceiling of 10% of pre-test targets); remaining prior targets train. This implements SPEC's existing minimums without guessing trading-day-to-calendar-month conversions.
- Anchor every boundary to the effective first evaluation date plus 24*n months. Clamp leap days to a valid day in the boundary month, calculating each boundary from the original anchor to avoid accumulating drift. End each test fold just before its next boundary; gaps never synthesize sessions.
- Preserve requested/effective bounds and a reason when insufficient history shifts evaluation. An empty eligible interval is an error.
- Revalidate complete partitions/date identity before constructing samples; truncate the Dataset view at fold end, then reuse `make_samples`. This keeps the A0 algorithm unchanged while exposing deliberate-lookahead regressions.

2026-10-15 review refinement: the existing sample builder requires lookback >=2 and at least two test targets. Align the protocol's minimum lookback with that constraint, and add an explicit single-test-target option used only by the fold adapter so a short final fold stays valid. The A0 default continues requiring two test targets; no A0 model/metric behavior changes.

## Risks / Trade-offs

- Standalone protocol does not establish frozen model behavior → runner integration and per-fold model retention stay separate A1 work.
- Calendar rather than exchange calendars → only supplied observed sessions are used; upstream dataset validation owns session provenance.
- Historical data is absent → tests use synthetic business-date prices and are not paper evidence.
