# Explicit Sharpe-window diagnostic history

## Planned file-only implementation — 2026-10-17

Read actual loss, runner batch/checkpoint loop, objective identity/repeat guards and existing normalization/fold/service pins. A1 task3.6 authorizes the diagnostic scope; define explicit fixed-holdout controls and verification gates before implementation. Preserve the current loss/default schedule, record full-training scope/update counts and keep service/fold methods fixed. All planning artifacts were written manually, without OpenSpec CLI validation. No source import, test, training, model, service, shell or GPU execution is authorized.
## Objective-window control source written — 2026-10-17

RunConfig now appends objective_window with the existing minibatch default and pre-device validation. Full-training uses all training targets as one optimizer batch per epoch; inference and validation prediction batching remain configured as before. Dynamic objective declarations bind actual scope to run/report identity, and history records optimizer_steps. Repeat preflight validates the objective corresponding to config. Service/fold adapters and the known-allocation fixture explicitly retain minibatch; full-training direct folds reject before runtime. Loss arithmetic, stabilization and optimizer are unchanged by design. No tests, project imports, model/training/GPU or commands ran; default/alternate numerical compatibility is unverified.
## Objective-window regression source written — 2026-10-17

Added hand-calculated fixed-weight minibatch/full-window distinction, copied/default metadata, invalid-window and unsupported-fold no-runtime cases. Future CPU references cover both train-only/raw normalization, single-batch numerical equality, dynamic objective/config/model metadata, update counts, local repeat, exact epoch resume and changed-window evidence preservation. A separate small-batch gate expects three versus one optimizer updates for 81 training targets. Service/fold preservation assertions were extended without extra model cases. All are unrun source, including expected equality/counts; no optimizer/model/test/import/GPU/process execution occurred.
## Objective-window source guide written — 2026-10-17

Added a guide documenting exact training/update/validation scopes, configured prediction batching, full-graph memory cost, identity/repeat/resume and fixed service/fold boundaries. Explicitly disclosed update-count confounding and the absence of any study/preferred-mode result. README, WALK-FORWARD and HANDOFF link the unrun controls. The learnability design/guide freeze its original minibatch scope before execution. No CLI/link/OpenSpec validation, tests, imports, models, worker/storage or GPU execution ran.
## Planned alternate-control type preflight — 2026-10-17

Before finishing the new controls, reuse strict setting-type preflight whenever raw normalization or full-training objective mode is selected. The legacy default A0 validation path stays unchanged; newly selected diagnostics should reject malformed counts/oversized numerics/device types before device/data access instead of failing later in optimization. Add no-runtime source cases for both controls. No model/test/device/process execution is authorized.
## Alternate-control type preflight source written — 2026-10-17

RunConfig validates mode names first, then reuses strict count/finite-numeric/device-type guards for selected raw/full-training controls before bounds or device probes. Legacy default A0 validation scope remains unchanged by design. Added unrun cross-control boolean/fractional/oversized/nonfinite/device-type cases forbidding data/device/training access and output creation. No project imports, tests, models, GPU probes or processes ran.
## Canonical control-status reconciliation — 2026-10-17

SPEC section4, DESIGN, requirements coverage, OpenSpec context and handoff now link the new source-only controls, actual objective/update scope, strict alternate-setting preflight and fixed service/fold defaults. Full-training memory/update confounds and the absence of any paired-study/preferred-method result remain explicit. Numeric preset acceptance and broader A1/B/C/D gates are unchanged. No project command, validation, model, test, provider or GPU execution ran.
