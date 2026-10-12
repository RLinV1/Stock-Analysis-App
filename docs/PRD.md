# Portfolio Lab — product requirements

Version 0.2, corrected 2026-09-21. Planned product behavior; see [DESIGN.md](../DESIGN.md) for implemented versus future milestones and [SPEC.md](SPEC.md) for the canonical contract.

## Purpose and users

UI direction follows the user-supplied apple-design skill, adapted for Expo/Android and web in [UI-DESIGN.md](UI-DESIGN.md). A synthetic preview shell and seven component tests exist; the full interaction/accessibility, live-service and device checks remain planned.

Help a researcher run, compare and reproduce portfolio-learning experiments, and let an Android user monitor work running on their PC. A reviewer should be able to identify the exact inputs behind a result without trusting a headline number. A contributor should be able to add a strategy through a documented interface.

The contribution is reproducible evidence and reliable execution. Matching the paper, outperforming baselines or finding a flaw is not required for an honest result. Do not present proposed contributions as proven novelty or publication acceptance.

## Product boundary

Historical research only. No broker credentials, orders, real-money execution, risk profiling or personalized advice. Display a research-use notice alongside portfolio results. Do not describe this boundary as proof of legal compliance.
No multi-tenant SaaS, billing or account-management product in the current scope. A single-operator authentication mechanism is still required before network-accessible compute.

## Stories and acceptance

| Story | Milestone | Acceptance |
|---|---|---|
| Configure a bounded experiment | A0 CLI, B API, C UI | Record all settings; reject invalid ranges with field-specific errors; distinguish paper settings from chosen defaults |
| Run and recover locally | A0 | Save progress/checkpoints; reject incompatible resume; record runtime and memory-measurement limits |
| Compare complete research results | A1 | All seven paper baselines on identical dates/costs; undefined metrics carry reasons; all deviations linked |
| Seed/cost sweeps | A1 | Record every requested member, failure and seed; report mean, spread and per-run values without selecting favorable runs |
| Verify an exported manifest | A1 CLI, B HTTP, C UI | Compare immutable inputs first and metrics second; distinguish unavailable inputs, input mismatch, runtime failure and numerical mismatch |
| Launch and monitor remotely | B/C | Return job ID promptly; report attempts, fold/epoch, actual cancellation status and sanitized failure; retries do not duplicate work |
| Recover after worker crash | B | Expired lease is reclaimed; stale worker cannot publish; committed results survive restart |
| Inspect equity and allocations | C | Model and relevant baselines on shared dates; ordered assets and raw/scaled distinction; Android and web charts tested |
| Read results offline | C | Previously loaded results show cache timestamp; submit/cancel/verify disabled offline |
| Compare instrument assumptions | A1 | Separate non-investable fidelity hypothesis and tradable extension; compare on common protocol/window and label unavailable evidence |
| Add architectures/universes/objectives | Later | New explicit scope, comparable protocol and tests; never silently change the reproduction claim |

Cost sensitivity may have no crossing or multiple crossings. Report the evaluated range and observed crossings; never invent a unique break-even cost. Allocation behavior during COVID is an observed comparison, not a target to tune against held-out data.

## Scope and success

A0 is the existing bounded prototype, owned by reproduce-portfolio-learning. A1 adds fuller research and CLI verification. B adds API/worker/PostgreSQL/Liquibase/LocalStack/Compose, with ONNX inference as a parity-gated extension. C adds Expo physical Android and web. D adds K3s. Neither a UI nor phone enrollment gates A0.

Success means:
- Results include baselines, evidence identity and deviations.
- A supported replay yields an explicit outcome under declared tolerances.
- Duplicate submissions and worker crashes do not create duplicate completed results.
- Setup time and runtime are measured on the user's PC; a “15 minute setup” is an aspiration until tested.
- Resume bullets describe only delivered capabilities and measured outcomes.

## Publication and unresolved choices

Publish positive or negative findings with limitations after evidence is reproducible. A missing paper input is uncertainty, not proof the paper is wrong.
Apache-2.0 remains proposed. Provider and artifact permissions must be recorded before publishing; synthetic CI fixtures are the default. No paid data/compute or public deployment is authorized.
