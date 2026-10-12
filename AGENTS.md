# Project working agreement

- Document every logical change in OpenSpec, including minor fixes, major features, tooling, infrastructure, and documentation.
- Before implementation, create or update a change with scope, rationale, and tasks. Immediately after each logical change, update its implementation.md with what changed, verification results, and limitations; update its tasks. Do not defer documentation until session end.
- Add behavioral spec deltas when behavior changes. Validate and archive completed changes, preserving their implementation history.
- Required stack: React Native/Expo/TypeScript mobile client, Java/Spring Boot backend, Python/PyTorch research worker, Liquibase, PostgreSQL, LocalStack, and an additional K3s deployment path. The 2026-09-21 requirements reconciliation supersedes Kotlin/Quarkus.
- Docker Compose must independently start the backend and required infrastructure without Kubernetes. The user confirmed a physical Android phone as the mobile client.
- Selected direction: Deep Learning for Portfolio Optimization research and a mobile experiment lab. DESIGN.md is the current roadmap; docs/SPEC.md is the canonical planned technical contract; docs/archive/ABACUS-DESIGN.superseded.md is historical only. Backend/worker run on this PC; phone access over private Tailscale is deferred and Tailscale is disconnected at the user's request. Compose first, K3s later. Distinguish implemented behavior, planned requirements, and proposed defaults.
- Build a small working vertical slice first. Never describe planned capabilities as implemented.
- UI direction: apply the user's preserved apple-design skill at docs/reference/apple-design.md using docs/UI-DESIGN.md for React Native/Android and web adaptations. Keep native Android behavior, accessibility and honest experiment states. Validate rendered UI/device behavior before claiming client completion.

## Agent handoff

- At session start, read this file, `openspec/HANDOFF.md`, `openspec/config.yaml`, relevant current specs, and active change artifacts before editing. Inspect the actual files and working tree; do not assume the handoff is current.
- After every logical change, update its implementation record and `openspec/HANDOFF.md` whenever project status, decisions, checks, blockers, or next steps change. Before ending a work session, reconcile both with the actual work, including partial or failed work.
- Keep the handoff concise: confirmed decisions, assumptions, unresolved questions, active change references, verification evidence, blockers, and the next concrete step. Link to detailed artifacts rather than duplicating them.
- Keep relevant design documents and configuration consistent with accepted decisions. Label superseded proposals clearly. Never promote a brainstormed idea or recommendation to an accepted decision without user agreement.
- Do not mark tasks complete or archive changes while required implementation or verification remains unfinished. Document unrun checks explicitly.
- If instructions conflict with current code or specs, investigate and record the discrepancy instead of silently choosing a version. User instructions take precedence.


