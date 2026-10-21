## ADDED Requirements

### Requirement: Parse local run controls unambiguously before dispatch

The local run CLI SHALL load explicit configuration and saved resume configuration as strict UTF-8 JSON objects, rejecting duplicate fields, nonfinite constants, overflowing floating-point tokens, missing config objects and missing/unknown RunConfig fields as usage errors before experiment dispatch. Saved input evidence SHALL remain unchanged on rejection.

#### Scenario: Resume manifest contains ambiguous configuration

- **WHEN** a saved manifest contains duplicate fields or a missing/non-object config
- **THEN** the CLI SHALL exit with a clear usage error before calling the runner or altering saved artifacts

### Requirement: Preflight every local training control strictly

RunConfig validation SHALL reject boolean/fractional counts or seeds, nonfinite/non-numeric scalar settings, non-string split endpoints and invalid device types before bounds/device/data/training access. This SHALL apply to default train-only/minibatch and alternate diagnostic modes alike. Valid defaults, allowed numeric bounds and algorithm behavior SHALL remain unchanged.

#### Scenario: Default mode has malformed count or cost

- **WHEN** a default fixed-holdout config contains a boolean/fractional count or unrepresentable cost
- **THEN** validation SHALL raise a configuration error before CUDA probing, dataset reading, output creation or training
