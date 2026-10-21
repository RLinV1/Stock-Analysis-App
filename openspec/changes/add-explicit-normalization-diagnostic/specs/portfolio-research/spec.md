## ADDED Requirements

### Requirement: Declare bounded normalization diagnostic mode
Local fixed-holdout research SHALL accept explicit train-only standardization or raw-input identity transform, retaining train-only as the existing default. Both modes SHALL preserve next-return alignment, chronological masks, target values and float32 conversion. Raw mode SHALL record zero mean/unit scale rather than fitted statistics and SHALL reject nonfinite conversion without silently changing mode.

#### Scenario: Explicit raw input control
- **WHEN** a caller selects raw normalization for a local fixed-holdout run
- **THEN** the runner SHALL use unstandardized prior-window price/return features with the same targets/splits and retain the selected mode and identity transform in run/model metadata

#### Scenario: Normalization is omitted
- **WHEN** an existing local caller uses the default
- **THEN** the train-only standardization operations and intended numerical behavior SHALL remain unchanged

### Requirement: Bind preprocessing mode to local identity
Normalization mode SHALL participate in config/run/checkpoint identity and retained deviations. A changed mode SHALL reject local resume while preserving prior evidence. Current-source raw references SHALL use the existing bounded local repeat path without implying external verification. Invalid modes SHALL reject before dataset/device/training access.

#### Scenario: Resume under a different mode
- **WHEN** a paused local run is resumed with a different normalization mode
- **THEN** resume SHALL reject incompatible inputs before training and preserve its manifest/status/checkpoint

### Requirement: Preserve existing service and fold normalization scope
Bounded synthetic service execution SHALL explicitly retain train-only normalization without changing its closed request schema. Walk-forward groups/sweeps SHALL retain their existing config scope. Raw direct-fold execution SHALL be rejected before runtime access until separately scoped and verified.

#### Scenario: Raw direct fold is requested
- **WHEN** a direct fold caller selects raw normalization
- **THEN** it SHALL reject before dataset/device/training access rather than silently extending the fold protocol

#### Scenario: Diagnostic controls are written but not executed
- **WHEN** controls and regression source exist without a completed paired study
- **THEN** documentation SHALL identify them as unverified controls and SHALL NOT report a preferred mode or completed normalization finding
