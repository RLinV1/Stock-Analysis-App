## ADDED Requirements

### Requirement: Document every logical change
The project SHALL maintain an OpenSpec record for every logical modification, including minor fixes, major features, tooling, infrastructure, and documentation.

#### Scenario: A logical modification is completed
- **WHEN** an agent completes a logical modification
- **THEN** it immediately updates the associated change with the modification summary, verification outcome, and known limitations before reporting completion

### Requirement: Preserve validated history
Completed changes SHALL be validated and archived with implementation evidence, updating capability specs when applicable.

#### Scenario: A change is complete
- **WHEN** implementation and documentation tasks are complete
- **THEN** the agent validates and archives the change while preserving its implementation record
