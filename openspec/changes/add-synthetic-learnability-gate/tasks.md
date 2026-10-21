## Source status — 2026-10-17

Controlled fixture/analytic cases, both real-run gate cases and a source guide are written. No checks, imports, model or GPU operations ran. Leave every task unchecked until its required verification runs.

- [ ] 1.1 Add test-owned controlled two-asset data and analytic objective-bound cases for both asset orderings, with explicit provenance/rounding and no historical claim.
- [ ] 1.2 Add real CPU runner learnability cases with frozen fixture settings/thresholds, chronological held-out dates, retained artifacts and equal-weight comparison. No training or test execution now.
- [ ] 1.3 Document source status, scope and future command/check expectations; update implementation/handoff immediately after logical changes.
- [ ] 2.1 After explicit process authorization, execute analytic and both end-to-end cases, record failures honestly and verify relevant/full compatibility. Do not tune thresholds using held-out outcomes.
- [ ] 2.2 Validate OpenSpec and documentation, reconcile evidence and archive only when all implementation and required verification is complete. No push.
