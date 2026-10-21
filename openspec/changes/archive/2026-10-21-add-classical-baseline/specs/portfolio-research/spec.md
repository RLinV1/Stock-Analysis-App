## ADDED Requirements

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
