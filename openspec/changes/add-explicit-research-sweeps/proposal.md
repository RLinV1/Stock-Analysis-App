## Why

Approved A1 task3.8 requires multi-seed/cost sweeps, with honest failure and variability reporting. The current runner and new unverified fold draft produce individual reports but no complete candidate inventory or descriptive sweep summary.

## What Changes

- Require caller-declared unique seeds, costs and a maximum candidate count; adopt no new seed/cost defaults.
- Retain every requested seed/cost cell, including failure or invalid-result state.
- Produce descriptive counts/mean/population spread and null explanations without selecting favorable runs.
- Retain/check the actual gross-return objective and disclose that current costs affect evaluation only, without implying cost-aware training.
- Compare learned/baseline differences only at tested costs; label missing comparisons and avoid invented crossing thresholds.
- Add sequential local execution source with fixed snapshot/settings and retained per-run identity, plus explicit standalone offline/training entry points; keep all runtime acceptance gates open until verified.

## Capabilities

### New Capabilities

- `research-sweep-reporting`: strict offline input, complete terminal-grid summaries and preservation of existing output.
- `research-sweep-execution`: sequential snapshot-bound local candidate execution, identity checks and retained partial/failure state.
- `research-sweep-cli`: explicit local training configuration and honest success/failure exit status.

### Modified Capabilities

- `portfolio-research`: explicit bounded sweep coverage and honest descriptive comparison.

## Impact

New local research sweep source/tests and documentation. Current work is code-only and unverified; no shell, tests, CLI, build, Git, service or model process is authorized. Full historical seed/cost evidence, seven-baseline scope, defaults acceptance, external replay and service/UI integration remain open.
