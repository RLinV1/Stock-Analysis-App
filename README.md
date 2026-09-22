# Portfolio Lab

A mobile experiment lab for reproducible portfolio-learning research.

**Current state:** a Python/PyTorch prototype exists, with 17 tests passing in the 2026-09-21 review. No verified historical reproduction, API, mobile app, or container deployment exists yet.

## What this investigates

[Deep Learning for Portfolio Optimization](https://arxiv.org/html/2005.13665v3) trains a network to output portfolio allocations directly. This project will compare its method with baselines, disclose assumptions, and report results across seeds whether or not they match the paper.

The paper's volatility-series identity and several implementation details need clarification. The local audit notes contain observations that have not been independently reproduced from saved scripts and manifests. They are hypotheses to investigate, not established flaws in the paper.

## Stack and sequence

- Python/PyTorch for research and background training.
- Java/Spring Boot API with PostgreSQL, Liquibase, and LocalStack S3.
- React Native/Expo client for physical Android and web.
- Docker Compose first; an additional K3s path later.

First finish the bounded local prototype, then extend the research protocol and build recoverable background jobs. Planned results bind code, data, configuration, and numerical conventions to a manifest.

## Read next

- [Start here](docs/START-HERE.md)
- [Design and milestones](DESIGN.md)
- [Technical contract](docs/SPEC.md)
- [Product requirements](docs/PRD.md)
- [Current readiness](docs/READINESS.md)
- [Paper background](docs/PAPER-BACKGROUND.md)
- [Implemented numerical deviations](docs/REPRODUCTION.md)
- [Requirements review and resolution](docs/REQUIREMENTS-REVIEW.md)
- [Security](docs/SECURITY.md) and [toolchain](docs/TOOLCHAIN.md)

Agents must read [AGENTS.md](AGENTS.md), [handoff](openspec/HANDOFF.md), OpenSpec configuration/specs, and active changes before editing. Record every logical change immediately.

## Boundaries

Research only: no brokerage execution or personalized investment recommendations. Historical outcomes do not predict future returns. Tailscale is disconnected and phone connectivity is deferred.

Apache-2.0 is proposed; no license has been adopted yet. Do not redistribute vendor data or derived artifacts without recorded permission for the specific artifact. CI uses synthetic fixtures.
