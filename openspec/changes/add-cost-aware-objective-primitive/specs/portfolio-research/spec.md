## ADDED Requirements

### Requirement: Provide explicit-boundary cost-aware objective math
Research math SHALL provide an unverified differentiable net-return/Sharpe prerequisite using the existing idealized target-turnover formula and stabilization. The previous target SHALL be required explicitly, with cash or normalized long-only values. Adjacent current-window targets SHALL participate in turnover gradients. Inputs SHALL have matching floating tensor shapes/devices/dtypes, finite normalized targets and finite returns above -100%; cost SHALL be a finite non-boolean real scalar within current bounds. Nonfinite arithmetic or net returns at/below -100% SHALL reject without clipping or hidden conversion.

#### Scenario: Initial cash accounting
- **WHEN** the caller explicitly supplies an all-zero previous target
- **THEN** net return paths SHALL match the existing evaluator's initial-entry target-turnover arithmetic

#### Scenario: Explicit boundary handoff
- **WHEN** a second window receives the preceding window's last target
- **THEN** its first cost SHALL use that actual target difference rather than another initial cash entry

#### Scenario: Zero cost
- **WHEN** the declared transaction cost is zero
- **THEN** net-objective loss and gradients SHALL agree with the current gross objective

### Requirement: Keep cost math separate from unselected training policy
The primitive SHALL NOT silently enable cost-aware runner/service/fold/sweep training or choose a minibatch boundary/gradient-detachment policy. Current run artifacts SHALL continue declaring actual gross-return training and evaluation-only costs. Source-only math SHALL NOT establish a paired study, preferred method, realistic execution model or paper reproduction.

#### Scenario: Primitive exists without integration or execution
- **WHEN** only the math and regression source have been written
- **THEN** the cost-aware training/study capability SHALL remain incomplete and unverified
