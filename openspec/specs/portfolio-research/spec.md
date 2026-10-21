# Portfolio Research Specification

## Purpose

Provide causal, auditable research protocols and numerical evidence while preserving explicit distinctions between synthetic checks, historical reproduction and retrievable replay.

## Requirements

### Requirement: Generate causal expanding fold plans
The research protocol SHALL plan expanding training/validation history and contiguous non-overlapping evaluation folds on observed, strictly ordered real dates. Retraining boundaries SHALL be anchored every 24 calendar months to the effective first evaluation date; non-trading boundaries SHALL use the next observed date without inventing data. Each fold SHALL have lookback context, at least 252 training targets and max(63, ceiling(10% of pre-test targets)) validation targets, all strictly before evaluation. An unsupported requested start SHALL move forward with an explicit reason, or fail when no eligible evaluation date remains. Malformed, duplicate or unordered dates and invalid ranges SHALL fail explicitly.

#### Scenario: History begins too late
- **WHEN** the requested evaluation date lacks the required training, validation and lookback history
- **THEN** the first evaluation date moves to the first eligible observed date with its reason recorded, or planning fails if the requested end leaves no eligible date

#### Scenario: Calendar boundary falls between observed dates
- **WHEN** a 24-month boundary falls on a weekend or gap
- **THEN** the preceding fold ends before the boundary and the next fold starts at the first observed date after it, without duplicate or missing evaluation targets

### Requirement: Fit fold samples using prior training inputs only
The fold sample adapter SHALL use the existing next-return alignment, fit preprocessing only on the training input rows, and omit all observations beyond that fold's evaluation end. It SHALL reject a fold whose target partitions, stored dates or lookback do not match the dataset. Changes after the training boundary SHALL NOT change training samples/preprocessing; changes after the fold end SHALL NOT change any sample in that fold. Planning a fold SHALL NOT imply that models were trained, frozen or historically evaluated.

Lookback SHALL be a whole number of at least two observations. A final evaluation fold containing only one target SHALL remain constructible without adding observations beyond the requested end; the existing A0 default SHALL retain its two-test-target minimum.

#### Scenario: Requested end leaves one test target
- **WHEN** the last fold contains exactly one observed evaluation date
- **THEN** its sample adapter returns that target using prior inputs only, without relaxing the default A0 split checks

#### Scenario: Deliberately borrow a future target
- **WHEN** a caller places an evaluation target into the fold's training partition
- **THEN** sample construction rejects the overlapping or non-contiguous fold

#### Scenario: Future prices are changed
- **WHEN** prices after a fold's evaluation end are changed
- **THEN** every sample, target and fitted scaler for that fold remains unchanged

### Requirement: Compare finished walk-forward runs with classical mean-variance
A finished walk-forward run SHALL be comparable with a long-only, fully invested, maximum-Sharpe mean-variance portfolio re-estimated daily from the previous 50 daily returns, using the run's own dataset snapshot, test dates, target returns, cost and continuous accounting. The comparison SHALL refuse to write unless recomputed recorded strategies match the run report exactly, and SHALL create a new output file without modifying the run.

#### Scenario: Compare a completed run
- **WHEN** a caller compares a completed walk-forward run
- **THEN** the output SHALL list every recorded strategy's metrics unchanged plus mean-variance metrics over the same number of test days

#### Scenario: Weights use only prior data
- **WHEN** prices on or after a target day change
- **THEN** the mean-variance weights for that target day SHALL be unchanged

#### Scenario: Output exists
- **WHEN** the comparison output file already exists
- **THEN** the command SHALL fail without overwriting it

### Requirement: Acquire Yahoo history as hashed local snapshots
Historical acquisition SHALL download each ticker's daily history with explicit adjustment, action, repair and date options, retain the exact downloaded bytes with SHA-256 hashes, record the client version, query and retrieval time, and write only to a new local directory that is never committed.

#### Scenario: Fetch a tier
- **WHEN** a caller fetches tier1 or tier2 with explicit start and end dates
- **THEN** the output SHALL contain each ticker's raw CSV, an acquisition record with hashes and query, and a dataset manifest accepted by the existing loader

#### Scenario: Output already exists
- **WHEN** the output directory already exists
- **THEN** acquisition SHALL fail before downloading or replacing anything

### Requirement: Build total-return prices before aligning dates
Each ticker's price series SHALL be a total-return index compounded from split-adjusted close plus same-day distributions, computed on that ticker's own calendar before keeping only dates every ticker traded. Missing, nonpositive or nonfinite values SHALL be rejected, never filled, and the number of dropped dates SHALL be recorded as a deviation.

#### Scenario: Distribution on a date another ticker lacks
- **WHEN** a ticker pays a distribution on a date missing for another ticker
- **THEN** the distribution SHALL still be included in that ticker's next retained return

### Requirement: Label tier and source limits
Every Yahoo dataset SHALL declare that it is a reconstruction rather than the authors' data, that raw ^VIX is not investable (tier1) or that VIXY replaces VIX with history from 2011 (tier2), and that close prices carry hindsight split adjustment.

#### Scenario: Tier 1 manifest
- **WHEN** tier1 data is written
- **THEN** its deviations SHALL state that the raw VIX index is not investable
