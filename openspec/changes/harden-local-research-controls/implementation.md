# Implementation record

## Planning — 2026-10-17

Read AGENTS.md, current HANDOFF/config, portfolio-research main spec, active objective-window proposal/design/spec/tasks and actual CLI/runner/shared JSON code. Scope/rationale/tasks/spec delta recorded before implementation. Identified explicit discrepancy with the older alternate-only validation scope; root was notified to reconcile shared artifacts. No source edits, project execution or verification yet.

## Control boundary source — 2026-10-17

Local run explicit config and saved resume manifest now use load_json_object. A narrow _run_config constructor validates object shape, translates missing/unknown fields into ValueError usage errors and validates before runner dispatch; bounded CLI defaults also validate before dispatch. RunConfig.validate now invokes shared strict types unconditionally before mode/range/device checks. Shared validation includes split endpoint string types when present (group preflight objects need not yet have fold-derived split dates). No training/model/loss/default/schema changes. Source inspection confirms edited branches; no project imports, tests, CLI, CUDA or other project processes ran. Regression source and execution gates remain pending.

## Regression source — 2026-10-17

Added test_local_controls.py with explicit/resume malformed JSON/object/constructor cases, nested duplicate resume metadata, invalid typed controls, no-runner-dispatch and forbidden CUDA/data/runtime/training sentinels, saved-byte preservation, and valid default/raw/full-training config forwarding. Direct default RunConfig cases cover type failures before runtime, including huge integers and boolean/fractional counts. A stubbed bounded-default CLI case checks preserved epochs/seed/cost and inferred split positions without training. Every case is written but unrun. No syntax/test/OpenSpec/CLI check or project import occurred, so compatibility is not established and tasks remain unchecked.
