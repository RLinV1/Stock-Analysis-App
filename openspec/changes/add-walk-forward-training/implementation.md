# Implementation record

## Partial-state and memory source review — 2026-10-15

Failure/interruption status now retains the active fold and completed child records/hashes directly, so partial evidence does not rely solely on the last folds.json write. Extended the failure regression source to inspect that retained model identity. Released each temporary fold sample/window object immediately after copying its evaluation targets, avoiding retention of the previous fold's windows during the next training call. No resource measurement or test was run; this remains an unverified code-only refinement.

## Snapshot destination review — 2026-10-15, code only

Removed an unnecessary basename-only snapshot restriction introduced in the initial draft. Snapshot copying now preserves any relative CSV subpath already accepted by the public loader while rejecting absolute, drive-qualified and parent-traversing destination paths. Target parents are created only inside the new snapshot. This avoids silently narrowing the existing dataset contract for packaging convenience. No loader format was broadened and no execution/verification was performed.

## Final short-group regression source — 2026-10-15

Added a whole-group one-target regression requiring exactly one date/fold/wealth observation and explained null Sharpe for every strategy. This complements the metric and child-fold source cases. It remains unrun along with all code-only edits; no completion, archive, commit or successful execution is claimed.

## Child provenance and limitations — 2026-10-15, code only

Source review added pre-aggregation checks binding each completed child to the exact fold protocol, settings, snapshot manifest, source fingerprint and runtime versions. Group output now carries each child's modelling/execution deviations and consistent baseline-omission explanations. Added a source regression that alters a child's protocol and requires failed group status without an aggregate report. All remain unrun; this is source review, not successful provenance or runtime verification.

## Source-status reconciliation — 2026-10-15

README, OpenSpec context and handoff now identify the new fold/group/CLI implementation as an unverified source draft. All earlier numerical/container checks are prior-source evidence, not validation of these edits. No CLI/OpenSpec/link/secret scanner or Git process has run after the code-only instruction; these checks and commits remain pending. All change tasks remain unchecked, and no main spec sync/archive has been performed.

## Fold resume and later-fold causality regression source — 2026-10-15

Added source coverage that rejects a changed/missing fold protocol before checkpoint mutation, then resumes only the matching paused fold. Expanded the actual-file mutation case to both within-first-fold future inputs and observations wholly beyond the first fold; the latter requires identical first-fold strategy outputs. All remain unrun. Group resume remains unsupported; this source test addresses only the existing child epoch-checkpoint mechanism with explicit fold identity.

## On-disk causality/snapshot regression source — 2026-10-15, code only

Added source tests that change future prices in a separate actual CSV, replace only exact old CSV-digest references, validate the changed dataset through the public loader, and compare first-fold model/scaler and earlier predictions across real group executions. Added a test that corrupts the original CSV after the first child returns and requires later folds to use the group's validated snapshot. These are intended end-to-end checks but remain **unrun**; loader compatibility and all test assumptions still require execution/review. Added docs/WALK-FORWARD.md with explicit draft status, complete synthetic verification settings and limitations. No process or commit was started.

## Explicit configuration guards — 2026-10-15, code only

Added pre-group integer/count/seed and finite numeric setting guards, preserving existing RunConfig bounds and A0 behavior. Added rejection scenarios and parameterized source regressions for boolean/fractional counts, invalid numeric values and device types. All new work remains unrun under the user's no-process instruction; no tasks have been marked complete.

## CLI and orchestration regression source — 2026-10-15, code only

Written an explicit `walk-forward` CLI requiring a complete configuration object, plus source regressions for hand-calculated continuous boundary turnover/cost/wealth, multi-fold date/model hash retention, preserved first-fold evidence after second-fold failure, and CLI dispatch/incomplete-config rejection. Restored the original default metric error wording while keeping explicit single-row behavior. No commands, imports, tests, builds, services or commits were run. These tests and the whole fold/group implementation remain unverified; all tasks stay unchecked. A real CLI smoke and full on-disk future-mutation tests remain required before any completion/archive claim.

## Group orchestration source — 2026-10-15, code only

Written `walk_forward.py` with fully explicit caller settings, a validated local dataset snapshot, sequential fold execution, retained model/scaler/manifest/report hashes, exact chronological coverage checks, and continuous accounting recomputed from actual adjacent allocations/returns. Each group retains partial child artifacts and an interrupted/failed status rather than false completion. No group resume, service routing or external replay is added. Child reports retain local-entry costs; the aggregate recomputes one initial entry across the whole sequence. Source only: no import, test, CLI smoke or runtime execution has run. CLI wiring, orchestration regressions and full on-disk future-mutation verification are still pending; all tasks remain unchecked.

## Code-only fold runner continuation — 2026-10-15

The user subsequently prohibited starting processes and requested code only. No shell, CLI, build, test, app, service or commit process is started after that instruction. A pre-instruction metrics/protocol check had been launched, but its session/output is no longer available; do not infer a pass from it.

Written: explicit one-observation metric opt-in with unchanged default minimum and invalid-input guards; hand-calculated regression cases; optional validated fold context for the existing runner; fold-bound samples and protocol-bound checkpoint identity; frozen selected model/scaler metadata; explicit rejection of fold/group protocols in A0 repeat/comparison. Added source regressions for bounded dates/artifacts, split mismatch, one-target metrics, loaded-data future-mutation invariance and repeat rejection before training. These changes and all new tests are **unrun/unverified**. The price-injection test isolates fitting from ingestion; it does not replace the planned on-disk, multi-fold end-to-end causality check.

No group orchestration, continuous cross-fold accounting or CLI exists yet. Do not mark tasks complete or archive. Research source edits change the A0 source fingerprint; prior container/host evidence remains prior-source evidence. The built images have not been rebuilt for these research changes.

## Planned continuation — 2026-10-15, before edits

Scope follows approved A1 task3.11 and the user's sustained implementation request. Inspected the actual planner, sample adapter, runner, metrics, CLI and A0 repeat preflight. The planner permits a one-target final fold, while evaluate requires two rows; implement explicit short-fold metrics first, preserving the A0 default. Then integrate validated fold training, retain frozen models/scalers, orchestrate a local group and recompute continuous boundary costs. No new default acceptance, historical acquisition, LocalStack, phone or v2 replay claim. Package work is committed as c4ffa72; the usage window was94% used before this change, so partial work must remain honestly recorded if a limit interrupts execution.
## Planned source continuation — 2026-10-16

Before editing: extract a reusable, fresh-directory dataset snapshot helper for the walk-forward group and future sweep executor. Bind copied manifest content to the already validated preflight manifest, preserve exact manifest bytes, copy only its declared relative CSV, and validate the copied dataset before training. Reject path escape and manifest/CSV destination collision before creating output. This closes a source-review gap where a coherently replaced original manifest could change the group inputs between preflight and snapshot. Add regression source for mutation, fresh destination ownership, and path rejection. No project commands, imports, tests, builds, services, training or commits will run. File inspection through the code runtime was blocked by automatic approval review; further work uses source already read. All verification and tasks remain open.

## Snapshot source written — 2026-10-16

Added `research/src/portfolio_lab/snapshots.py` and wired the walk-forward group to it. Snapshot creation now compares the source manifest content against the validated preflight manifest before creating its fresh directory, preserves manifest bytes, copies only the declared relative CSV, and delegates copied-data validation to the existing public loader. JSON identity distinguishes booleans from numbers. Path checks also reject drive-qualified/parent paths across host path conventions and reserve the manifest filename. Existing destinations are never replaced; partial new snapshots remain on copy/validation failure for group failure accounting.

Added `research/tests/test_snapshots.py` for byte preservation, nested relative CSVs, omission of unrelated input files, manifest mutation, boolean/number drift, CSV mutation, path/collision rejection, and existing-directory ownership. Its small fake validator isolates copying; real loader and full group integration remain required gates. Verification: source review only; tests, imports, OpenSpec validation, Git checks and commits NOT RUN. No task is marked complete. Runtime-backed file inspection was blocked by automatic approval review; no workaround or retry was used.

## Planned edge-case source review — 2026-10-16

Before editing: reject Windows path normalization/alternate-stream aliases that could collide with the reserved snapshot manifest, and turn oversized numeric model inputs into deliberate ValueError rejection rather than OverflowError from math.isfinite. Add focused regression source without running it. These tighten existing path/finite-input requirements; they do not add an accepted research default or capability-completion claim.

## Edge-case source written — 2026-10-16

Snapshot paths now reject trailing-dot/trailing-space components and alternate-stream separators before creating output, including case/normalization aliases of the manifest filename. Regression parameters were added to `test_snapshots.py`. Walk-forward numeric configuration now rejects oversized integers as ValueError instead of allowing math.isfinite to raise OverflowError; `test_walk_forward_numeric_config.py` covers booleans, strings, nulls, NaN/infinity and oversized integers before any fold access. Verification: all cases UNRUN, source review only. No processes, checks, imports or commits were launched; all required verification remains open.

## Snapshot loader contract reconciliation plan — 2026-10-16

Approved file-only inspection confirms `load_dataset` accepts a CSV filename alongside the manifest; nested relative directories are NOT supported. Earlier helper/stub assumptions and documentation incorrectly described nested-path support. Before editing: align snapshot validation with that established filename-only contract, retain path/Windows alias guards, correct regression source, and add actual public-loader snapshot cases for future execution. Do not broaden the canonical loader or A0 behavior. Lightweight file access is now authorized, but tests/imports/training/builds/services remain stopped, especially while the user's separate GPU model is running.

## Snapshot loader reconciliation source written — 2026-10-16

Aligned `snapshot_csv_path` with the actual public loader: only a CSV filename alongside the manifest is accepted; nested directories and explicit separator prefixes are rejected. Earlier claims of nested-path support came from a stub and did not reflect the loader. Updated the stub cases and added source cases using `synthetic_dataset` and the public loader for exact snapshot round-trip, post-preflight checksum failure and independence from later source changes. These cases are NOT RUN. No change was made to the canonical loader or A0 contract. User-approved lightweight file reading/editing continues; project processes and GPU work remain stopped while the user's independent GPU model runs.

## Planned capability inventory reconciliation — 2026-10-16

Reconcile proposal.md with the existing research-dataset-snapshots delta capability and filename-only loader contract. This records the scoped snapshot helper already written; it does not broaden the loader, authorize execution or complete any task. OpenSpec validation remains unrun.

## Capability inventory reconciled — 2026-10-16

Proposal now declares the already-written research-dataset-snapshots capability and its existing filename-only loader boundary, while retaining portfolio-research modifications. No loader expansion or runtime execution occurred. Validation and every required verification gate remain open.

## Planned finite-evaluation source correction — 2026-10-16

Before implementation: keep ordinary target-turnover/wealth/volatility formulas unchanged while making invalid scalar costs, matrix conversion overflow and nonfinite derived arithmetic fail explicitly as ValueError. Finite input alone does not guarantee finite compounded wealth or volatility. Add focused CPU numerical regression source for future execution; preserve the single-target opt-in and A0 minimum. Also correct the stale design sentence claiming nested CSV support, which file inspection already disproved. No project import, test, training, build, service or GPU work is authorized or run.

## Finite-evaluation source written — 2026-10-16

Updated the shared evaluator to validate real scalar costs without boolean/string/array coercion, convert unrepresentable matrices to ValueError, catch NumPy arithmetic overflow/invalid/divide failures locally, and check returned paths/metrics for nonfinite values. Ordinary formulas, bankruptcy rejection, one-target opt-in and A0 minimum are unchanged by design. Added `test_metrics_numeric_guard.py` for cost types/bounds, hand-calculated initial accounting, wealth/variance/weight/return overflow, conversion overflow, large finite one-target handling and restoration of the caller's NumPy error policy. Corrected the stale nested-CSV design claim to match the inspected loader. Source only: tests/imports/runtime compatibility remain UNRUN, all tasks open; no GPU work or project process started.

## Numerical readback and complex-input follow-up plan — 2026-10-16

Read back the finite-evaluation guard and regression source using file access only. One remaining conversion edge is complex arrays: a float cast can discard imaginary data rather than rejecting an invalid real-return input. Before editing: reject complex allocation/return inputs before conversion and add a warnings-as-errors regression source case. This stays within numeric input validation; no tests or project imports will run.

## Numerical source reconciliation complete — 2026-10-16

Added pre-cast complex-matrix rejection and source cases that treat warnings as errors, preventing silent imaginary-component loss. Proposal/design/spec/task/source documentation now reflects scalar cost, real-matrix and finite-derived-output validation, with the stale nested-directory assumption removed. Numerical source was inspected by file reading; no Python execution, tests, builds, training, services, GPU work or commits ran. Focused numeric cases and complete A0 compatibility remain required, unchecked gates; the implementation is still unverified.

## Planned shared fold preflight correction — 2026-10-16

Source review found that strict integer/finite type checks live only in WalkForwardConfig.for_fold. Direct `run_experiment(..., fold=...)` calls can bypass them: boolean/fractional counts or boolean seeds can pass RunConfig.validate comparisons, and malformed folds are checked only after data loading/device availability. Before editing: share the existing strict fold-setting type checks, call them from both entry points, and reject invalid fold identity/split settings and malformed fold stop budgets before loading data or probing a device. Preserve ordinary A0 validation behavior and valid checkpoint identities. Add source regressions that forbid data/device/training access on invalid input; do not execute them.

## Shared fold preflight source written — 2026-10-16

Added shared `validate_fold_settings` type checks in runner.py and reused them in WalkForwardConfig.for_fold and direct fold execution. Direct calls now reject malformed fold numbering, strict setting types, split mismatches and nonpositive/non-integer fold stop budgets before RunConfig device validation or dataset loading. The no-fold A0 validation path is unchanged. Added unrun source cases forbidding dataset/training/CUDA availability access and preserving existing checkpoint/status bytes on rejection. Source only; no runtime calls, tests, imports, models, GPU work or commits. All fold and A0 compatibility gates remain open.

## Planned owned-child report validation — 2026-10-16

Continuing source review after direct-call and boundary-stop corrections: walk-forward orchestration currently opens a returned child report before proving the directory belongs to that fold, and dictionary equality can accept boolean/numeric aliases in child identity. Before editing: resolve/check returned child ownership before artifact reads, compare typed JSON child provenance, validate report method/conventions/cost type and the existing expected strategy order, and retain relative child references correctly when output_root is relative. Add source cases for foreign/sibling directories, aliased/malformed provenance/report context, missing strategies and relative output roots. No new baseline, external manifest importer or replay claim; no tests or project execution.

## Owned-child validation source written — 2026-10-16

Walk-forward groups now resolve/check fold-root and returned-child containment before opening artifacts, including protection against an owned-root alias escaping the group. Child provenance uses typed JSON comparison, with expected fold/config/dataset/source/runtime/method/conventions. Reports validate method/conventions, numeric cost, dates and the learned/current-baseline order before allocation reads. Child records use resolved group-relative paths, retaining compatibility with relative output roots. Added stub-only artifact guard source and an unrun real-run relative-root regression. No tests, training, project imports, GPU work or commands ran; all task gates remain open.

## Planned strict local JSON reader — 2026-10-16

Artifact/CLI inspection found inconsistent parsing: sweep input rejects duplicate/nonstandard constants, but new fold-group artifact readers and the walk-forward CLI use permissive json.loads. Before implementation: extract a lightweight stdlib-only shared JSON reader, reject duplicate fields/nonfinite constants/float exponent overflow, and use it for new walk-forward configuration/owned artifact and snapshot reads. Keep the legacy A0 dataset/config loader and the already-strict service request loader unchanged. Add source-only malformed-document/no-aggregation cases. This is local control/artifact validation, not an external replay importer; no tests or project code will execute.

## Shared JSON reader source written — 2026-10-16

Added stdlib-only json_io parsing for duplicate keys, nonfinite constants, finite float exponents, UTF-8 and object expectations. New walk-forward CLI, snapshot-manifest and owned child readers use it. Fold manifest/report hashes now cover the exact bytes parsed, matching the sweep inventory's existing captured-byte policy. Legacy A0 configuration/dataset parsing and the service request loader are unchanged. Source only; parser/consumer regression source is next and no imports, tests, model/GPU or command execution occurred.

## Strict JSON regression source written — 2026-10-16

Added unrun json_io cases for UTF-8, integer/boolean type preservation, duplicate/escaped/nested fields, nonfinite constants, exponent overflow, top-level object requirements and input byte preservation. Added walk CLI no-dispatch, duplicate snapshot-manifest and duplicate fold-artifact source cases. Foreign-content guards now cover both text and byte reads after the reader refactor. No tests or project imports ran; the legacy A0/service loader boundaries remain unchanged. Actual parser/consumer/A0 compatibility remains an unchecked gate.

## Planned objective/cost audit metadata — 2026-10-16

Source inspection confirms the existing negative_sharpe objective uses gross portfolio returns and variance stabilization 1e-8; cost_bps is used only during evaluation. Before editing: name the existing unchanged epsilon and declare objective metadata (training minibatches, validation selection window, stabilization and evaluation-only costs), retain it in local run/fold/group artifacts/identity, and validate it when composing owned folds. Add source cases for objective arithmetic/metadata and malformed child declarations. This records existing behavior, not a new numerical default or cost-aware training method. No model/test/GPU execution will occur.

## Objective metadata source written — 2026-10-16

Named the existing unchanged variance epsilon and added OBJECTIVE_CONVENTIONS describing stabilized gross-return loss, chronological minibatch training, full-validation selection and evaluation-only costs. Run and walk-group identities/reports now retain that declaration; fold composition validates child manifest/report declarations. Existing optimizer, loss arithmetic, seed policy and evaluation accounting are unchanged by design. No imports, model execution, tests, GPU work, build or commands ran; source regression/compatibility verification remains open.

## Objective audit regression source written — 2026-10-16

Added a hand-calculated gross-loss/stabilization case and objective declaration assertions to existing run/resume/group regressions, without adding extra model runs to those cases. Manifests explicitly disclose evaluation-only costs. All cases remain unrun. Source review also found stale canonical SPEC wording saying no Java/HTTP/durable consumer exists despite recorded service/browser evidence; next document-only correction will reflect the bounded implemented consumer and retain unverified storage/Compose boundaries. Numeric preset acceptance is not inferred or changed.

## Planned current-source A0 repeat compatibility — 2026-10-16

Dependency review found repeat.py's identity field list omits newly declared objective input, so fresh current-source A0 runs would fail their identity preflight. Before editing: share the A0 identity field registry, include objective/report declarations, use strict JSON for repeat metadata, and compare immutable inputs with JSON type distinctions. Reject missing legacy objective metadata explicitly without guessing migration/training; validate actual method/conventions/objective/report metadata before a repeat. Keep output numeric tolerance at 1e-7 while comparing objective/convention/cost metadata exactly. Add source regressions for fresh matches, missing/tampered metadata, tiny metadata changes and typed input aliases; no tests or model/process execution.

## Repeat reference type preflight follow-up — 2026-10-16

Before completing the repeat correction, reuse the existing strict integer/finite/device-type preflight for saved reference settings as well. Expose a generic helper name while keeping the fold helper alias, so no-fold execution defaults remain unchanged but a malformed saved reference cannot reach training/device access. This also avoids an oversized integer escaping as OverflowError before a comparison report can be retained. A combined record/code patch was rejected for duplicate target operations and applied no edits; the corrected patches are split. No runtime checks will be executed.

## Current-source repeat compatibility source written — 2026-10-16

Runner and repeat now share RUN_IDENTITY_FIELDS including objective metadata. Repeat metadata uses the shared strict JSON policy, validates explicit reference setting types and current method/conventions/objective/report consistency before training, and rejects missing prior objective declarations without guessing migration. Immutable inputs compare with JSON type distinctions; report objective/convention/cost metadata and manifest conventions use zero tolerance while ordinary numerical outputs retain 1e-7. Direct comparison rejects unsupported local schema versions/protocols. Added a generic name for the existing type validator while preserving its fold alias and the no-fold execution path. Source only; all repeat/model compatibility checks remain unrun, and no project/GPU/command execution occurred.

## Repeat metadata regression source written — 2026-10-16

Extended the existing repeat suite with identity reconstruction including objective, missing prior/current report declarations, duplicate reference JSON, malformed setting types/huge numeric inputs, tampered objective/conventions/method, exact report metadata and typed input aliases. Objective tampering is checked even after the self-declared identity hash is recomputed. Numeric comparison entries now record their applied absolute bound (zero for metadata/integral values; existing 1e-7 for ordinary float outputs). No additional reference fixture fit was introduced; all tests, imports, models and GPU work remain unrun. Fresh current-source repeat compatibility must still be executed, not assumed from source inspection.

## Planned finite repeat diagnostics — 2026-10-16

Numerical read-through found that compare._compare sends arbitrary integer counts through math.isfinite and can put infinity into absolute_difference when finite floats have an unrepresentable difference. Before editing: handle integer/type comparisons without unsafe conversion, flag nonrepresentable differences as mismatches, and use null for an unrepresentable maximum rather than serializing infinity or implying zero. Check reference observation count/type against dates before training. Add unrun retained-comparison/large-count/overflow cases, preserving finite-output tolerance and the distinction between a local output comparison and authenticated replay.

## Finite repeat diagnostic source written — 2026-10-17

Readback confirms the prior diagnostic patch landed: repeat preflight rejects non-integer/date-mismatched observation counts before training; comparison handles integral/type checks without unsafe float conversion and flags unrepresentable differences with a null maximum instead of infinity. Added unrun source cases for float/bool/huge/mismatched counts, extreme finite float subtraction, huge exact integer differences and JSON serialization. Direct comparison remains diagnostic rather than authenticity validation. No project imports, tests, models, commands or GPU operations ran. Every task remains unchecked pending execution authorization.
## Planned fold baseline omission follow-through — 2026-10-17

The sweep contract review exposed a related fold gap: strategy names are already checked against dataset roles, but the first baseline_omissions value is accepted without validation. Before editing: require the matching current omission declaration before reading allocations, retaining failed-group evidence. Add unrun malformed/wrong omission cases to the existing guard suite; no new baseline estimator or acceptance claim.
## Fold omission source written — 2026-10-17

Walk-fold aggregation now requires the omission declaration derived from its already-validated dataset baseline set, including in the first fold and before allocation reads. Added malformed/missing/wrong omission cases to the existing forbidden-aggregation guard suite. All regression source is unrun. No project/process/GPU execution occurred, and no task is marked complete.
## Planned aggregation memory reduction — 2026-10-17

Read-through found each accepted fold calls make_fold_samples again just to select samples.y[test], reconstructing full input windows and fitting an unused scaler. Before editing: recover only planned evaluation returns from adjacent owned price rows, retaining the same float64 price arithmetic and float32 target conversion used by make_samples. Keep training/sample construction untouched. Add source equality/no-feature-construction cases for single and multiple targets and assert group gross paths agree with concatenated child gross paths. This is a source-level allocation reduction, not a measured memory claim; no execution is authorized.
## Aggregation memory source written — 2026-10-17

Walk aggregation now reads only planned adjacent-price returns through _evaluation_returns and keeps the existing float32 target conversion; it no longer calls make_fold_samples or constructs another training tensor/scaler after a child completes. Training/sample construction is unchanged. Added unrun exact target-equality cases with feature construction forbidden for single/multiple targets, plus concatenated child/group gross-path equality in the existing multi-fold integration case. Source readback is not numerical or measured-memory verification. No project imports, tests, training, commands or GPU operations ran.
## Planned owned fold accounting reconciliation — 2026-10-17

Source review found fold composition checks provenance/strategy names but can reference malformed or inconsistent nested child accounting while still recomputing a valid aggregate from allocations. Before editing: use the new target-only return path to recompute each fold's local-entry evaluator result and require the complete typed JSON report result to match before accepting the fold. Do not concatenate local wealth or reset group costs. Add model-free producer fixtures for valid reports and altered metrics/paths/shape/types; preserve explicit source-only status and no external/model replay claim. The same current evaluator/float32 targets/round-tripped allocation values should reproduce exact local output; actual-run compatibility remains an unrun gate.
## Owned fold accounting source written — 2026-10-17

Each accepted fold now has its complete local-entry evaluator result recomputed from serialized allocations and target-only owned returns. Typed JSON result mismatch rejects the fold before it enters completed-fold inventory or aggregate output. Group accounting still carries targets continuously across boundaries. Added model-free producer source cases for valid completion and changed metric/gross/net/cost/turnover/wealth paths, missing/extra result shape, numeric count types and invented null explanation. Fake model bytes are hash-only fixture evidence, never loaded. All tests and real-producer compatibility remain unrun; no project/model/GPU/process execution occurred.
## Planned recorded resume identity follow-through — 2026-10-17

CLI/identity read-through found local resume checks only manifest.identity_sha256 against freshly computed inputs. If actual saved identity fields are edited but the old digest remains, direct resume can retain inconsistent metadata while training with current inputs. Before editing: compare actual typed recorded identity plus schema/protocol presence/method/conventions before _train, use strict manifest/status JSON, reject unsupported states and preserve existing evidence. Add stale-digest/typed/schema/protocol/duplicate-control regression source around a single shared paused CPU fixture. Do not load/authenticate external checkpoints or claim durable service recovery. All execution remains prohibited.
## Recorded resume identity source written — 2026-10-17

Local fixed-holdout/direct-fold resume now parses manifest/status with strict JSON and compares actual typed recorded identity, schema, protocol presence and method/conventions against freshly requested inputs before _train. An unchanged self-declared hash cannot mask edited identity fields; unsupported status rejects too. Added one shared future paused CPU fixture with stale-digest, typed alias, schema/protocol, duplicate-control and unknown-state rejection cases preserving file bytes, plus unchanged/changed-request dispatch guards. No checkpoint authentication or service resume was added. Every test/model/import/process/GPU check remains unrun.
## Resume guard source read-through — 2026-10-17

Removed a brittle positional-argument assertion from the new unchanged-resume dispatch guard during source review; it indexed stop_after_epochs rather than the resuming flag. The case now checks the intended boundary: unchanged metadata reaches the stub exactly once, while incompatible cases cannot reach it and preserve evidence. Added guide text for current owned accounting/target-only aggregation/resume guards. No assertion or project code was executed; runtime outcomes remain unknown.
## Planned finite objective-moment follow-through — 2026-10-17

The isolated net-loss review exposed the same issue in current gross loss: finite float32 portfolio returns can overflow variance and yield a finite zero loss through division by infinity. Before editing: share the unchanged stabilized formula in model.py with explicit mean/variance/final-loss finite guards; route gross and isolated net primitives through it. Add unrun finite-overflow and ordinary exact value/gradient regression source. No runner method, epsilon, optimizer, cost policy or numeric preset is changed; invalid objective intermediates now fail explicitly. No execution is authorized.
## Shared finite objective source written — 2026-10-17

Gross and isolated net objectives now share stabilized_negative_sharpe with explicit finite mean/variance/final-loss checks. The ordinary formula/epsilon is unchanged by design; overflowing variance no longer yields a finite zero objective. Added unrun hand-derived two-return loss/gradient and zero-series gradient cases, finite float32 variance/final-loss overflow and nonfinite-moment rejection. Current model/training/repeat compatibility remains open. No tensor, autograd, test, import, model, device/GPU or project process execution ran.
