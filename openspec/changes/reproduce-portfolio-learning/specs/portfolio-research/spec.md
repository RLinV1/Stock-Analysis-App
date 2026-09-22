## Purpose

Enable auditable local experiments comparing learned portfolio allocations with simple baselines, while preserving causal evaluation and clearly distinguishing reproduction from methodological extensions.

## ADDED Requirements

### Requirement: Identify data and methodological provenance
Each experiment SHALL reference an immutable dataset manifest with source, instrument identifiers, date range, adjustment convention, missing-data policy, access/license notes, and content checksums. Reports SHALL identify unresolved paper assumptions and deviations, and SHALL NOT present an adapted or synthetic experiment as an exact historical reproduction.

#### Scenario: Original instrument mapping is unresolved
- **WHEN** a run uses a substitute instrument or cannot establish the original series
- **THEN** its report identifies the uncertainty or substitution and labels the run as adapted or paper-inspired

### Requirement: Prevent future-data use
The runner SHALL keep training, validation, and test observations chronologically ordered, fit preprocessing only on training observations, and apply allocations only to subsequent returns. Hyperparameter selection SHALL exclude held-out test outcomes.

#### Scenario: Future prices change
- **WHEN** observations strictly after a fixed decision time are changed without retraining the fixed model
- **THEN** the features and allocation at that decision time remain unchanged

#### Scenario: Split configuration is invalid
- **WHEN** configured target dates overlap between training, validation, and testing
- **THEN** the runner rejects the configuration before training

### Requirement: Produce valid allocations and comparable reports
The model SHALL produce finite, nonnegative allocation weights summing to one within a declared numerical tolerance. Evaluation SHALL include equal-weight and fixed stock/bond baselines when the selected universe supports them, using the same dates and disclosed execution/cost assumptions. Reports SHALL include cumulative return, annualized volatility and Sharpe, maximum drawdown, turnover, and explicit metric conventions. Undefined metrics SHALL be marked undefined rather than silently replaced by favorable values.

#### Scenario: Return variance is zero
- **WHEN** a strategy produces a constant return series
- **THEN** evaluation marks its undefined risk-adjusted metric explicitly and training avoids division by zero under a documented stabilization rule

### Requirement: Preserve reproducible run evidence
Every run SHALL save its dataset checksum, code and dependency versions, seed, device, split boundaries, configuration, cost assumptions, method label, allocation history, returns, metrics, and model artifacts. A completed run SHALL retain its original manifest when another run is started.

#### Scenario: A researcher repeats an experiment
- **WHEN** the saved manifest is used to repeat a run
- **THEN** the runner uses the recorded inputs/settings and reports numerical differences under a documented tolerance and determinism scope

### Requirement: Support bounded local execution and recovery
The runner SHALL offer CPU execution without cloud or broker credentials and a small synthetic smoke configuration. Epoch budgets SHALL be configurable. Completed-epoch checkpoints SHALL permit resumption with matching configuration and data; incompatible checkpoints SHALL be rejected. Measured elapsed time and peak-memory measurement availability SHALL be included in run evidence.

#### Scenario: A local run is interrupted
- **WHEN** training stops after a valid completed-epoch checkpoint
- **THEN** a resume operation restores model, optimizer, progress, and random state and continues without presenting an incomplete run as completed
