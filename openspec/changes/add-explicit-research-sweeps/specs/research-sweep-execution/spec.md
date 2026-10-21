## ADDED Requirements

### Requirement: Sequential snapshot-bound local sweeps
Local sweep execution SHALL require all common model and walk-forward protocol settings and an explicit seed/cost grid with a maximum candidate count. It SHALL validate the full candidate/fold plan before creating experiment output, record both candidate and fold counts, and execute candidates sequentially against one validated owned dataset snapshot. Seed and cost SHALL be the only varying experiment settings.

#### Scenario: Invalid grid or model configuration
- **WHEN** any candidate or common setting fails preflight validation
- **THEN** no sweep group SHALL be created and no training SHALL start

#### Scenario: Input changes after snapshot
- **WHEN** the caller's original dataset changes after the sweep snapshot is validated
- **THEN** later candidates SHALL continue to use the same validated sweep snapshot

### Requirement: Retain candidate identity and terminal progress
Each requested candidate SHALL have a persisted inventory entry. Successful candidates SHALL have completed group status, matching configuration, dataset, source, runtime and protocol identity, matching test dates, and retained manifest/report hashes. Failed training and invalid returned artifacts SHALL remain visible as distinct terminal states. Progress SHALL persist after each candidate; interrupted sweeps SHALL retain pending entries and SHALL NOT claim complete coverage or group resume support.

#### Scenario: One candidate fails
- **WHEN** a candidate's training raises an ordinary exception
- **THEN** its failure SHALL remain in the inventory and the next requested candidate SHALL still be attempted
- **AND** the completed summary SHALL distinguish coverage completeness from all-successful completion

#### Scenario: Returned artifact has different settings
- **WHEN** a returned group differs from the requested candidate identity
- **THEN** that candidate SHALL be invalid and SHALL NOT contribute numeric summary values

#### Scenario: Consume the actual walk-forward report contract
- **WHEN** a completed walk-forward report contains strategy entries with nested metrics and return paths
- **THEN** the sweep SHALL extract each strategy's metrics for descriptive aggregation and retain the complete child report by reference and hash
- **AND** malformed or flat strategy entries SHALL be invalid rather than silently reinterpreted

#### Scenario: Completed status conflicts with the fold plan
- **WHEN** returned completed-fold or fold-budget counts differ from the candidate's planned fold count
- **THEN** that candidate SHALL be invalid even if its status label says completed

#### Scenario: Operator interrupts training
- **WHEN** execution is interrupted before all candidates terminate
- **THEN** the sweep SHALL retain partial progress and mark interruption
- **AND** it SHALL NOT produce a complete terminal-grid summary
### Requirement: Disclose cost sensitivity versus cost-aware training
Sweeps using the current local LSTM method SHALL retain its actual gross-return objective and evaluation-only cost treatment in common identity and result metadata. Returned candidate declarations SHALL match that method. A configured cost grid SHALL NOT be described as introducing transaction costs into training loss, nor as model reuse or a different seed policy.

#### Scenario: A candidate claims a different objective
- **WHEN** a returned candidate declares a cost-aware or otherwise different objective
- **THEN** it SHALL be invalid for the current common-method sweep
### Requirement: Preserve owned baseline comparison scope
Sweep execution SHALL validate returned child and candidate-root ownership within the sweep before reading child artifacts. Completed candidates SHALL contain exactly the learned strategy and baselines supported by the owned dataset's declared asset roles, with the corresponding explicit baseline omissions. A consistently missing baseline SHALL NOT become the common strategy set merely because it appeared in the first candidate. Offline caller-supplied summaries SHALL remain a separate, unauthenticated contract.

#### Scenario: Every candidate omits an expected baseline
- **WHEN** returned candidate reports all omit an available equal-weight or stock/bond baseline
- **THEN** those candidates SHALL be invalid rather than yielding a successful narrowed comparison

#### Scenario: Candidate root resolves outside the sweep
- **WHEN** a returned directory is inside a candidate root whose resolved location is outside the sweep
- **THEN** it SHALL be rejected before child artifact contents are opened
