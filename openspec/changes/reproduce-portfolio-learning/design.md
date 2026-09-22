## Context

See proposal.md for motivation. The repository contains the A0 Python prototype and tests, with no API/mobile code. The user selected the portfolio deep-learning direction and subsequently confirmed the initial topology: backend on this PC, physical phone connecting to it. Hardware inspection found an 8-core Ryzen 9 6900HS, approximately 16 GB RAM, and an RTX 3060 Laptop GPU with 6 GB VRAM. Training and container GPU access remain untested.

## Goals / Non-Goals

Goals: first establish a correct, reproducible local numerical experiment that can later be submitted through the backend. Fit one small run on the existing PC, retain CPU support, and record measured memory/runtime.

Non-goals for this change: a finished Android app, server endpoints, message queues, cluster manifests, broad parameter sweeps, brokerage integration, or profitable-trading claims. Those application milestones remain required follow-up work, not discarded requirements.

## Decisions

### Research before distributed execution
Build a local research runner first. It establishes the inputs and artifacts that the later Spring Boot service will orchestrate. Python/PyTorch is the approved research/worker stack for automatic differentiation and numerical tests. The later API uses Java/Spring Boot and the client Expo/TypeScript; see DESIGN.md.

### Bounded paper target
Reference: https://arxiv.org/html/2005.13665v3 (Zhang, Zohren, Roberts). Start with its single-layer 64-unit LSTM, 50 daily observations, price/return features, softmax long-only allocation output, Adam, and configurable epoch budget capped at 100 by default. Paper batch size is 64. Provide a tiny synthetic CPU smoke run before historical data training. The learning objective is negative Sharpe for a minimization optimizer; define near-zero variance handling explicitly.

### Data audit before reproduction claims
Record instrument identifiers, source, license/access, adjustment convention, dates, missing-data handling, and file checksums in a dataset manifest. The paper refers to VIX as if it were an ETF; resolve the precise series and investability before drawing financial conclusions. Do not silently substitute a volatility product. If original data or methodology details cannot be recovered, retain a paper-inspired label and explicit deviations. Synthetic fixtures enable implementation without paid data or resolving historical sourcing immediately.

### Causal evaluation
Keep samples chronological. The existing A0 CLI places the test boundary at floor(70% of raw rows), then the training boundary at floor(90% of those pre-test rows); explicit configuration can instead supply date boundaries. Validation therefore contains approximately the final 10% of pre-test raw rows, not necessarily 10% of usable sample targets after lookback. There is no random temporal split. A1 uses its separately specified target-count/minimum-history rule. Fit transformations only on training data. Lag holdings so period-t information cannot earn period-t returns. Compare all strategies on the same dates, cost convention, and asset universe. Implement equal-weight and fixed stock/bond baselines first. Additional original-paper baselines are needed for a full reproduction claim. Volatility scaling and monthly rebalancing are later explicit modes; do not silently mix their results with the initial unscaled experiment.

### Reproducible artifacts
Each run has an immutable manifest recording dataset checksum, code version, dependency versions, seed, split boundaries, model configuration, objective/metric definitions, cost model, hardware/device, and reproduction/deviation label. Save weights, realized returns, allocation history, metrics, and checkpoint state. Fix metric annualization and risk-free conventions. Support restart at completed-epoch checkpoints including optimizer and random state; label CPU/GPU nondeterminism rather than promise identical results on different hardware.

The A0 spec also requires repeating saved inputs/settings and reporting numerical differences. Checkpoint resumption alone does not satisfy that scenario; a bounded same-environment comparison remains required before A0 completion. A1 subsequently adds the full v2 source-snapshot/lock and third-party CLI verification contract.

### Initial deployment topology (follow-up milestone)
Physical phone -> private Tailscale connection -> host PC Spring Boot API -> PostgreSQL and LocalStack; a Python worker handles numerical jobs. Both devices join the same tailnet; they need not share a Wi-Fi network. Proposed implementation: Tailscale runs on the PC host and phone, while Tailscale Serve provides a private HTTPS endpoint forwarding to a loopback-published Compose API port. Keep database and LocalStack ports internal by default. Configure the phone with the actual Serve hostname after device enrollment; localhost on the phone refers to the phone. Verify Serve/HTTPS prerequisites, tailnet access policy, and phone access from mobile data during the API milestone. Use private Serve, not public Funnel. The PC must remain awake with the backend running. Compose remains independent of K3s, and training stays on the PC. K3s and worker recovery/scaling remain subsequent milestones. PC installation/sign-in occurred previously; Tailscale is now disconnected and phone work is deferred.

### Hardware budget
CPU execution is the mandatory default; GPU acceleration is optional. One worker/run at a time initially. Use a physical phone, no emulator requirement. Do not run the Compose and K3s environments simultaneously by default. The small model should fit the existing machine; this is an engineering estimate pending a benchmark. C has approximately 56 GiB free and D approximately 242 GiB at inspection. Consider D for large artifacts after choosing paths; no relocation has been performed.

## Risks / Trade-offs

- Unrecoverable paper data or assumptions -> explicitly report deviations and restrict reproduction claims.
- Backtest leakage or incorrect cost accounting -> synthetic known-answer tests, temporal boundary tests, and a declared convention before running held-out evaluation.
- Overfitting -> validation-only tuning, held-out results, multiple seeds, and simple baselines; a negative result is still valid.
- Approximately 16 GB RAM shared with tools/containers -> stage services and benchmark one experiment before adding parallelism.
- CUDA setup differs between host and containers -> CPU fallback and a separate GPU smoke check during implementation; GPU purchase is unnecessary to begin.

## Migration Plan

Preserve the original Abacus document under docs/archive and replace the root design with a current roadmap. This is a greenfield project; no database or deployed-service migration exists. Keep this change active until its research tasks and evidence are complete. Later changes introduce the API, phone app, Compose stack, and K3s path.

## Open Questions

- Exact historical data provider/instrument mapping: the manifest and audit task support documenting unavailable originals without blocking synthetic development.
- An isolated Python 3.12 .venv with CPU PyTorch 2.8.0 exists. Do not mutate global Python; retain current pins until an explicit tested upgrade.
- Android is confirmed. PC Tailscale installation/enrollment are verified in setup-tailscale-access. Phone enrollment and HTTPS verification are deferred at the user's request; no Serve endpoint exists yet.

