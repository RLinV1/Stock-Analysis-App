## ADDED Requirements

### Requirement: Explicit offline sweep input
The research tooling SHALL provide an offline summary entry point accepting an explicit input file and new output file. The input SHALL declare integer schema version 1, a settings object containing exactly seeds, costs_bps, and max_runs, and a records array. Neither seeds nor transaction costs SHALL have implicit defaults. The loader SHALL reject unknown top-level or settings fields, duplicate JSON object fields, and nonstandard nonfinite JSON constants.

#### Scenario: Ambiguous settings are rejected
- **WHEN** an input repeats a JSON field or omits the explicit candidate budget
- **THEN** the tool SHALL reject the input before creating output

#### Scenario: Summary processing has no training side effect
- **WHEN** an offline summary document is processed
- **THEN** the entry point SHALL summarize its supplied records without launching training, worker children, or services
- **AND** the report SHALL not represent supplied context as authenticated artifacts

### Requirement: Complete terminal grid and honest statistics
The summary SHALL retain exactly one terminal record for every requested seed and cost combination. Allowed terminal states SHALL be completed, failed, and invalid. Failed and invalid candidates SHALL retain a reason. Coverage completeness and all-candidate success SHALL be reported separately. Completed candidates SHALL share dataset identity, common settings identity excluding seed and cost, method label, ordered test dates, and strategy set. Numeric metrics and derived comparisons SHALL be finite. Null Sharpe values SHALL retain explanations and SHALL not be converted to zero.

#### Scenario: Complete grid containing failures
- **WHEN** every requested candidate has a terminal record and one or more records failed
- **THEN** coverage SHALL be complete and all-successful SHALL be false
- **AND** failure reasons and counts SHALL remain visible

#### Scenario: Missing result prevents summary completion
- **WHEN** a requested candidate is missing, duplicated, unrequested, or still running
- **THEN** the tool SHALL reject the input before creating output

#### Scenario: Failed middle cost is not skipped
- **WHEN** two successful tested costs are separated by a failed tested cost
- **THEN** their intervening adjacent intervals SHALL be unavailable
- **AND** the tool SHALL not bridge the failure to infer a break-even threshold

### Requirement: Preserve existing summary evidence
The offline summary entry point SHALL validate and serialize a summary before creating its output and SHALL exclusively create a new output file. It SHALL refuse to replace an existing file, including its input. A failure or interruption during writing MAY leave a partial newly created file; the documentation SHALL disclose this limitation and require consumers to parse and validate files.

#### Scenario: Output already exists
- **WHEN** an output file already contains prior results
- **THEN** summary creation SHALL fail and preserve those contents

#### Scenario: Invalid document has no output side effect
- **WHEN** input validation fails before writing
- **THEN** no output file SHALL be created
### Requirement: Reject impossible completed metric values
Completed strategy metrics SHALL satisfy the existing evaluator's domains: cumulative return SHALL be at least -1, volatility/turnover/cost SHALL be nonnegative, and maximum drawdown SHALL be between 0 and 1 inclusive. These domain checks SHALL apply in addition to finite-number, observation-count and null-Sharpe checks. Rejected candidate metrics SHALL NOT contribute numeric observations.

#### Scenario: A completed record declares negative drawdown
- **WHEN** a supplied completed strategy has negative maximum drawdown or negative volatility/turnover/cost
- **THEN** summary validation SHALL reject that record

#### Scenario: A return below total loss is supplied
- **WHEN** a cumulative return is less than -1
- **THEN** summary validation SHALL reject it before any cost comparison

### Requirement: Parse owned sweep artifacts consistently
Owned candidate artifacts and training completion status SHALL use the same unambiguous JSON policy as explicit sweep input: duplicate fields and nonfinite constants SHALL be rejected, as SHALL floating-point exponent overflow. Captured hashes SHALL remain hashes of the exact bytes parsed. This consistency check SHALL NOT be presented as external artifact authentication.

#### Scenario: An apparently completed artifact has duplicate status fields
- **WHEN** a candidate status or report repeats a JSON object field
- **THEN** the candidate SHALL be invalid and SHALL NOT contribute summary metrics
