## ADDED Requirements

### Requirement: Check controlled synthetic learnability
Research verification SHALL include a deliberately simple synthetic two-asset case with an analytically preferred long-only allocation under the implemented stabilized gross-return objective. It SHALL verify the analytic bound and exercise the actual chronological data/preprocessing/training/validation-selection/held-out runner path. Asset order SHALL be reversed in a second case. Fixture settings and acceptance thresholds SHALL be declared before execution, and all cases SHALL be reported without favorable selection. The check SHALL retain ordinary run evidence and SHALL NOT imply historical prediction, paper reproduction or a new research preset.

#### Scenario: Learn the known preferred asset
- **WHEN** the real CPU runner trains on controlled constant positive versus negative return assets with explicit fixture settings
- **THEN** the held-out mean preferred-asset weight SHALL reach at least 0.95, best validation loss SHALL be at most -18, and cumulative return SHALL exceed equal weight
- **AND** those expectations SHALL be checked for both asset orderings without threshold tuning on held-out outcomes

#### Scenario: Verification is prohibited or the gate fails
- **WHEN** the model has not been run or a declared check fails
- **THEN** the capability SHALL remain unverified and its task SHALL remain incomplete with the limitation or failure recorded
