# Portfolio Lab

A mobile experiment lab for reproducible portfolio-learning research.

**Current state:** the Python/PyTorch prototype supports local training, checkpoint recovery and a saved-experiment repeat comparison. New runs include Git revision metadata. All 74 research tests pass, including 15 new bounded synthetic-request tests; retained synthetic repeat and resume matched exactly. See [A0 evidence](docs/A0-EVIDENCE.md). Spring Boot now has source-level submit/status/cancel routes, migration/repository code and six passing contract/MVC tests, but no live database verification. An Android/web Expo preview shell has seven passing component tests and successful web/Android bundles; it cannot submit experiments. No verified historical reproduction, working API, live mobile flow, or container deployment exists yet.

## What this investigates

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

To exercise a completed-epoch interruption and resume with the same dataset:

```powershell
$paused = & $labPython -m portfolio_lab.cli run $dataset --output $runRoot --epochs 3 --stop-after-epochs 1
& $labPython -m portfolio_lab.cli run $dataset --output $runRoot --resume $paused
```

These commands use synthetic data and the small default 64-unit/50-observation CPU model. They are engineering checks, not investment-performance evidence. Repeat requires matching source bytes/runtime and uses absolute tolerance 1e-7; it is not the planned v2 verifier. See [implemented scope](docs/REPRODUCTION.md) for identity and comparison limits. This quickstart assumes the existing `.venv`; a clean locked installation is still a later reproducibility check.

## Read next

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
- [Requirements review and resolution](docs/REQUIREMENTS-REVIEW.md)
- [Security](docs/SECURITY.md) and [toolchain](docs/TOOLCHAIN.md)

Agents must read [AGENTS.md](AGENTS.md), [handoff](openspec/HANDOFF.md), OpenSpec configuration/specs, and active changes before editing. Record every logical change immediately.

## Boundaries

Research only: no brokerage execution or personalized investment recommendations. Historical outcomes do not predict future returns. Tailscale is disconnected and phone connectivity is deferred.

Apache-2.0 is proposed; no license has been adopted yet. Do not redistribute vendor data or derived artifacts without recorded permission for the specific artifact. CI uses synthetic fixtures.
