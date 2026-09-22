## Purpose

Bind a recorded run to a retrievable source revision, so that the code which produced a result can be recovered rather than only fingerprinted.

## ADDED Requirements

### Requirement: Record a retrievable source revision for each run
A recorded run SHALL capture the repository commit identifier and whether the working tree contained uncommitted modifications to tracked source at execution time. A content fingerprint MAY be recorded in addition, and SHALL NOT be presented as equivalent to a commit identifier.

#### Scenario: Run executes from a clean tree
- **WHEN** a run executes with no uncommitted modifications to tracked numerical source
- **THEN** its record contains the commit identifier and indicates a clean tree

#### Scenario: Run executes from a modified tree
- **WHEN** a run executes while tracked numerical source differs from the recorded commit
- **THEN** its record indicates the modification, and the run is not presented as reproducible from that commit alone

#### Scenario: No repository is available
- **WHEN** a run executes outside a repository
- **THEN** the absence of a source revision is recorded explicitly rather than implied by a fingerprint
