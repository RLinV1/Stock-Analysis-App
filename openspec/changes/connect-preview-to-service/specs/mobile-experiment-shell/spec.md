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
