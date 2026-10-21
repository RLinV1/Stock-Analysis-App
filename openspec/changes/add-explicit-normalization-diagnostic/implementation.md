# Explicit normalization diagnostic history

## Planned file-only implementation — 2026-10-17

Read actual sampler, runner, service adapter, model declarations and data/fold regressions, plus approved A1 task3.5 and SPEC's unresolved normalization experiment. Defined narrow fixed-holdout controls before code: preserve existing train-only behavior, add explicit raw identity transform with mode-bound metadata, pin service behavior and reject raw direct folds. No paired study/default decision, CLI validation or project/test/model/GPU/process execution is authorized. Planning artifacts were written manually; all verification remains open.
## Explicit mode source written — 2026-10-17

Added shared mode validation and keyword-only sampler normalization. The train-only branch preserves existing fit/arithmetic by design; raw mode uses explicit zero/unit transform with unchanged features, masks, targets and finite float32 guard. RunConfig now appends the mode field, binds it through existing identity/checkpoint/model config, dispatches fixed-holdout sampling and retains an accurate deviation. Direct folds reject raw before data/device/training access. The service adapter explicitly selects train-only without a request schema change. No source import, numerical execution, test, model, GPU or command ran; compatibility and paired-study outcomes remain unverified.
## Normalization regression source written — 2026-10-17

Added test_normalization.py: exact default/explicit train-only parity, raw feature/alignment/target/mask and identity-transform checks, future-mutation causality, finite conversion rejection, invalid-mode no-runtime guards, raw direct-fold rejection and explicit service pin. A shared future CPU raw reference supports real run/artifact/epoch-resume/local-repeat checks plus changed-mode evidence preservation. Those are unrun assertions, not observed numerical equivalence or learning results. Source-only caller review found no fixed-signature sampler monkeypatch needing adaptation. No tests, imports, models, project commands or GPU work ran.
## Diagnostic source guide written — 2026-10-17

Added NORMALIZATION-DIAGNOSTIC.md with exact mode semantics, identity-transform disclosure, fixed-holdout-only boundaries, explicit existing config entry point, finite-conversion/saturation risks and future regression/paired-study gates. README, DESIGN and HANDOFF link the source-only controls and preserve service/fold preprocessing scope. No preferred mode, empirical result or new numeric preset is claimed. No command, link/OpenSpec validation, import, test, model or GPU work ran.
## Canonical source-status reconciliation — 2026-10-17

Canonical SPEC section4, requirements coverage and OpenSpec context now distinguish prior prototype evidence from current walk/sweep/learnability/normalization source. Recorded local raw/train-only mode identity, service/fold constraints and the absence of any paired-study finding. SPEC section8's preset values/acceptance question is unchanged. No implementation task is complete without its required execution; no CLI/link validation or project/model/GPU execution ran.
## Planned explicit fold/default pins — 2026-10-17

Follow-through source review: now that normalization is selectable locally, explicitly pass train-only in the fold config adapter and fold sample adapter as well as the service, keeping the existing fold contract independent of a future RunConfig/sampler default change. Pin the previously frozen learnability fixture to train-only and record that setting before any run. Add a no-training fold-config assertion. This is contract preservation, not extending raw mode to A1 groups or accepting a new default. No execution will occur.
## Explicit fold pins source written — 2026-10-17

Fold config and sample adapters now explicitly select train-only normalization, matching the pinned service and existing protocol rather than relying on the newly selectable local default. Added a no-training fold-config source assertion. The known-allocation fixture is explicitly pinned to its original train-only mode before any run. Group/sweep configs gain no raw option. All compatibility/learnability tests, imports, models and GPU/process work remain unrun.
## Planned explicit raw setting-type follow-through — 2026-10-17

Share the objective-control follow-through's strict type preflight for explicitly selected raw mode, retaining legacy default A0 validation scope. Reject malformed budgets/numerics/device values before device/data access. This closes a new-control input gap without changing accepted numeric settings or running a paired study; all checks will remain unrun.
## Raw control setting-type source written — 2026-10-17

Explicit raw normalization now uses the shared strict integer/finite-numeric/device-type preflight before device/data access. The combined objective-window suite contains unrun raw/full-training malformed-setting cases; default A0 validation scope remains unchanged. No source/test/model/device/GPU/process execution occurred; this is not a completed normalization study.
