## ADDED Requirements

### Requirement: Evaluate short final folds explicitly
Research evaluation SHALL support a final fold containing one observed target only through explicit opt-in, retaining its actual return, turnover, cost and wealth and a null Sharpe with its explanation. The default A0 evaluation SHALL continue requiring at least two observations. Empty, malformed or invalid allocation/return inputs SHALL remain rejected.

#### Scenario: One target remains at the requested end
- **WHEN** explicit fold evaluation contains one target
- **THEN** its actual finite result is retained with undefined Sharpe explained and without inventing another target

#### Scenario: Default A0 receives one target
- **WHEN** ordinary evaluation receives only one observation without opt-in
- **THEN** evaluation rejects the insufficient sample

### Requirement: Retain frozen models for causal walk-forward execution
Local walk-forward execution SHALL train/select only from each validated fold's prior training/validation history, retain that fold's immutable selected model/scaler and identity, and freeze them throughout its evaluation dates. Changes to later evaluation data SHALL NOT change the fitted model/scaler or earlier predictions. Requested/effective bounds and exclusions SHALL be recorded. A failed group SHALL retain partial evidence and SHALL NOT claim completion.

Explicit training counts/seeds SHALL be whole numbers rather than booleans or fractional values. Invalid settings SHALL fail before group creation or training.

#### Scenario: Future evaluation prices change
- **WHEN** prices after a fold's model-selection boundary are changed
- **THEN** its selected model/scaler remain unchanged and predictions preceding the changed input remain unchanged

#### Scenario: A boolean is supplied as a training budget
- **WHEN** an explicit walk-forward configuration uses a boolean or fractional epoch/count/seed value
- **THEN** it is rejected before any group or model is created

#### Scenario: Direct fold calls bypass the group wrapper
- **WHEN** a direct fold runner call has malformed fold identity, invalid setting types, mismatched split settings, or a boolean/fractional stop budget
- **THEN** it SHALL reject the input before dataset/device/training access without altering existing run or checkpoint evidence

### Requirement: Account continuously across fold boundaries
The aggregate walk-forward report SHALL cover every planned evaluation target once in chronological order and recompute shared target-turnover/cost/wealth metrics from recorded allocations and aligned returns, carrying the previous target across fold boundaries. It SHALL identify synthetic data and incomplete broader research/replay scope. A0 local repeat SHALL reject unsupported fold/group runs before executing training.

#### Scenario: The selected model changes at retraining
- **WHEN** the first target of a later fold differs from the preceding fold's last target
- **THEN** cost uses their actual allocation difference rather than a second initial cash entry
### Requirement: Reject invalid numerical evaluation results
Shared research evaluation SHALL reject invalid scalar transaction costs, unrepresentable input matrices and nonfinite derived accounting or metric values with an explicit validation error. Boolean/string/non-scalar costs SHALL NOT be silently coerced into a valid configured cost. Valid finite accounting SHALL retain the declared formulas, single-target opt-in and default A0 observation minimum.

#### Scenario: Finite returns overflow compounded wealth
- **WHEN** finite input returns produce nonfinite wealth or derived statistics
- **THEN** evaluation SHALL fail explicitly rather than returning an invalid result or treating an undefined numeric overflow as null Sharpe

#### Scenario: Boolean or non-scalar cost is supplied
- **WHEN** the cost is a boolean, string, array, or an unrepresentable numeric scalar
- **THEN** evaluation SHALL reject it as an invalid configured cost

#### Scenario: Complex inputs would lose imaginary data
- **WHEN** allocations or returns are supplied as complex-valued matrices
- **THEN** evaluation SHALL reject them before casting rather than discarding imaginary components

### Requirement: Validate owned fold artifacts before aggregation
Walk-forward groups SHALL reject returned child directories outside the current fold's owned root before reading their artifacts. Child provenance SHALL match the requested fold/configuration/dataset/source/runtime with JSON type distinctions preserved. Reports SHALL match the declared method/conventions, numeric transaction cost, planned dates and existing learned/baseline strategy order. Relative output roots SHALL still produce valid group-relative child references. Rejection SHALL retain failure state without publishing an aggregate report.

#### Scenario: A fold returns another directory
- **WHEN** a child returns a foreign directory or a sibling fold's directory
- **THEN** the group SHALL reject it before opening child artifact contents

#### Scenario: A child identity aliases a number with a boolean
- **WHEN** a returned child changes a numeric configuration/protocol/convention field to a boolean
- **THEN** the group SHALL reject the typed identity mismatch

#### Scenario: A relative output root is supplied
- **WHEN** the caller uses a relative local output path
- **THEN** recorded child references SHALL resolve within the resulting group and retain their model/report hashes
### Requirement: Reject ambiguous local control and artifact JSON
The explicit walk-forward configuration, owned dataset snapshot manifest and returned fold artifact readers SHALL reject duplicate object fields, nonstandard nonfinite constants and floating-point exponents that overflow finite representation. Artifact readers expecting objects SHALL reject other top-level JSON types. Rejection SHALL occur before training for configuration/snapshot input and before aggregation for returned artifacts. This local policy SHALL NOT imply external replay import/authentication support.

#### Scenario: Child report repeats a field
- **WHEN** a returned fold report contains duplicate JSON fields
- **THEN** the group SHALL reject it before allocation aggregation

#### Scenario: A numeric token becomes infinity
- **WHEN** JSON contains a floating-point numeric token outside finite representation
- **THEN** parsing SHALL reject it rather than silently constructing infinity
### Requirement: Declare the existing local objective and cost scope
Current A0-derived local LSTM runs and their walk-forward groups SHALL retain the implemented gross-return stabilized negative-Sharpe objective, its training/validation scope and variance stabilization in identity and report metadata. They SHALL state that transaction costs are applied in evaluation and are not included in training or validation loss. Group composition SHALL reject inconsistent objective declarations. Recording this behavior SHALL NOT change the algorithm or claim cost-aware training or exact paper reproduction.

#### Scenario: A cost is configured for local training
- **WHEN** the current local LSTM run is configured with transaction costs
- **THEN** retained metadata SHALL identify those costs as evaluation-only and retain the actual gross-return objective/stabilization

### Requirement: Preserve current-source A0 repeat identity
The local A0 repeat path SHALL include the retained objective in current input identity and reject unsupported/missing declarations without silently migrating a reference. Immutable input fields SHALL compare exactly with JSON type distinctions. Objective, convention and configured-cost metadata SHALL compare exactly rather than using numeric output tolerance. Numerical output comparisons SHALL retain their existing 1e-7 absolute bound. Invalid reference metadata SHALL be rejected before training, with reference evidence unchanged and a retained non-match outcome. This SHALL NOT imply external v2 replay verification.

#### Scenario: Fresh A0 run contains objective metadata
- **WHEN** a current-source A0 run is repeated with matching inputs and environment
- **THEN** objective metadata SHALL participate in identity preflight rather than causing a false old-field digest mismatch

#### Scenario: A metadata change is smaller than output tolerance
- **WHEN** objective/convention/configured-cost metadata differs by less than the numeric output tolerance
- **THEN** it SHALL still be a mismatch rather than a numerical match
### Requirement: Retain finite local comparison diagnostics
Local A0 comparison SHALL compare integral outputs exactly without unsafe float conversion and SHALL label numeric type mismatches. A numeric difference outside finite reporting range SHALL be a mismatch with an explicit overflow indicator; its maximum absolute difference SHALL be null rather than infinity or misleading zero. Comparison reports SHALL remain serializable with nonfinite JSON disallowed. Reference observation counts SHALL be integer counts matching recorded dates before repeat training is attempted.

#### Scenario: Finite operands have an unrepresentable difference
- **WHEN** two finite compared values have an absolute difference outside finite reporting range
- **THEN** the comparison SHALL retain a mismatch and explicit overflow indicator with null maximum, without emitting infinity

#### Scenario: Reference observation count is malformed
- **WHEN** the reference count is not an integer matching its date series
- **THEN** repeat preflight SHALL reject it before training and retain a non-match comparison report
### Requirement: Retain dataset-derived baseline omissions
Walk-forward groups SHALL validate each fold's baseline omission declaration against the available baseline strategies derived from owned dataset roles. Malformed, missing or incorrect omission declarations SHALL fail before allocation aggregation, including in the first fold.

#### Scenario: First fold declares unsupported omissions
- **WHEN** the first returned fold has a malformed or incorrect baseline omission declaration
- **THEN** the group SHALL fail instead of propagating that declaration into a completed aggregate
### Requirement: Aggregate without rebuilding training windows
Walk-forward account aggregation SHALL recover only its planned evaluation returns from owned adjacent price rows using the same float32 return conversion as fold samples. It SHALL NOT rebuild training/validation feature windows or refit a scaler merely to recover those returns. Numerical account/date conventions SHALL remain unchanged.

#### Scenario: A completed fold is aggregated
- **WHEN** its recorded allocations are accepted for group accounting
- **THEN** aggregation SHALL use aligned evaluation returns identical to the fold sample targets without constructing another fold training tensor
### Requirement: Reconcile owned fold accounting before completion
Walk-forward composition SHALL recompute each owned fold's local-entry evaluator result from recorded allocations, aligned owned returns and declared cost, and require its saved strategy report to match the current evaluator's complete typed JSON result before accepting that fold. Missing/extra fields, changed metrics/paths and invalid null/type declarations SHALL fail the group without publishing an aggregate. This local consistency check SHALL NOT claim model prediction replay or external artifact authenticity.

#### Scenario: Saved report disagrees with allocations
- **WHEN** a completed owned fold has plausible metadata but its numeric report or result shape differs from recomputed local accounting
- **THEN** the group SHALL reject that fold and retain failed-group evidence instead of referencing inconsistent local results from a completed group
### Requirement: Validate recorded resume identity before training
Current local fixed-holdout and direct-fold resume SHALL parse saved manifest/status controls with the shared strict JSON policy and compare actual recorded identity fields, protocol presence, schema and method/conventions with requested current inputs before training. Matching only a self-declared identity hash SHALL NOT permit edited manifest fields. Unsupported status or incompatible metadata SHALL reject without replacing existing manifest/status/checkpoint evidence. This SHALL NOT imply external checkpoint authentication or durable service resume.

#### Scenario: Manifest changed but old identity hash retained
- **WHEN** a saved manifest field changes while its identity hash still equals the requested run's hash
- **THEN** resume SHALL reject before training rather than producing new results under inconsistent retained metadata

#### Scenario: Ambiguous saved resume controls
- **WHEN** saved manifest/status JSON repeats fields or declares an unsupported state/schema/protocol
- **THEN** resume SHALL reject before training and preserve the existing evidence
### Requirement: Reject invalid objective intermediates
The stabilized local Sharpe loss SHALL reject nonfinite mean, variance or final loss explicitly. Finite returns whose variance overflows SHALL NOT be treated as a finite zero objective through division by infinity. The existing ordinary formula, epsilon and gradients SHALL remain unchanged. The isolated net-objective primitive SHALL share this guard without enabling cost-aware runner training.

#### Scenario: Finite gross returns overflow population variance
- **WHEN** the loss receives finite portfolio returns whose variance is nonfinite at the declared tensor precision
- **THEN** it SHALL raise an explicit validation error rather than supply a zero objective for training or model selection
