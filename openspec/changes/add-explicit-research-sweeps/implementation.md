# Implementation record

## Pure sweep source — 2026-10-15

Written explicit immutable candidate settings/planning and complete terminal coverage checks. Added context-bound, null-aware descriptive summaries and tested-adjacent-cost sign comparisons, retaining failed/invalid cells and avoiding interpolation/selection. No default seed/cost list, experiment execution, CLI or external artifact verifier is added. Source only: no import, test, process, validation or commit has run. Regression source and sequential execution remain pending; no task is complete.

## Planned code-only continuation — 2026-10-15, before edits

Create this scoped change manually through file edits because the user prohibits starting processes, including OpenSpec CLI. Scope follows approved A1 task3.8. Initial work is pure explicit grid/summary source, with all seeds/costs/budgets supplied by the caller; no proposed defaults are accepted. No experiment, dependency, CLI, shell, test, build, Git, app or service process is started. Artifacts and code remain unvalidated until execution is authorized. Actual sequential execution/integration and historical evidence remain separate unfinished tasks.
## Source review continuation (2026-10-15)

Documentation reconciliation: added `specs/research-sweep-reporting/spec.md` for the offline entry point, strict input, complete terminal grid, comparable context, honest null/failed statistics, adjacent cost intervals, and exclusive output creation. Added an unchecked verification task for that contract. This delta is source documentation only; OpenSpec validation is unrun. No archive or completion claim is made.

Offline entry point source written: `research/src/portfolio_lab/sweep_cli.py` accepts a strict version 1 JSON document and produces a descriptive summary without training. Duplicate fields, nonstandard nonfinite constants, unknown settings, nonterminal records, and incomplete grids are rejected before output creation. Exclusive file creation protects existing evidence and the input file. `research/tests/test_sweep_cli.py` adds malformed-input, no-output-on-validation-failure, existing-output protection, and CLI dispatch cases. Verification: NOT RUN; no processes started. Interrupted or failed writes can leave a partial newly created output; consumers must parse and validate outputs. This does not implement training orchestration or authenticate artifacts, and tasks remain unchecked.

Next scoped source step: add a standalone offline JSON summary entry point with an explicit versioned input contract, duplicate-key/nonfinite-JSON rejection, strict setting fields, and exclusive output creation. It will summarize supplied terminal records only, without training, spawning children, or claiming artifact authentication. Add source cases for malformed input and preservation of existing output; do not execute them under the current user restriction.

Source written: `research/src/portfolio_lab/sweep.py` now has a defined candidate/result schema, exact terminal coverage, context comparability, null-aware descriptive statistics, and adjacent tested cost comparisons. The planner copies caller collections and enforces the explicit candidate budget. Finite checks cover oversized integers and derived return differences; mean calculation avoids overflowing a finite intermediate sum. `research/tests/test_sweep.py` contains fixed-answer and rejection cases, including failed middle costs and all-failed grids. These checks have NOT been executed. No task is marked complete; executor, CLI, artifact authentication, validation, and archive remain outstanding.

Scope before editing: make the pure sweep planner and summary contract explicit, retain every requested candidate and terminal failure, and add fixed-answer regression source for coverage, comparable contexts, null Sharpe values, and tested cost intervals. Guard derived statistics against overflow as well as nonfinite input. No execution, CLI integration, process launch, or new research default is authorized by this source-only step. Verification remains unrun; all tasks stay open.

## Planned sequential executor source — 2026-10-16

Before implementation: add `sweep_runner.py` using the shared fresh-directory snapshot helper and existing `run_walk_forward` interface. Require complete common model/protocol settings separately from explicit seed/cost settings. Validate the entire candidate/fold plan before creating the group; record candidate and fold budgets. Run candidates sequentially against the owned snapshot, check returned group status/config/dataset/source/runtime/protocol/date identity, and retain manifest/report hashes. Preserve every terminal failure/invalid record, persist progress after each candidate, and distinguish complete coverage with failures from all-successful completion. Interruptions retain pending inventory and do not produce a complete summary. No group resume, service routing, historical claim, or default grid is included.

Known limitation before editing: further source inspection was blocked by automatic approval review. The adapter will require the report contract already used by the fold/group source (per-strategy evaluator metrics and test_dates); compatibility with the actual final walk-forward report must be verified after process/file-inspection authorization. New unit source will isolate orchestration with a stub; those cases cannot substitute for actual training integration. No process or import will be launched while writing this code.

## Sequential executor source written — 2026-10-16

Added `research/src/portfolio_lab/sweep_runner.py` with explicit common model settings, whole-grid/fold preflight, one owned validated dataset snapshot, sequential candidate execution, persisted pending/running/terminal inventory, child identity checks, manifest/report hashes, and final summary composition. Ordinary execution errors remain failed records; returned artifact/schema/context errors become invalid records. Interrupted runs retain pending progress and do not produce a complete summary. Completion with failures is explicitly distinct from all-successful completion. Source only: no imports, tests, training, commands, commits or validation ran. The real final walk-forward report adapter remains an unverified integration assumption pending inspection and runtime checks. Stub-based orchestration regression source is the next step; no task is complete.

## Executor regression source — 2026-10-16

Added `research/tests/test_sweep_runner.py` with stub-based cases for caller order and a common snapshot, retained artifact hashes, whole-grid/common-setting preflight, original-input mutation, failed training with later candidates continuing, invalid returned identities/dates/status, baseline-omission drift, foreign returned directories, and partial interruption without a complete report. Artifact hashes now cover the exact bytes parsed for validation, avoiding a separate read/hash race. Error messages from training are not copied into retained failure records; exception class and a generic reason are retained. The stub does not establish real model training, dataset-loader validation, final group report compatibility, or crash durability. All tests and imports remain NOT RUN; tasks remain unchecked.

## Planned training entry point source — 2026-10-16

Before implementation: add a standalone training CLI requiring explicit dataset, config file, and output root. The versioned config must contain exactly complete common model settings and explicit sweep settings; no seed/cost/output defaults. Reuse strict duplicate/nonfinite JSON loading from the offline summary entry point through a public loader. Dispatch to the sequential executor and distinguish all-successful exit 0 from complete coverage with failures exit 1 and invalid CLI/input exit 2. Add dispatch/schema/exit regression source without executing it. This is source integration only; actual runner report compatibility is still unverified and the no-process constraint remains in force.

## Training entry point source written — 2026-10-16

Added `research/src/portfolio_lab/sweep_train_cli.py`, requiring explicit dataset/config/output arguments and a complete version 1 model/sweep document. It rejects missing/extra fields and invalid grids, reuses the strict JSON loader exposed by `sweep_cli.load_document`, dispatches to the new executor, and distinguishes all-successful exit 0, completed-with-failures exit 1, and invalid/inconsistent input/output exit 2. Added stub-only dispatch/schema/status regression source in `research/tests/test_sweep_train_cli.py`. No CLI, training, import, test, build, Git operation or validation was executed. Tasks remain unchecked; actual final walk-forward report compatibility and real-loader integration remain mandatory gates. These modules are standalone entry points; the existing general CLI and service routes are unchanged.

## Planned source reconciliation — 2026-10-16

Before edits: extend executor regression source for changed strategy/metric shape, a changed owned snapshot stopping later training calls, and an entirely failed grid. Reconcile task organization, top-level source documentation and stale handoff wording with the unverified draft. Preserve implementation history and all unchecked verification gates; do not imply code execution or current Git inspection.

## Source reconciliation written — 2026-10-16

Extended stub executor cases for strategy-set drift, nonfinite metrics despite completed child status, changed sweep snapshot identity preventing later training calls, and an entirely failed grid with no invented metrics. Reorganized the task file while retaining all unchecked scope and gates, added the top-level README link, and corrected stale handoff statements about training CLI source and the previously committed container work. No runtime verification, Git status inspection, link/OpenSpec validation or commit occurred. Current limitations remain: adapter compatibility not inspected, real loader/training unverified, no historical evidence, no sweep resume or external replay verifier. Further runtime-backed inspection remains blocked by auto-review under the user's no-process instruction.

## Approved file inspection and adapter correction plan — 2026-10-16

User explicitly authorized the file-reading helper, then requested minimal processes because a separate GPU model is running. Only lightweight file inspection/editing is authorized here; no project imports, tests, training, builds, services or GPU work. The actual `walk_forward.py` and evaluator confirm a source defect: report strategy entries contain `metrics` plus return/wealth paths, whereas the sweep adapter assumed flat metrics. The stub repeated that incorrect assumption. Before editing: extract the actual nested metrics contract, reject malformed/flat entries, and update stub/contract cases to reflect the producer. Tighten status fold counts, report method/conventions/cost type, and JSON-typed identity comparisons so boolean/numeric aliases cannot bypass matching. Runtime integration remains unverified; tasks stay open.

## Adapter correction source written — 2026-10-16

Approved file-only inspection confirmed the nested report mismatch. The sweep adapter now extracts each strategy's `metrics` from the actual evaluator result object, retains child report hashes/paths, and rejects malformed or flat entries. It also checks completed-fold/budget counts, report method/conventions and numeric cost type, and compares JSON identities with type-preserving digests. Stubs now use the real evaluator's result shape; source cases cover nested extraction, flat/malformed results and boolean/numeric identity aliases. Tests remain UNRUN, including the revised stub suite and actual training integration. No model, GPU, test, build, service, shell or Git process was started. The file-reading helper is explicitly authorized; the earlier inspection block is resolved for this limited use only.

## Planned real-producer regression source — 2026-10-16

Before editing: add a small synthetic CPU-only integration regression using the actual dataset loader, sweep executor, walk-forward producer and evaluator schema. It will require two explicitly declared candidate costs and one short evaluation window, retain nested child report evidence, and check extracted summary metrics and hashes. This is a future execution gate, not permission to train now; the test file will only be written/read. Reconcile user-facing source docs to distinguish completed source inspection from still-unrun runtime compatibility.

## Actual-producer integration regression source written — 2026-10-16

Added `research/tests/test_sweep_integration.py`: future CPU-only execution with the public synthetic loader, two explicit costs, a five-target window and actual sweep/walk-forward/evaluator producer. It checks complete/all-successful status, child nested metrics versus flat inventory summaries, fixed-date coverage, child hashes and one-value descriptive counts/spread. File-only readback of the adapter and new cases is complete. No Python/project import, fitting, test or GPU execution occurred. This is an unrun acceptance gate, not passing evidence. Updated `docs/RESEARCH-SWEEPS.md` to distinguish the now-inspected producer schema from remaining runtime integration verification.

## Planned current-state handoff reconciliation — 2026-10-16

Before editing: replace the accumulated handoff's superseded continuation notes with a concise current-state record, preserving confirmed decisions, prior verification evidence/commit references, active changes, new source corrections and remaining gates through links to detailed implementation history. Explicitly record that the user resolved the file-helper inspection block, requested minimal processes, and is running an independent GPU model. No new execution authority or verification claim is inferred. The first combined documentation patch was rejected because it targeted this record twice; no edit from that patch was applied. This corrected edit separates planning, handoff replacement and final recording.

## Current-state handoff reconciled — 2026-10-16

Condensed `openspec/HANDOFF.md` into current authorization, confirmed direction, linked prior evidence, current unverified research source, remaining gates and next steps. Removed superseded blocking/CLI-source statements while retaining their chronology in this implementation history. Recorded the GPU workload constraint and limited file-helper authorization. No tests, training, builds, GPU work, shell/Git commands or OpenSpec validation ran; all task checkboxes remain open.

## Planned capability inventory reconciliation — 2026-10-16

File review found that proposal.md declared only modified portfolio-research behavior while the existing delta folders also document reporting, execution and CLI capabilities. Reconcile those declarations with the already-written scoped deltas; this adds no execution or new product scope. Strict OpenSpec validation remains unrun.

## Capability inventory reconciled — 2026-10-16

Proposal declarations now match the existing research-sweep-reporting, research-sweep-execution and research-sweep-cli delta folders and retain portfolio-research as modified. Source/runtime acceptance remains unfinished; no validation or task completion is claimed. Only file reading/editing occurred.

## Planned metric-domain validation source — 2026-10-16

Before implementation: align completed-record validation with the existing evaluator's domains: cumulative return at least -1, nonnegative volatility/turnover/cost and maximum drawdown between 0 and 1. Sharpe may retain either finite sign or its explicit null explanation. Current flat fixtures incorrectly use negative drawdown; correct them. Replace the deliberately impossible below-total-loss comparison fixture with a rejection case. Add boundary and invalid-domain source cases; do not execute them or alter descriptive aggregation formulas. No new numeric default or historical claim is introduced.

## Metric-domain source written — 2026-10-16

Completed-record validation now rejects return below -1, negative volatility/turnover/cost, and drawdown outside [0,1], matching the inspected evaluator's conventions. Corrected the flat fixture's negative drawdown and replaced its impossible below-total-loss overflow setup with explicit domain rejection. Added invalid-domain/boundary source cases while preserving negative finite Sharpe and explicit null explanations. No tests or project imports ran; aggregation formulas, source authentication limitations and unchecked tasks remain unchanged.

## Metric-domain documentation reconciled — 2026-10-16

Updated tasks and research source guide with the newly written metric range guards and their unrun boundary cases. Negative Sharpe is preserved separately from zero-volatility/null-Sharpe source cases. Handoff records the numerical continuation and prior-source evidence boundary. Range validation is not authentication or full algebraic consistency verification. No runtime checks, imports, models, GPU operations or commits occurred; all task checkboxes stay open.

## Planned shared strict JSON integration — 2026-10-16

Move the existing strict sweep-input policy to a stdlib-only json_io module shared with new fold consumers, retain the public sweep load_document wrapper, and apply strict parsing to owned candidate artifacts and returned training status. Add finite float-exponent rejection rather than allowing JSON numbers to become infinity. Preserve captured-byte hashes and field/schema validation; no caller defaults, model execution, dependency additions or replay-authentication claim. Add focused parser/adapter source cases; execution remains prohibited.

## Shared strict JSON source written — 2026-10-16

The sweep public load_document wrapper now delegates to json_io; candidate artifacts and training completion status use the same duplicate/nonfinite/float-overflow policy. Artifact digests remain hashes of captured raw bytes. No schema/default, training or replay-authentication behavior was added. No runtime checks, imports, tests, commands or GPU work ran; all verification remains open.

## Strict JSON consumer regression source written — 2026-10-16

Added duplicate candidate status/manifest/report cases, rejection of unused nonfinite/exponent-overflow artifact fields, and duplicate training-completion status rejection. These complement the shared parser and preserve full invalid-candidate accounting rather than accepting ambiguous content. All cases are source only and unrun. No process, GPU, model, test, project import or commit was started.

## Planned cost-sweep objective disclosure — 2026-10-16

Record the existing gross-return stabilized objective and evaluation-only transaction costs in sweep common identity/manifest/report and verify the same declaration in returned candidates. Document that a cost grid does not add a cost penalty to training/validation; candidates are currently executed independently, with no reuse/cache or new seed policy. Update stubs and metadata regression source without executing it. No algorithm, estimator, numeric default or historical claim changes.

## Cost objective disclosure source written — 2026-10-16

Sweep common identity, manifest/report and candidate validation now retain/check the actual gross-return objective declaration and evaluation-only cost treatment. Updated child stubs and mismatch cases, and removed a stale pure-summary limitation implying no executor exists. Each requested candidate still runs independently; no training reuse/cache, new grid or cost penalty was added. All source is unrun and no project/GPU/process execution occurred; exact numerical behavior and artifact compatibility remain required gates.

## Cost-scope regression source written — 2026-10-16

Extended the already-written two-cost CPU integration case to inspect objective metadata, same-seed fitted model/scaler tensors and validation history across cost-only changes. This adds artifact comparisons, not additional fits beyond that existing test's two candidates. Costs continue to affect accounting only. All cases are unrun; no torch/model/project import, GPU call, training, build or test execution occurred. Numeric preset wording in SPEC remains planning text and is not injected into explicit caller configurations; its acceptance status remains unresolved in handoff.

## Planned baseline scope and owned-root follow-through — 2026-10-17

Source inspection found the sweep accepts the first candidate's strategy set as common context, allowing every candidate to omit an expected baseline consistently. Before editing: derive the expected learned/baseline set and omission declaration from the owned dataset asset roles and validate every candidate, keeping offline caller summaries separate. Also require the resolved candidate root to remain within its sweep before any returned artifact read, matching the existing walk-fold ownership guard. Add unrun fixture cases for missing/extra baselines, malformed/incorrect omissions and root escape. No runtime work is authorized.
## Baseline scope and ownership source written — 2026-10-17

Sweep candidate acceptance now checks the exact learned/dataset-role baseline set and corresponding omission declaration, including the first candidate. Candidate roots must resolve within the sweep before child artifact reads. Updated the stub dataset to declare actual asset roles and added unrun first-candidate missing/extra baseline, malformed/wrong omission, available 60/40 and escaped-root cases. The offline summary contract is unchanged. No tests, project imports, models, shell commands or GPU operations ran; actual producer compatibility and OpenSpec validation remain open.
## Planned bounded ordered input capture — 2026-10-17

Direct SweepSettings currently calls tuple() on arbitrary iterable axes before checking max_runs, so a set loses caller order and a lazy/unbounded iterable can be consumed before the budget gate. Before editing: accept explicit ordered list/tuple axes only, validate the candidate budget/count before copying, preserve existing mutable-list isolation, and add source cases that forbid iteration during unsupported/over-budget input rejection. JSON CLIs already require arrays. Do not imply this candidate-count cap bounds fold time or training memory. No runtime checks will run.
## Ordered input capture source written — 2026-10-17

SweepSettings now accepts ordered lists/tuples only and checks positive integer max_runs plus Cartesian count before freezing axis copies. Existing caller order/list-mutation isolation is preserved by design. Added unrun rejection cases for sets, mappings, lazy generators, ranges, text/None and forbidden iteration on invalid/excess budgets. No generator/test/model/project code was executed while writing this source. Runtime verification and full CLI compatibility remain open; this is not a fold-time or model-memory cap.
