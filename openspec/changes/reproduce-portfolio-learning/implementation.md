# Planning and implementation record

## Final continuation checks — 2026-10-09
- Strict OpenSpec validation passed 5/5; all 49 Markdown documents passed local file/heading/duplicate-requirement checks. Git diff --check passed. Retained reference artifact hashes and numerical source fingerprint still match the measured smoke evidence.
- A0 checklist is 17/18 complete. Historical seed/cost task 4.2 remains open, so the change is not archived and no historical reproduction is claimed. UI/API/Compose/device checks remain unrun because those implementations do not exist.
- Planning and current research verification are complete for the user's requested model continuation. All changes remain uncommitted; no project commit, remote publication, dependency upgrade or Tailscale reconnection occurred.

## Evidence and task reconciliation — 2026-10-09
- Recorded environment/resource evidence and completed tasks 1.2/3.3; task 4.1 follows its documented synthetic-only/data-limitation branch. README commands, retained artifact links and current handoff support task 4.3. No historical study is marked complete; task 4.2 stays open and the change is not archived.
- Current README/DESIGN/READINESS/config distinguish the tested runner from unbuilt service/client work. Shared schema/locked environment for a synthetic service slice can proceed without closing the historical study. Final documentation validation follows these status edits; no numerical source changes after retained smoke generation.

## Retained CPU evidence — 2026-10-09
- Retained the fixed 420-observation, 64-unit/50-lookback, three-epoch CPU reference and separate-process CLI repeat under runs/cpu-evidence-2026-10-09-a3ea8ef5. Repeated outputs matched with zero maximum absolute difference; reference artifact hashes were unchanged.
- Paused an equivalent run after epoch 1, resumed to epoch 3 and compared against the uninterrupted reference: zero maximum absolute difference and unchanged resume manifest. The evidence JSON contains paths, settings, hashes, environment, source dirty metadata, sampled RSS and all strategy metrics.
- Reference call took 5.899s, with 0.421s on the narrower training/evaluation timer and 284.81 MiB maximum sampled RSS. These are single synthetic observations, not a performance benchmark or continuous peak. GPU untested. docs/A0-EVIDENCE.md records evidence and limitations.
- No provenance-validated historical snapshot was located; no market data was fetched/evaluated. This satisfies task 4.1's explicit data-limitation/synthetic-only branch; historical seed/cost task 4.2 remains open. Final documentation reconciliation and structural validation follow.

## Integrated test result — 2026-10-09
- Combined current research suite passed all 59 tests in 54.22 seconds with a new workspace-local temporary directory and pytest cache disabled. This includes 17 original numerical/recovery cases, 10 provenance cases and 32 repeat cases. Independent read-only code review found no material correctness blockers.
- Tasks 1.1/1.3, 2.1–2.4, 3.1–3.2 and 3.4–3.5 are now reconciled with their source/test evidence. This does not satisfy retained resource measurement or historical experiment tasks. CPU smoke evidence is the next step; source is settled before generating reference runs.

## Integrated verification resumed — 2026-10-09
- Re-inspected the saved working tree before resuming the pending checks. Source-provenance's ignored-bytecode fix and workspace-local Git-discovery test are present; targeted provenance evidence is 10 passing tests. Repeat's earlier 32 focused cases passed. No new numerical behavior is introduced in this verification step.
- Running the combined suite, then a retained synthetic smoke with 420 observations, lookback 50, hidden size 64, batch 64, three epochs, seed 7 and 1 bps cost; these values are fixed before inspecting results. Save fresh repeat and one-epoch interruption/resume comparisons plus resource observations. GPU and historical comparisons remain outside this synthetic evidence.
- Removed an accidental duplicate empty README heading. Final checklist, measured outputs and handoff reconciliation follow the checks.

## Repeat verification and execution guidance — 2026-09-23
- Independent test implementation added 32 focused repeat cases; all passed in 10.98 seconds with a fresh workspace-local temporary directory. Cases exercise real fresh training, copied data/config, reference immutability, unsupported/incomplete/tampered inputs, nonfinite results, numeric/structural differences, failed-run retention and CLI exit outcomes.
- Added PowerShell quickstart and completed-epoch recovery commands to README; documented local A0 comparison limits in REPRODUCTION. Source-revision work has targeted evidence in initialize-version-control. Full integrated suite and retained CPU/resume/repeat run are next; no historical-data result has been produced.

## Local repeat implementation — 2026-09-23
- Preflight also requires every saved configuration field and completed-run artifacts (including model/checkpoint presence), rejects nonfinite JSON values including numeric overflow, and checks metric/series completeness. Model/checkpoint binaries are checked for presence only, never deserialized; artifact authenticity is not certified.
- Added repeat.py and the CLI repeat command. A completed A0 run supplies its copied dataset and saved configuration; source/runtime/data/identity checks precede fresh training. Separate comparison directories preserve reference files and retain unavailable/incompatible/failed/different outcomes.
- Comparison covers report metrics/history/dated series, preprocessing/split metadata and allocation rows, with absolute 1e-7 tolerance and exact structural/count/date/null comparisons. Timing, memory, run IDs and descriptive Git metadata are excluded. No reference model/checkpoint is deserialized.
- This is a local A0 comparison, not the v2 verifier or a proof of artifact authenticity/source retrieval. Focused tests and independent code review are next; tasks 3.4/3.5 are not yet checked.

## Continuation scope — 2026-09-23
- User requested continuing Claude's work. Inspected Git history, current source, existing specs/tasks and the stale handoff. Version control exists; numerical runner remains the A0 fixed-holdout prototype.
- Scoped local saved-run repeat and negative-path tests before implementation, plus retained CPU/recovery evidence and checklist reconciliation. Parallel source-revision work belongs to initialize-version-control. Reference outputs remain immutable and this does not claim v2 verification.
- Existing 17-test evidence is historical until current changes are verified. No historical dataset is currently approved/retained for this session; inspect local availability and record limits before claiming historical work.

## Final readiness verification — 2026-09-21
- Fresh existing research suite passed: 17 tests in 9.65 seconds, using a unique workspace-local temporary directory. This verifies the current prototype after packaging/comment cleanup; it is not a historical benchmark or full-service test.
- Strict OpenSpec validation passed 4/4; 41 Markdown documents had zero unresolved file/heading links or duplicate requirement titles. Section 5 is complete. Final task reconciliation restored the 5.1 checkbox after concurrent documentation edits; the implementation and dependency evidence were retained.
- Original A0 tasks remain open pending task-level artifact/evidence reconciliation, including the newly explicit saved-run comparison. No dependency upgrade, full lock/clean install, historical research, GPU or service deployment was performed. Do not archive this change as completed.

## A0 contract clarification — 2026-09-21
- Corrected proposal/design to identify Python/PyTorch as approved. Reconciled REPRODUCTION and design with the existing CLI raw-row split; no numerical behavior changed. At 420 rows/lookback 50, its 30 validation targets are about 12.3% of 244 usable pre-test targets, not 10%.
- Added task 3.4 for the already specified saved-experiment comparison. Resume tests alone do not satisfy that scenario; the broader v2 replay contract remains A1. Task 5.2 is complete; existing evidence/implementation tasks stay open for task-level reconciliation.
- Verification: inspected cli.py boundary arithmetic and the existing A0 repeat-run spec against descriptions. No training or historical measurement performed. Final OpenSpec/link checks are owned by define-product-and-stack section 9.

## Dependency declaration and CLI description — 2026-09-21
- Task 5.1: declared the directly imported filelock==3.32.6 in pyproject.toml and requirements-cpu.txt, matching the existing environment; corrected the CLI docstring to describe reuse by the planned Python job worker.
- Verification passed: parsed TOML/CPU requirements with Python and checked every direct dependency against installed metadata (NumPy 2.2.6, PyTorch 2.8.0+cpu, psutil 7.0.0, filelock 3.32.6). The CPU PyTorch build satisfies the project's 2.8.0 requirement. The isolated environment's `python -m pip check` reported no broken requirements, and `python -m portfolio_lab.cli --help` exited successfully with synthetic/run commands.
- Task 5.1 is complete. No packages were installed or upgraded, and no numerical logic changed. The editable package metadata was not regenerated, and a clean-environment install/full dependency lock remains unverified. Numerical tests were not rerun for this declaration/docstring-only cleanup; the earlier 17-test evidence is unchanged. The source fingerprint includes docstrings, so checkpoints created with the previous CLI source correctly fail the existing source-identity resume check; no old artifacts were rewritten.

## Final readiness cleanup scope — 2026-09-21
- Added section 5 tasks before edits: explicitly declare the existing filelock dependency, correct the CLI service description, and reconcile A0 raw-row split/approved-stack wording. Numerical behavior and installed package versions remain unchanged.
- Independent read-only research review found causal windows and checkpoint/test separation coherent. Existing A0 tasks still require evidence reconciliation; source existence alone does not complete them. Final cleanup verification pending.

## Requirements reconciliation, 2026-09-21
- Reconciled later stack references to Java/Spring Boot and Expo while retaining this change's A0 fixed-holdout/two-baseline scope. Full A1 walk-forward/replay and service work belong to subsequent implementation changes.
- Current prototype exists; review ran 17 tests successfully. Older no-code/no-tests statements below are historical and superseded. Required CPU report/historical evidence and task-by-task completion are not inferred from this documentation edit.
- Tailscale is disconnected; phone work remains deferred. No numerical code changed. Final structural validation is recorded under define-product-and-stack.

## Research implementation started, 2026-09-14
- User explicitly requested project work and deferred phone connectivity.
- Added docs/REPRODUCTION.md with the paper contract, VIX ambiguity, dataset limitations, and explicit timing/cost/baseline deviations. Added the research module package definition and CPU dependency pins; environment installation is next.
- Chose Python 3.12 in an isolated project .venv. No global Python installation is modified.
- Implemented provenance-checked CSV manifests, synthetic data, chronological windows/train-only scaling, target-turnover metrics, equal-weight/60-40 baselines, and the 64-unit LSTM. Verification pending the test suite.
- Implemented bounded training, immutable run identities/artifacts, atomic completed-epoch checkpoints, checkpoint resumption, and CLI entry points. Test evaluation occurs only after validation-selected training completes. Verification pending; no task is marked complete solely because source exists.
- Added numerical and integration tests for malformed data, chronological alignment, future-data isolation, hand-calculated costs/drawdown, normalized allocations, finite gradients, checkpoint equivalence, immutable completed runs, and concurrent resume rejection. Dependency installation is still running; tests have not yet executed.

## Direction and hardware discovery
- User selected the deep-learning portfolio paper direction after considering other ideas; Flow is the intended future resume replacement.
- Created this change using the OpenSpec CLI and drafted its first-milestone proposal.
- Read the paper's methodology and training sections: one LSTM layer with 64 units, 50 observations of prices/returns, batch size 64, and generally 100 epochs.
- Read-only PC inspection: Ryzen 9 6900HS (8 cores/16 threads), 15.2 GiB OS-visible RAM, RTX 3060 Laptop GPU with 6144 MiB VRAM. Free space at inspection: C approximately 55.8 GiB, D approximately 241.6 GiB.
- Assessment: suitable for an initial small experiment; training runtime and peak memory are unmeasured. Driver visibility via nvidia-smi does not verify PyTorch or container GPU access.
- No application code, model training, package installation, file relocation, or container startup performed in this change.
- Final planning validation: all four artifacts complete; openspec validate --all --strict passed (2 items, 0 failures).

## Planning artifacts and current-state reconciliation
- Created design, portfolio-research delta specification, and verified-by-task implementation checklist; all implementation tasks remain unchecked.
- Incorporated user confirmation that the phone connects to a backend on this PC. Compose is first; K3s remains a later milestone.
- Preserved the old DESIGN.md verbatim under docs/archive/ABACUS-DESIGN.superseded.md, replaced the root roadmap, and reconciled AGENTS.md, OpenSpec config, and HANDOFF.md with the selected direction.
- First milestone covers numerical research only; remaining stack and mobile requirements are retained as follow-up milestones.
- No model/code implementation, training, connectivity test, runtime installation, or benchmark has been performed. Planning is validated; implementation remains outstanding.


## Tailscale planning refinement

Current status correction (2026-09-14): Android is confirmed; PC Tailscale installation and enrollment are verified in the separate setup-tailscale-access record. Updated this proposal/design accordingly. Earlier inspection notes below are historical; numerical requirements and implementation tasks are unchanged.
- Updated DESIGN.md, AGENTS.md, OpenSpec config/HANDOFF, and this change's proposal/design to replace the same-LAN dependency with private Tailscale connectivity.
- Proposed host-level Tailscale Serve HTTPS to a loopback-published Compose API port. Database/LocalStack remain internal; phone and PC join the same tailnet. No public Funnel planned.
- Read the existing research specification and tasks: they remain consistent because network setup belongs to the later API/mobile milestone, not the local research runner. No numerical requirements/tasks changed.
- Official sources: https://tailscale.com/docs/reference/tailscale-cli/serve and https://tailscale.com/docs/use-cases/personal-or-at-home-use/access-nas-media-file-servers .
- Tailscale CLI was not found on PATH, which is not proof of absence elsewhere. No installation, enrollment, network modification, or connectivity test was performed.
- Checked active documents for stale same-LAN requirements; strict OpenSpec validation passed (2 items, 0 failures). Research specs/tasks remain unchanged and implementation is still outstanding.

