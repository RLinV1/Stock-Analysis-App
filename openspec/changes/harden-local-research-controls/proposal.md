## Why

Local fixed-holdout run/resume CLI config loading still accepts ambiguous JSON and lets malformed mappings escape as Python errors. Default train-only/minibatch RunConfig validation also skips the shared strict type preflight used by alternate controls. Reject malformed controls before dispatch or runtime access while preserving every valid default and numerical operation.

## What Changes

- Parse local run config and saved resume manifest with the shared strict UTF-8 JSON object loader; reject duplicate fields, nonfinite/overflow floats and non-object config values.
- Translate missing/unknown constructor fields into clear CLI usage errors and validate constructed configs before dispatch.
- Apply strict count, scalar, split-string and device types universally in RunConfig.validate before bounds/device probes.
- Add source-only invalid-input/no-dispatch/no-runtime and valid-default compatibility cases; no execution is authorized by this change.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `portfolio-research`: unambiguous local run/resume controls and strict preflight for all local configurations.

## Impact

Research CLI, runner validation and narrow regression source. Valid default train-only/minibatch settings, method scopes and numerical algorithms remain unchanged. This deliberately supersedes the earlier objective-window draft's promise to preserve legacy invalid-input validation scope; it does not select numeric presets or broaden service/group schemas.
