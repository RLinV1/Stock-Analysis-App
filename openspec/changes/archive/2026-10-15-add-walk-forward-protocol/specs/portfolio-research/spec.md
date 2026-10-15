## Purpose

Provide causal, auditable research protocols and numerical evidence while preserving explicit distinctions between synthetic checks, historical reproduction and retrievable replay.

## ADDED Requirements

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
