## Context

See proposal.md. A0 reports contain dated strategy metrics and null Sharpe explanations. The new fold/group source also emits strategy metrics but is unrun. Sweep work follows already-approved A1 task3.8; no provenance-validated historical data or accepted seed list exists.

## Goals / Non-Goals

Account for the complete caller-declared experiment grid and summarize its results without favorable selection. Begin with pure planning/summary functions and source regressions. Do not choose research defaults, run experiments, add baseline estimators or claim statistical significance/historical evidence.

## Decisions

- Require explicit unique integer seeds, finite costs within existing bounds and an explicit positive maximum candidate count. Reject duplicates or excess combinations instead of deduplicating or truncating.
- Inventory the Cartesian product in caller order. Require exactly one terminal result per declared cell, with no extra or duplicate cell.
- Validate completed strategy metrics, dimensions/context and null explanations before summarizing. A missing run is a coverage failure, not a silently omitted observation.
- Group descriptive metrics by tested cost and strategy. Preserve each requested seed's terminal state, numeric/null counts and null reasons. Population standard deviation describes the observed sample only; it is not a confidence interval or significance claim.
- Cost comparisons use the sign of cumulative-return differences at caller-tested points. Label adjacent tested intervals with missing results as unavailable. Do not interpolate an untested threshold, fill failed runs or identify a recommended seed/cost.
- Add actual sequential execution only after the summary layer is reviewed, with an immutable dataset snapshot and all non-seed/cost settings fixed. Execution and verification remain prohibited until the user authorizes processes.

## Risks / Trade-offs

- Sparse/failed cells can bias summaries: show requested/completed/failure counts alongside every summary and preserve full records.
- New fold reports are unverified: maintain explicit source-draft status and require integration checks later.
- No historical snapshot: synthetic fixtures test mechanics only. This does not complete historical A0 task4.2.
