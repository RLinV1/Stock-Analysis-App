## ADDED Requirements

### Requirement: Connect only after a successful service response
The client SHALL treat the service as connected only after an authenticated run list request succeeds, SHALL keep the base URL and token in memory only, SHALL never display the token, and SHALL show only runs and states returned by successful responses.

#### Scenario: Token rejected
- **WHEN** the user connects with a token the service rejects with 401
- **THEN** the UI says the token was rejected, stays disconnected and shows no live runs

#### Scenario: Retry a submission
- **WHEN** a submission fails with a network error and the user retries the same draft
- **THEN** the client sends the same idempotency key so the service cannot create a second run

### Requirement: Display only validated measured report values
The client SHALL retrieve completed reports through the authenticated runs client, reject a manifest naming a different service run, and show only validated finite measured metrics. Undefined Sharpe values SHALL retain their explanation, and missing or malformed results SHALL show an error with a retry action instead of invented values. Results SHALL identify synthetic data, evaluation dates and costs when supplied, and show the research-only notice. A response from a prior connection or selected run SHALL NOT replace the current result. The A0 report run_id is a research-run provenance identifier, distinct from the service UUID; the authenticated route supplies service-run context.

#### Scenario: Inspect a completed measured report
- **WHEN** the requested run returns a valid report
- **THEN** Results shows the returned strategy metrics and evaluation context with synthetic and research-only labels

#### Scenario: Undefined Sharpe ratio
- **WHEN** a strategy reports a null Sharpe ratio with a reason
- **THEN** Results displays the reason and no numeric substitute

#### Scenario: Manifest identity mismatch
- **WHEN** a manifest names a different service run from the one requested
- **THEN** the client rejects the manifest response

#### Scenario: Service result unavailable
- **WHEN** loading a completed report fails
- **THEN** the screen displays an honest failure and a named retry action

### Requirement: Inspect validated equity and allocations
Results SHALL retrieve equity and allocations through the authenticated client, require finite equity values on ordered real calendar dates and finite long-only weights in declared asset order summing to one within 1e-6. Displayed views SHALL match the measured report's dates and strategies; equity SHALL also match its transaction cost. The UI SHALL show endpoint conventions, numerical equity values and labelled asset weights with named strategy/date controls, explicit synthetic labels and the research notice. Each view SHALL have independent loading/error/retry states. Responses from previous runs or connections SHALL NOT replace the selected run's values.

#### Scenario: Inspect a date
- **WHEN** valid report, equity and allocations are returned and the user selects an evaluation date
- **THEN** Results shows the measured wealth and weights for that date, preserving asset order and conventions

#### Scenario: Reject incompatible result views
- **WHEN** an equity or allocations view disagrees with the measured report's dates or strategies, or equity disagrees with its cost
- **THEN** that view shows an unavailable state with a retry action while the valid report remains visible

#### Scenario: A previous run completes loading late
- **WHEN** a result response arrives after another run is selected or the connection changes
- **THEN** it cannot replace the current result

### Requirement: Adapt result controls to large text
The client SHALL preserve system text scaling and SHALL stack result metrics and strategy/date controls into one column on narrow windows or at large text sizes. Essential actions SHALL remain at least 48 logical pixels tall, expose disabled and busy state where applicable, and commit only on activation rather than press-down. Metric label/value pairs SHALL be available as a single named assistive-reading group. Automated layout checks SHALL NOT be reported as rendered or physical-device acceptance.

#### Scenario: Inspect results with large system text
- **WHEN** the user inspects a measured report at 200% system text scaling
- **THEN** metric groups and strategy/date controls use a single column with wrapping text and without suppressing font scaling

#### Scenario: A submission is pending
- **WHEN** Start experiment is awaiting service acceptance
- **THEN** the action exposes disabled and busy state and cannot submit another run on press-down
