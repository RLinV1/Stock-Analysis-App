## ADDED Requirements

### Requirement: Scan locally reachable Git history without revealing secret values
The local scanner SHALL offer an explicit history mode that inspects unique Git objects reachable from all local references, HEAD and reflogs, including removed blobs, commit/tag messages and sensitive tree-entry filenames. It SHALL disable Git replacement objects during inspection, reject shallow repositories and report failures without raw Git diagnostics or matched values. Existing detector, allowlist, binary and content-size limitations SHALL be documented; a clean result SHALL NOT be described as publication approval.

#### Scenario: A secret was committed and subsequently removed
- **WHEN** history mode scans a repository containing an earlier matching secret
- **THEN** it reports a nonzero finding with an object identifier, rule and line without printing the secret or its prefix

#### Scenario: Historical content is absent from the current branch
- **WHEN** matching content is reachable only from another local reference or reflog
- **THEN** history mode still reports it

#### Scenario: History is incomplete
- **WHEN** the repository is shallow
- **THEN** history mode fails with an explicit incomplete-history error

#### Scenario: A historical test fixture is reviewed
- **WHEN** an exact object identifier, rule and line are documented as a reviewed test fixture
- **THEN** the default history scan may exclude only that finding, an explicit unfiltered audit mode still reports it, and changed object/line/rule findings remain failures

### Requirement: Gate local commits on staged content
The repository SHALL provide a repo-owned pre-commit hook that runs the default scanner against staged blobs, preserves the scanner's failure status and fails closed when no supported Python interpreter is available. Hook activation SHALL be repository-local and preserve existing hook configuration unless reviewed explicitly.

#### Scenario: Working-tree edits differ from the index
- **WHEN** a staged secret is removed only from the working tree
- **THEN** the hook rejects the staged commit

#### Scenario: Staged content is clean
- **WHEN** an unstaged edit contains a matching secret but the staged blob is clean
- **THEN** the hook permits the clean staged content
