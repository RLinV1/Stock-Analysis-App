## ADDED Requirements

### Requirement: Preserve explicit sweep coverage
Local research sweeps SHALL require caller-declared unique seeds/costs and a maximum candidate count, reject invalid/duplicate/excess candidates, and retain exactly one terminal record for every requested combination. Failures and invalid results SHALL remain visible and SHALL NOT be silently omitted, replaced or treated as successful observations.

#### Scenario: A selected run fails
- **WHEN** a requested seed/cost candidate fails
- **THEN** its declared cell and failure state remain in coverage and the summary's missing/completed counts

### Requirement: Report descriptive sweep variability honestly
Sweep summaries SHALL report numeric/null counts, reasons for undefined metrics and descriptive mean/population spread only from valid completed observations, alongside all requested terminal states. They SHALL NOT select favorable seeds, fabricate missing values or imply historical reproduction/statistical significance. Comparisons SHALL preserve strategy/data/evaluation context.

#### Scenario: Sharpe is undefined for a completed run
- **WHEN** a completed strategy contains null Sharpe and its explanation
- **THEN** the null and reason are counted without a numeric substitute

### Requirement: Compare costs only where tested
Cost comparisons SHALL use actual caller-tested cumulative-return differences and label missing adjacent comparisons as unavailable. A sign change between tested points SHALL NOT be presented as an interpolated exact crossing, recommended cost or selected favorable seed.

#### Scenario: An intervening tested cost failed
- **WHEN** one candidate is missing a valid completed result
- **THEN** adjacent intervals involving that candidate remain unavailable rather than skipping across it to infer a crossing
### Requirement: Bound ordered sweep input capture
Direct sweep settings SHALL accept explicit ordered lists or tuples for seed and cost axes, preserve that order, and reject unordered mappings/sets and lazy iterables rather than consuming them implicitly. Positive integer candidate budget and Cartesian count SHALL be checked before copying those axes. This SHALL NOT imply a fold-time or memory budget for model execution.

#### Scenario: Caller supplies a lazy or unordered grid axis
- **WHEN** an axis is a generator, mapping, set or other unsupported iterable
- **THEN** construction SHALL reject it without iterating it

#### Scenario: Declared grid exceeds its candidate budget
- **WHEN** explicit list/tuple lengths exceed max_runs
- **THEN** settings SHALL reject before copying axes or creating candidates/output
