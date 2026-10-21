# Stock-Analysis-App

A mobile experiment lab for reproducible portfolio-learning research, developed as Portfolio Lab.

**Current state:** the Python/PyTorch prototype supports bounded synthetic training, checkpoint recovery, Git revision metadata and saved-experiment repeat comparison. Retained synthetic repeat/resume matched exactly; see [A0 evidence](docs/A0-EVIDENCE.md). Spring Boot implements authenticated submit/status/cancel/list and verified artifact/report/equity/allocations routes at source/unit level; a PostgreSQL-backed Python worker and Compose configuration exist. The Android/web client has 91 component/contract tests, clean TypeScript/lint and Android/web exports. Java startup/repository and Python worker PostgreSQL checks pass. A real browser/API/PostgreSQL connect/list/submit/status/cancel smoke and separate mocked Results rendering review pass as of 2026-10-15. API/worker image builds, non-root migration/API/database restart and an offline worker child also pass; [container evidence](docs/evidence/container-images-2026-10-15/README.md) records limits. S3/worker publication, full Compose, physical Android, historical reproduction and K3s remain unverified. [The handoff](openspec/HANDOFF.md) records current checks and blockers.

## What this investigates

Current uncommitted research edits change the runner/repeat source and add walk-forward, sweep, synthetic learnability and explicit local normalization/objective-window controls. They have **not been imported, tested or run** under the current file-only instruction. The evidence above predates those edits; it does not establish current-source compatibility or completed A1 capabilities.

[Deep Learning for Portfolio Optimization](https://arxiv.org/html/2005.13665v3) trains a network to output portfolio allocations directly. This project will compare its method with baselines, disclose assumptions, and report results across seeds whether or not they match the paper.

The paper's volatility-series identity and several implementation details need clarification. The local audit notes contain observations that have not been independently reproduced from saved scripts and manifests. They are hypotheses to investigate, not established flaws in the paper.

## Stack and sequence

- Python/PyTorch for research and background training.
- Java/Spring Boot API with PostgreSQL, Liquibase, and LocalStack S3.
- React Native/Expo client for physical Android and web.
- Docker Compose first; an additional K3s path later.

First finish the bounded local prototype, then extend the research protocol and build recoverable background jobs. Planned results bind code, data, configuration, and numerical conventions to a manifest.

## Run the local prototype

From the project root in PowerShell, using the existing project Python environment:

```powershell
$labPython = ".\.venv\Scripts\python.exe"
$demoId = [guid]::NewGuid().ToString("N")
$dataset = & $labPython -m portfolio_lab.cli synthetic "data/demo-$demoId" --observations 420
$runRoot = "runs/demo-$demoId"
$run = & $labPython -m portfolio_lab.cli run $dataset --output $runRoot --epochs 3 --seed 7 --cost-bps 1
$comparison = & $labPython -m portfolio_lab.cli repeat $run --output $runRoot
Get-Content $comparison
```

Each run saves its manifest, copied dataset, report, allocation history, model and checkpoint. Repeat writes a separate comparison and fresh run; it never overwrites the reference. A matched repeat exits 0; different/incompatible/unavailable/failed outcomes retain a report and exit 1. Invalid command usage exits 2. Paths/settings for an existing run come from its saved manifest, not current CLI defaults.

To exercise the versioned synthetic request that the later API and worker will share:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location).Path 'research\src')
& .\.venv\Scripts\python.exe -m portfolio_lab.cli synthetic-run contracts\examples\synthetic-smoke.v1.json --output runs\request-demo
```

The command prints the completed run directory. It retains `request.json`, `request.sha256`, the copied generated dataset and the A0 report. The [closed request schema](contracts/synthetic-run-request.v1.schema.json) permits only small synthetic CPU jobs; its hash identifies the request for future idempotency work, not v2 reproducibility. This command runs locally without an HTTP API, database or container.

## Experimental walk-forward source

The current uncommitted research draft adds explicit fold-aware training, local group orchestration, continuous boundary accounting and a separate CLI. It was written under a code-only/no-process instruction and has **not been run or verified**. Earlier A0, container and planner evidence does not validate this draft. See [walk-forward status and limitations](docs/WALK-FORWARD.md) and the [active implementation record](openspec/changes/add-walk-forward-training/implementation.md); no trained walk-forward model, historical finding or completed research milestone is claimed.

To exercise a completed-epoch interruption and resume with the same dataset:

```powershell
$paused = & $labPython -m portfolio_lab.cli run $dataset --output $runRoot --epochs 3 --stop-after-epochs 1
& $labPython -m portfolio_lab.cli run $dataset --output $runRoot --resume $paused
```

These commands use synthetic data and the small default 64-unit/50-observation CPU model. They are engineering checks, not investment-performance evidence. Repeat requires matching source bytes/runtime and uses absolute tolerance 1e-7; it is not the planned v2 verifier. See [implemented scope](docs/REPRODUCTION.md) for identity and comparison limits. This quickstart assumes the existing `.venv`; a clean locked installation is still a later reproducibility check.

## Read next

- [Running on Windows, macOS, Linux and Docker Compose](docs/RUNNING.md)
- [Historical Yahoo data through 2026 (code ready, not yet run)](docs/HISTORICAL-DATA.md)
- [Start here](docs/START-HERE.md)
- [Design and milestones](DESIGN.md)
- [Technical contract](docs/SPEC.md)
- [Product requirements](docs/PRD.md)
- [Current readiness](docs/READINESS.md)
- [UI direction and acceptance checks](docs/UI-DESIGN.md)
- [Android/web preview and test commands](mobile/README.md)
- [Backend scaffold and tests](backend/README.md)
- [Paper background](docs/PAPER-BACKGROUND.md)
- [Implemented numerical deviations](docs/REPRODUCTION.md)
- [Unrun controlled learnability gate](docs/SYNTHETIC-LEARNABILITY.md)
- [Unrun explicit normalization controls](docs/NORMALIZATION-DIAGNOSTIC.md)
- [Unrun explicit objective-window controls](docs/SHARPE-WINDOW-DIAGNOSTIC.md)
- [Unrun isolated cost-objective math](docs/COST-OBJECTIVE-PRIMITIVE.md)
- [Requirements review and resolution](docs/REQUIREMENTS-REVIEW.md)
- [Security](docs/SECURITY.md) and [toolchain](docs/TOOLCHAIN.md)

Agents must read [AGENTS.md](AGENTS.md), [handoff](openspec/HANDOFF.md), OpenSpec configuration/specs, and active changes before editing. Record every logical change immediately.

## Boundaries

Research only: no brokerage execution or personalized investment recommendations. Historical outcomes do not predict future returns. Tailscale is disconnected and phone connectivity is deferred.

Project code is licensed under [Apache-2.0](LICENSE), selected by the project owner on 2026-10-21. This does not grant rights to third-party data or derived artifacts; record permission for each artifact before redistribution. CI uses synthetic fixtures. Source is published at [RLinV1/Stock-Analysis-App](https://github.com/RLinV1/Stock-Analysis-App); application deployment remains unapproved.
## Explicit research sweep source (unverified)

Draft research source now includes explicit seed/cost planning, descriptive
summaries, sequential snapshot-bound walk-forward orchestration and standalone
offline-summary/training entry points. See [research sweep scope and limitations](docs/RESEARCH-SWEEPS.md).
New source and regression cases have not been executed under the user's no-process
instruction. In particular, real-loader/training integration and final report
compatibility are not verified. No historical performance or completed research
capability is claimed.
