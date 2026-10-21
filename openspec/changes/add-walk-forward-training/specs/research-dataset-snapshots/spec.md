## ADDED Requirements

### Requirement: Bind local research snapshots to preflight inputs
Before training any walk-forward fold, the group SHALL copy its validated dataset into a fresh group-owned snapshot directory. The copied manifest SHALL retain its original bytes and describe the same manifest content validated during preflight. The group SHALL copy only the declared dataset CSV and validate the copied dataset before training. A coherent replacement of the source manifest after preflight SHALL cause rejection rather than silently changing the experiment inputs.

#### Scenario: Original manifest changes after preflight
- **WHEN** the input manifest content changes between preflight and copying
- **THEN** snapshot creation SHALL reject that change before any fold trains

#### Scenario: Source CSV changes during copying
- **WHEN** the copied CSV no longer satisfies the preflight manifest's data validation
- **THEN** the group SHALL reject the snapshot before training

### Requirement: Preserve snapshot ownership and relative paths
Snapshot creation SHALL reject an existing destination directory and SHALL NOT alter its contents. The declared CSV SHALL be a filename alongside the manifest, matching the existing public dataset-loader contract; nested directories and path prefixes SHALL be rejected. It SHALL NOT escape through parent traversal or a drive-qualified path or collide with the snapshot manifest. Invalid paths SHALL be rejected before creating the snapshot directory. A newly created partial snapshot MAY remain after a copy or validation failure and SHALL NOT be treated as a completed experiment.

#### Scenario: Destination already contains evidence
- **WHEN** the destination directory already exists
- **THEN** snapshot creation SHALL fail without replacing its files

#### Scenario: CSV points outside the dataset
- **WHEN** the CSV path is absolute, drive-qualified, or includes parent traversal
- **THEN** snapshot creation SHALL reject it before output creation

#### Scenario: Windows path aliases a reserved destination
- **WHEN** the CSV path contains a trailing dot/space component or alternate-stream separator
- **THEN** snapshot creation SHALL reject it before output creation
