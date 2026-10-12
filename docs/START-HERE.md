# Start here

Portfolio Lab is a research project plus a mobile interface. You will train a small portfolio-allocation model, compare it with simple strategies, and make its results reproducible. The phone will eventually let you launch and inspect experiments running on your PC.

## What exists
A Python/PyTorch prototype has a fixed chronological split, two baselines, saved artifacts, checkpoint recovery, local repeat checks, and a bounded versioned synthetic request command. All 74 research tests passed on 2026-10-11. An Android/web Expo preview shell has seven passing component tests and web/Android bundles. It uses synthetic sample screens and cannot start a real service job. There are no verified historical results or working API/mobile service integration yet.

## What gets built
1. A0: finish and measure the bounded local prototype.
2. A1: fuller paper methodology, walk-forward evaluation, seven baselines, seed/cost comparisons, and CLI verification.
3. B: Java/Spring Boot API and recoverable Python jobs with PostgreSQL/Liquibase, LocalStack and Docker Compose.
4. C: React Native/Expo on physical Android, plus a web target.
5. D: an additional K3s deployment.

See [DESIGN.md](../DESIGN.md) for milestone ownership and [READINESS.md](READINESS.md) for the next checks.

## What makes it useful
The engineering contribution is a result that can be traced to its inputs and rerun, plus jobs that recover safely after interruption. The research contribution depends on what the experiments actually show. Neither positive returns nor a flaw in the paper is assumed.

The [volatility note](FINDING-VIX-INSTRUMENT.md) and [data note](FINDING-DATA-SOURCING.md) identify unresolved questions. Their earlier measured figures lack saved reconstruction evidence and must not be presented as verified findings.

## Practical limits
One CPU run initially. The existing PC is the host. Tailscale and phone setup are deferred at your request; they do not block numerical work. No paid services or public deployment. A public license remains undecided.

[SPEC.md](SPEC.md) is the planned technical contract; [REPRODUCTION.md](REPRODUCTION.md) describes what the current code actually implements.
