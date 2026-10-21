# Stock-Analysis-App

A mobile experiment lab for reproducible portfolio-learning research, developed as Portfolio Lab.

It tests one idea from the paper [Deep Learning for Portfolio Optimization](https://arxiv.org/html/2005.13665v3) (Zhang, Zohren and Roberts, 2020): instead of predicting the market and then building a portfolio from those predictions, train a neural network to choose the portfolio directly. The project reproduces that method, tests it on newer data through 2026, and lets you launch and review experiments from a phone.

## How portfolios are normally built

The usual approach has two separate steps:

1. **Forecast.** Estimate each asset's expected return and how assets move together (their covariance), usually from recent history or a separate prediction model.
2. **Optimize.** Feed those estimates into an optimizer, classically Markowitz mean-variance, which picks the weights with the best expected return for the risk taken.

The weak point is the handoff between the steps. The forecast is trained to be accurate, not to produce a good portfolio, and small forecast errors can swing the optimizer to extreme weights. Simpler alternatives, like fixed splits such as 60% stocks / 40% bonds rebalanced on a schedule, avoid forecasting entirely but never adapt to the market.

## How this model works

The paper removes the forecasting step. One network goes straight from recent market history to portfolio weights, and it is trained on the thing an investor actually cares about: risk-adjusted return.

- **Assets:** four ETFs, one per asset class: VTI (US stocks), AGG (US bonds), DBC (commodities) and a volatility asset (the VIX index, or the tradable VIXY fund).
- **Input:** the last 50 trading days of each asset's price and daily return.
- **Network:** a single LSTM layer with 64 units, a type of recurrent network that reads the 50 days in order and summarizes them.
- **Output:** a softmax layer that turns the summary into four weights that are all zero or positive and add up to 100%. That is a long-only portfolio with no leverage and no short selling.
- **Objective:** the [Sharpe ratio](docs/PAPER-BACKGROUND.md#4-the-objective-function) of the portfolio's returns, meaning average return divided by its volatility. The network adjusts itself to make this as high as possible.
- **No peeking ahead:** weights chosen with data up to day t−1 are scored only on day t's returns.

So the model never predicts a price. It learns, for example, to move into bonds when its inputs look like the start of a stock sell-off, because doing so improved the Sharpe ratio on its training data.

## How we'll train it and what we'll use

- **Data:** daily Yahoo Finance history from 2006 to October 2026, downloaded with yfinance and stored locally with file hashes so every run can be traced to its exact inputs. Prices include reinvested dividends. See [historical data](docs/HISTORICAL-DATA.md).
- **Code:** Python 3.12 and PyTorch, on this PC's CPU at first.
- **Settings:** the paper's values where it states them, the project's recorded defaults where it does not: Adam optimizer, learning rate 0.001, batches of 64 days, up to 100 passes over the training data. Inputs are standardized using training-period statistics only.
- **Walk-forward retraining:** train on all data before a test period, hold back the last 10% of it to pick the best training pass, then test on the next two years the model has never seen. Move forward two years and repeat. Stitching the test periods together gives one continuous out-of-sample result, the same protocol the paper uses.
- **Two test windows:** the paper's own (2011 to April 2020) and an extended one through 2026, each run with the VIX index and with VIXY.
- **Fair comparison:** every strategy pays the same trading cost (1 or 10 basis points per unit of turnover). The model is compared against simple strategies and against itself across several random seeds, which the paper did not report.
- **Later:** the same training runs as background jobs. The phone app submits a job to the Spring Boot API, a Python worker trains it, and results come back as equity curves and allocation charts.

## Why this project exists

The paper reports a Sharpe ratio of 1.96, well ahead of its comparison strategies, but it does not publish its data or code, reports one run with no variation between seeds, and names "VIX" as an asset even though the index itself cannot be bought. This project asks three questions:

1. Does the method reproduce when every unstated choice is written down?
2. How much do results vary from one training run to the next?
3. Does it still work with a volatility fund you can actually trade, and on the years after the paper (2020-2026)?

Results get reported whether or not they match the paper. This is a research tool, not investment advice or a trading system. What is built and verified so far is tracked in [the handoff](openspec/HANDOFF.md).

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
