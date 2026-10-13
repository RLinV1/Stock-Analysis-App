## ADDED Requirements

### Requirement: Connect only after a successful service response
The client SHALL treat the service as connected only after an authenticated run list request succeeds, SHALL keep the base URL and token in memory only, SHALL never display the token, and SHALL show only runs and states returned by successful responses.

#### Scenario: Token rejected
- **WHEN** the user connects with a token the service rejects with 401
- **THEN** the UI says the token was rejected, stays disconnected and shows no live runs

#### Scenario: Retry a submission
- **WHEN** a submission fails with a network error and the user retries the same draft
- **THEN** the client sends the same idempotency key so the service cannot create a second run
