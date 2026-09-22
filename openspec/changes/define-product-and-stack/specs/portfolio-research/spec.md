## Purpose

Strengthen experiment evidence requirements so that every reported result is independently verifiable, carries its uncertainty, and enumerates its departures from the source paper.

## ADDED Requirements

### Requirement: Separate allocation inference from retraining
Walk-forward evaluation SHALL compute daily allocations from changing trailing historical inputs while keeping the selected model and fitted preprocessing fixed within a fold. Retraining SHALL occur at recorded 24-month fold boundaries using only prior data. A fixed-holdout prototype SHALL NOT claim this retraining behavior.

#### Scenario: New day inside the same fold
- **WHEN** a new decision date provides a new historical input window
- **THEN** allocations may change but the model and fitted preprocessing versions remain unchanged and weights apply only to the subsequent return

### Requirement: Bind every result to a reproducible manifest
Each v2 run SHALL emit a schema-validated manifest recording available git identity, source snapshot and dependency-lock hashes, input data hash, adjustment convention, ordered features/assets, full configuration, fold boundaries, random seed, runtime identity, per-fold preprocessing/model hashes, and metrics. Missing git identity SHALL be explicit. A modified or non-git source tree SHALL require a retrievable full source snapshot and dependency lock to qualify for replay; a fingerprint alone SHALL NOT establish replay availability.

#### Scenario: Working tree is modified
- **WHEN** a run executes while tracked files differ from the recorded commit
- **THEN** its manifest records the dirty state and verification is UNVERIFIABLE unless the exact source snapshot and dependency lock can be retrieved

#### Scenario: Input data cannot be hashed
- **WHEN** a run's input dataset has no computable content hash
- **THEN** the run is marked unverifiable rather than recorded as a valid result

### Requirement: Support third-party verification of a manifest
The system SHALL validate a supported manifest and bounded inputs before replay, compare immutable input identities before metrics, and distinguish UNVERIFIABLE, INPUT_MISMATCH, EXECUTION_FAILED, MISMATCH and MATCH. Reports SHALL enumerate input differences, per-metric comparisons, tolerances and undefined reasons. Numeric comparison SHALL use absolute tolerance 1e-7 plus relative tolerance 1e-5; dates, ordering, counts, hashes and null reasons SHALL match exactly. Phase A1 SHALL expose CLI verification; Phase B SHALL reuse it through asynchronous HTTP jobs.

#### Scenario: Manifest is re-run on identical inputs
- **WHEN** a manifest is re-executed with matching code, data hash, configuration, and seed
- **THEN** successful replay reports MATCH only if every required comparison agrees within its declared tolerance; otherwise it reports MISMATCH or EXECUTION_FAILED as appropriate

#### Scenario: Manifest is re-run against different data
- **WHEN** re-execution uses a dataset whose content hash differs from the manifest
- **THEN** the verification result is INPUT_MISMATCH and names the data hash, even if resulting metrics happen to agree

#### Scenario: Reference input is unavailable
- **WHEN** the required source snapshot, dataset, preprocessing, or compatible runtime cannot be retrieved
- **THEN** verification reports UNVERIFIABLE with a reason and does not claim a numerical match

#### Scenario: Undefined ratio differs
- **WHEN** one result has an undefined metric and the other has a finite value or different undefined reason
- **THEN** verification reports MISMATCH rather than substituting zero

### Requirement: Report result variance across seeds
Headline results SHALL be produced from multiple random seeds and reported as a distribution including mean, standard deviation, and range. A single-seed figure SHALL NOT be presented as a headline result.

#### Scenario: A headline metric is published
- **WHEN** a Sharpe ratio is reported as a project finding
- **THEN** it is accompanied by the seed count and the observed variation across seeds

#### Scenario: Seed variation exceeds the gap to the paper
- **WHEN** across-seed standard deviation is comparable to the difference from the paper's reported value
- **THEN** the report presents the observed variation and comparison without claiming statistical indistinguishability from standard deviation alone

### Requirement: Enumerate and surface every deviation from the source paper
The project SHALL maintain an enumerated list of parameters the source paper leaves unspecified, each recording what the paper states, the value chosen, the rationale, and the measured impact where known. Deviations SHALL be reachable from any result that depends on them.

#### Scenario: A result depends on an unspecified parameter
- **WHEN** a result is produced using a value the paper does not specify
- **THEN** that deviation is recorded in the run manifest and reachable from the presented result

#### Scenario: A substitute instrument is used
- **WHEN** an asset in the paper's universe is not investable and a proxy is substituted
- **THEN** available variants are compared on a declared common protocol/window and any unavailable variant is explicitly reported; different training periods are not silently compared as equivalent

### Requirement: Verify exported inference parity
A model artifact exported for serving SHALL be verified to produce outputs matching the training-framework model within a declared tolerance on identical inputs, and exported allocation weights SHALL remain nonnegative and sum to one within tolerance. An artifact failing verification SHALL NOT be registered for serving.

Each fold SHALL retain its own preprocessing/model and ordered feature/asset contract. Registration SHALL retain parity evidence and content hashes; a supplied boolean alone SHALL NOT establish parity. Serving SHALL name the exact selected fold/model version.

#### Scenario: Export diverges from the trained model
- **WHEN** exported-artifact outputs differ beyond tolerance from the training framework on identical input
- **THEN** the artifact is marked unverified and is not registered for serving

### Requirement: Respect instrument availability in tiered evaluation
Tiered experiments SHALL use actual common trading dates and require sufficient pre-test training, validation and lookback history. Tradable experiments SHALL NOT synthesize pre-inception observations or splice nominal prices across instruments. The initial tradable default SHALL use VIXY throughout with testing no earlier than 2013; fidelity testing may begin in 2011 with raw VIX explicitly labelled not investable. First folds SHALL have at least 252 training and 63 validation targets plus lookback context. Comparative runs SHALL use matched training/test boundaries.

#### Scenario: First fold lacks history
- **WHEN** a proposed tradable fold lacks the minimum pre-test history
- **THEN** the run rejects that fold or moves its start forward with the exclusion recorded, never borrowing future observations
