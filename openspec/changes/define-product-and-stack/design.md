## Context

See proposal.md for the correction request. The local Python prototype exists; newer product documents added a Spring Boot/Expo architecture without reconciling agent instructions. The review found substantive research and execution-contract defects.

## Goals / Non-Goals

Goals: one current stack and technical contract, honest evidence labels, bounded milestone ownership, implementable job/replay semantics.
Non-goals: code implementation, dependency upgrades, live connectivity, claiming historical replication, granting a public license or publishing the project.

## Decisions

### One canonical technical contract
docs/SPEC.md owns API/schema/job/manifest details. Root DESIGN.md owns architecture and sequence, PRD owns stories. This avoids two conflicting API/table inventories.

### Current stack and phase ownership
Reconcile to Java/Spring Boot, Expo/TypeScript, Python/PyTorch, PostgreSQL/Liquibase, LocalStack, Compose and later K3s. FastAPI/Django are unselected alternatives. A0 stays in reproduce-portfolio-learning; A1 fuller research and B/C/D service/client/deployment require subsequent implementation scope.

### Durable PostgreSQL jobs
Use the existing database for job ownership and transactional registration. Leases, fencing and request idempotency handle retries; S3 objects are attempt-scoped, with DB completion only after verified publication. Alternatives such as a separate broker can be revisited if measured throughput requires them; no exactly-once execution claim is made.

### Versioned replay
Separate input mismatch, unavailable inputs, runtime failure and numerical mismatch. Record per-fold preprocessing/models and explicit serving selection. Source snapshots support development outside clean Git; a hash alone is insufficient without retrievable inputs. No silent migration from A0 local schema.

### Research uncertainty
Remove dynamic-return impossibility claims. Retain earlier figures as unverified observations pending reconstruction. Use later tradable folds with real pre-test history and VIXY throughout; do not splice price levels. Matched-window comparisons limit protocol confounding.

### Gates by action
Synthetic implementation does not depend on phone setup or a public license. Data access/publication, network exposure and model serving require their own checks. Tailscale stays disconnected.

### First usable delivery
Stage A0, the minimum versioned schema/replay contract, then a synthetic B/C submit-status-results slice before the larger A1 studies. A1/B/C/D remain required scopes; early partial delivery does not complete a milestone or remove an endpoint/research requirement. This is a delivery-order refinement, not a new product direction. Root DESIGN owns the sequence and READINESS owns acceptance evidence. Compose starts PC services; the Expo phone client is installed separately.

### Stack sign-off review
The current stack is explicitly approved in the user's AGENTS.md. Official-source checks support the architecture; exact locked integrations remain untested. Current LocalStack requires a private token and verified plan features, so synthetic inputs do not imply offline full-stack startup. Windows uses a Linux-container runtime, with k3d/K3s as the later additional path. No vendor account creation or paid plan is included.

Daily inference uses changing historical windows with a fixed fold model/scaler; two-year retraining occurs only at fold boundaries. Independent supervision renews leases and enforces cancellation; token and unexpired lease checks fence every committed write. Details and required tests are canonical in docs/SPEC.md.

## Risks / Trade-offs

- More explicit contracts than current code supports -> label all new behavior planned and retain unchecked implementation tasks.
- Incomplete historical data/access -> preserve synthetic progress and clearly scope claims.
- Shared database coupling -> version its contract through Liquibase and test worker/API compatibility.
- Numerical/environment variation -> declared tolerances and explicit replay outcomes, never relaxed silently.
- Documentation stack reconciliation may hide history -> preserve implementation records and review resolution.

## Migration Plan

Update existing documents and active deltas only. No runtime migration or deployment. Validate structure and links, scan active claims and status, and leave research tasks open. A0 introduces portfolio-research in main specs first; later additions must be merged without replacing its requirements.

## Open Questions

Public code license, provider-specific access, A1 estimator/EWM/exposure defaults and tested release pins remain milestone-specific decisions. No public/paid deployment or renewed phone setup is authorized.
