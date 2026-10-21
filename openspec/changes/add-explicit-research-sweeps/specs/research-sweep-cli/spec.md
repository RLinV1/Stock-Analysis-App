## ADDED Requirements

### Requirement: Explicit local training invocation
The local sweep training entry point SHALL require an explicit dataset manifest, versioned configuration file and output root. Its version 1 configuration SHALL contain exactly the common model settings and sweep settings. All declared model fields, unique seeds, transaction costs and candidate budget SHALL be supplied; unknown or missing fields SHALL be rejected. The loader SHALL reject duplicate JSON fields and nonstandard nonfinite constants. The CLI SHALL dispatch to the sequential snapshot-bound executor without changing the requested grid or common settings.

#### Scenario: Caller omits a seed grid or common model setting
- **WHEN** the training configuration omits required fields
- **THEN** the CLI SHALL report invalid input and SHALL NOT start the executor

### Requirement: Honest training command exit status
The training entry point SHALL return success status 0 only for complete, all-successful coverage. Complete coverage containing failed or invalid candidates SHALL return status 1 and identify the retained group directory. Invalid input or a failed group invocation SHALL produce a nonzero error status. Interrupted execution SHALL NOT be reported as success.

#### Scenario: One candidate fails in a completed sweep
- **WHEN** execution returns a completed-with-failures group
- **THEN** the CLI SHALL identify the retained group and return status 1

#### Scenario: Every candidate succeeds
- **WHEN** execution returns complete and all-successful coverage
- **THEN** the CLI SHALL identify the retained group and return status 0
