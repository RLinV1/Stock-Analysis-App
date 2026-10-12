## ADDED Requirements

### Requirement: Bound the first synthetic request
The local contract SHALL accept only version 1 synthetic fixed-holdout requests with the documented integer fields and limits, reject unknown or missing fields, and reject unsupported versions before creating a run.

#### Scenario: Reject an invalid request
- **WHEN** a caller supplies an unsupported version, unknown field, boolean integer, or out-of-range training budget
- **THEN** validation fails and no run output is created

### Requirement: Give equivalent requests stable identity
The adapter SHALL compute a SHA-256 request hash from canonical UTF-8 JSON independent of object-key order and SHALL retain the accepted request and hash with the resulting local run.

#### Scenario: Reorder request properties
- **WHEN** two otherwise identical JSON requests have different object-key order
- **THEN** they receive the same request hash

### Requirement: Execute one local synthetic request
The CLI SHALL generate the labelled synthetic dataset, derive the fixed A0 split, execute the CPU research runner, and retain its report and copied input without claiming durable service behavior or historical performance.

#### Scenario: Run the example
- **WHEN** the example one-epoch request is executed locally
- **THEN** a completed A0 run contains a report, copied synthetic dataset, accepted request, and request hash
