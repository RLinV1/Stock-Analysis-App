## ADDED Requirements

### Requirement: Declare local objective-window controls
Local fixed-holdout research SHALL support explicit minibatch and full-training objective windows, retaining minibatch as the existing default. Full-training mode SHALL make one optimizer update per epoch over training targets only; validation SHALL continue selecting on all validation targets. The stabilized gross-return loss formula and epsilon SHALL remain unchanged. Recorded identity, report/model config and objective scope SHALL match the selected control, and history SHALL retain actual optimizer-step counts.

#### Scenario: Full-training window selected
- **WHEN** a local fixed-holdout config selects full-training
- **THEN** every epoch SHALL compute its objective over all training targets in one update, exclude validation/test targets and record that scope and update count

#### Scenario: Minibatch already contains all training targets
- **WHEN** both controls use the same seed/data/settings and configured batch size covers all training targets
- **THEN** their numerical model/history/strategy outputs SHALL agree apart from declared method metadata

### Requirement: Preserve bounded method identity and scope
Invalid objective windows SHALL reject before device/data/training access. Changing a local window SHALL reject resume while preserving prior evidence; current-source repeat SHALL validate the actual objective declaration for config. Service and fold execution SHALL explicitly retain minibatch training; full-training direct folds SHALL reject before runtime access. Request/group/sweep schemas SHALL remain unchanged.

#### Scenario: Changed window on resume
- **WHEN** a paused local run is resumed under a different objective window
- **THEN** the runner SHALL reject incompatible identity before training and preserve saved evidence

### Requirement: Disclose objective diagnostic limitations
Controls without a completed study SHALL remain labeled unverified. Documentation SHALL disclose that full-training may use more memory and generally changes optimizer updates per epoch; it SHALL NOT present the modes as an isolated batch-size experiment or choose a method from held-out results. No cost-aware objective or paper reproduction SHALL be implied.

#### Scenario: Only source controls exist
- **WHEN** a diagnostic mode and regression cases have been written but not executed
- **THEN** no empirical comparison, preferred mode or completed A1 study SHALL be claimed
### Requirement: Preflight alternate local diagnostic settings strictly
Explicit raw normalization or full-training objective controls SHALL use whole-number counts/seeds, finite non-boolean learning-rate/cost values and a declared device string before device/data/training access. Invalid diagnostic settings SHALL fail before output creation. This SHALL preserve the legacy default path's existing validation scope and SHALL NOT introduce new numeric presets.

#### Scenario: Alternate control has a malformed budget
- **WHEN** raw or full-training is selected with boolean/fractional counts or unrepresentable numeric settings
- **THEN** validation SHALL reject before a device probe, dataset read or output directory is created
