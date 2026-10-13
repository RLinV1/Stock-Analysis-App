## ADDED Requirements

### Requirement: Call the runs API only through a contract-checked client
The mobile client SHALL send run requests only after validating them against synthetic request v1, SHALL send the bearer credential and Idempotency-Key, and SHALL report network failures, timeouts, problem responses and malformed responses as typed errors without inventing a run ID or state. Error messages SHALL never contain the bearer credential.

#### Scenario: Server returns an unexpected body
- **WHEN** a status response lacks a valid run state
- **THEN** the client raises an invalid-response error instead of returning a status

#### Scenario: Invalid draft
- **WHEN** the caller submits a request outside the v1 bounds
- **THEN** the client raises an invalid-input error and makes no network call
