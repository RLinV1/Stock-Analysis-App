# change-documentation Specification

## Purpose
Keep every minor and major project modification traceable through immediate OpenSpec documentation, verification evidence, and retained change history.

## Requirements

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

### Requirement: Maintain resumable agent context
Agents SHALL maintain openspec/HANDOFF.md with current project state, confirmed decisions, assumptions, open questions, active work references, verification limitations, blockers, and next steps.

#### Scenario: Work changes the handoff context
- **WHEN** a logical change alters status, decisions, verification, blockers, or next steps
- **THEN** the agent updates the handoff alongside its implementation record and reconciles both before ending the session

#### Scenario: Another agent resumes work
- **WHEN** an agent begins a work session
- **THEN** it reads the project instructions, handoff, configuration, relevant specs, and active change artifacts and verifies them against the actual repository before editing

#### Scenario: Discovery has not selected a product
- **WHEN** candidate ideas have been discussed without user selection
- **THEN** the handoff identifies those ideas as unapproved and preserves product selection as an open decision
