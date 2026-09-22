# Project handoff

Updated 2026-09-21.

## Current direction
- Latest request completed: final stack/readiness review and a clear implementation game plan. Independent architecture/research reviews support starting staged implementation. Documentation and small A0 packaging cleanup are applied and verified; full-stack integration remains unbuilt.
- Approved stack: React Native/Expo/TypeScript (physical Android first, web target); Java 21/Spring Boot API; Python/PyTorch research worker; PostgreSQL/Liquibase; LocalStack S3; independent Docker Compose and later k3d/K3s. Kotlin/Quarkus is superseded.
- PC hosts API/worker. One CPU run initially. No live trading, broker linkage, paid data/compute or public deployment. Apache-2.0 remains proposed.
- [DESIGN](../DESIGN.md) owns the roadmap; [SPEC](../docs/SPEC.md) owns the planned contract; [READINESS](../docs/READINESS.md) gives delivery acceptance checks and environment gaps.
- Delivery order: bounded A0, minimum shared schema/replay, synthetic Compose/Android submit-status-results/recovery slice, fuller A1/B/C scope, then K3s. Partial slices do not complete a milestone or remove its requirements.

## Actual implementation and evidence
- research/src/portfolio_lab contains CSV manifests, synthetic data, causal windows/scaling, metrics/two baselines, LSTM, bounded fixed-holdout training, checkpoints and CLI.
- No verified historical reproduction, API, mobile client, Compose, durable queue, K3s, ONNX or saved-manifest comparison yet. Source fingerprints are not full replay snapshots; this directory is not a Git repository.
- Final review: fresh prototype suite passed 17 tests in 9.65s; strict OpenSpec validation 4/4 and 41-document file/heading/duplicate-title checks passed. Python 3.12.14/PyTorch 2.8.0+cpu import/tensor smoke, dependency alignment, pip consistency and CLI startup pass. These are not full-stack or historical evidence.
- A0 cleanup declared existing filelock 3.32.6 explicitly and removed stale CLI wording. No numerical algorithm or installed version changed. CLI source bytes affect fingerprints, so existing checkpoints require their original source identity.
- A0 raw-row split is documented accurately; saved-experiment comparison remains task 3.4. Original A0 tasks require evidence reconciliation, not automatic completion from source presence.

## Toolchain and constraints
- Java 21.0.2 installed; PATH selects Java 24.0.1. Select/lock a maintained Java 21 patch before backend work.
- Node 22.12.0 is below current Expo SDK 57 minimum. Node 24 LTS + compatible stable Expo 57 patch is a reviewed candidate, not an installed/tested lock.
- Docker 28.3.2/Compose 2.38.2 installed; desktop-linux engine unavailable in elevated read-only check. No services started.
- LocalStack token/plan persistence, full Windows/Linux dependency locks and Android/web builds remain unverified. See [TOOLCHAIN](../docs/TOOLCHAIN.md).
- Earlier hardware inspection: Ryzen 9 6900HS, about 16 GB RAM, RTX 3060 Laptop 6 GB. GPU support/performance untested; benchmark before increasing concurrency.
- OpenSpec 1.13.0 works via %APPDATA%/npm/openspec.cmd with appropriate permissions.

## Active changes
- [define-product-and-stack](changes/define-product-and-stack/tasks.md): section 9 final readiness review complete. Broader research/default/evidence tasks remain open; no archive.
- [reproduce-portfolio-learning](changes/reproduce-portfolio-learning/tasks.md): A0; readiness cleanup section 5 complete. Runtime/report/historical/replay evidence remains to finish. Detailed checks in its implementation.md.
- [setup-tailscale-access](changes/setup-tailscale-access/tasks.md): deferred at user request.

## Tailscale
User requested stop. On 2026-09-21 tailscale down exited 0; Self.Online=false and health reported stopped. Installed Windows service remains running. No Serve endpoint or phone verification. Do not reconnect or prompt for enrollment during local work.

## Next concrete step
Resume A0: reconcile task evidence, retain a small measured CPU run with resume/repeat reports, and record a bounded historical experiment or explicit data-access limitation. Scope shared contract and B/C changes before implementing them. Do not repeat a broad stack review unless new evidence warrants it.
