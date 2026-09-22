# Data sourcing, adjustment and publication

Corrected 2026-09-21. **Provider choice and licensing are provisional.** Earlier statements that every free source prohibited redistribution and that the audit resolved data provenance were too broad.

## Candidate and evidence status

Yahoo via an explicitly pinned client is a candidate; no fetching module exists yet. Always make adjustment, repair, interval, requested dates and timezone options explicit. The review confirmed yfinance 1.7.0 exists, not that its acquisition path is validated here. Provider-specific defaults must be checked against the selected version before implementation.

Prior audit observations, retained but **not independently reproducible from saved local evidence**:
- AGG 2006-02-06 to 2020-12-31: raw price change 17.85%, adjusted return 89.25%, 179 distributions totaling about 50.22.
- Corresponding VTI figures: 206.74% / 310.61%; DBC: -39.50% / -33.60%.
- Proposed reconstruction reportedly produced AGG 89.27%.
These cannot yet serve as golden test answers. Raw price change is not total return. Whether changing adjustments changes optimal allocations is an empirical question, not a guaranteed directional outcome.

## Snapshot contract

Retain the exact locally acquired response and a canonical consumed dataset, each hashed, with retrieval time, query, provider/client versions, timezone, date exclusions and corporate-action recipe. Canonicalization fixes column order, float encoding, date format and line endings.
Provider history is not immutable. “Raw Close” may already be retrospectively split-adjusted; later splits or revisions can change it. Corporate-action fields may also be revised. Hashing identifies a snapshot; it does not guarantee a future fetch will match.
Do not replace an old snapshot silently. If hashes differ, retain both and produce an explicit revision comparison. Offline replay requires the original bytes; unavailable data means UNVERIFIABLE.

## Adjustment requirements

Use a tested provider-specific adapter. For split-consistent price and cash-distribution units, a candidate gross-return formula is (close_t + dividends_t + capital_gains_t) / close_previous. Check whether distribution fields overlap before summing; avoid double counting.
Do not apply split adjustments twice. Prices and distributions must use the same share basis and event timing. Preserve ex-dates, split factors, timezone/session rules and missing-data decisions.
Verify with synthetic known-answer fixtures for dividends, splits, capital gains and combined events. Cross-provider checks are optional integration evidence, never live network dependencies of unit tests.
Adjusted prices are not automatically point-in-time information; explicitly disclose hindsight adjustments.

## Access and publication

Record permission/access terms for each exact dataset and intended use before downloading or redistribution. A free endpoint is not a redistribution license; neither is a third-party rehost's assertion of ownership. This review did not establish legal permission across all providers.
There may be other redistributable datasets; that does not imply availability of the paper's instruments/dates.
Use synthetic samples for committed CI fixtures. Keep vendor snapshots local and ignored unless specific permission is recorded. Small samples are still data; being short does not establish permission.
Derived returns, figures, model artifacts and allocation series require their own publication assessment; transformation alone does not establish rights. Commit provenance and permitted outputs only. Apache-2.0 would cover project code, not automatically upstream data.
Use a provider adapter so a supported licensed source can replace a provisional source without changing experiment semantics. No paid data purchase is authorized.

## Work still required

Implement acquisition/validation and adjustment fixtures, confirm actual common dates, retain snapshot hashes and run the instrument investigation. Public historical claims require reproducible evidence; local synthetic work can proceed now.
