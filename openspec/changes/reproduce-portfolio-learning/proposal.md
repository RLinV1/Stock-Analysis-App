## Why

The user selected a deep-learning portfolio research project to replace Flow on their resume. A bounded reproduction of Zhang, Zohren, and Roberts' Deep Learning for Portfolio Optimization provides a concrete learning objective and measurable research evidence before building a distributed experiment service and mobile app.

## What Changes

- Continue after the version-control work: implement a bounded local `repeat` command for completed A0 runs, compare saved outputs without mutating the reference, retain CPU smoke/resume/repeat evidence, and reconcile the checklist with verified artifacts. This does not implement the externally supplied v2 manifest verifier.

- Final-readiness cleanup: declare the directly imported filelock dependency at its existing installed version, remove the stale CLI service reference, and align validation-split/stack descriptions with actual A0 behavior. No numerical algorithm or dependency upgrade is included.

- Establish the selected direction and supersede the Abacus proposal while preserving it as historical context.
- Implement the first milestone: a local, CPU-capable research runner for the paper's small LSTM and baseline strategies, with dated datasets, chronological evaluation, and reproducible result manifests.
- Separate paper-aligned experiments, documented deviations, and later long-term-investing extensions.
- Require an instrument/data audit before claiming an exact reproduction; the paper's VIX description needs clarification.
- Plan later Java/Spring Boot, PostgreSQL/Liquibase, LocalStack, Compose, K3s, and mobile delivery as subsequent changes, not first-milestone implementation tasks.

## Capabilities

### New Capabilities
- `portfolio-research`: Versioned datasets, causal model evaluation, bounded local training, baseline comparison, and reproducible experiment evidence.

### Modified Capabilities
None. Existing change-documentation requirements continue to apply.

## Impact

The Python/PyTorch research module, tests, and report outputs are partially implemented. Python/PyTorch is the approved research/worker stack; Java/Spring Boot is the API and Expo/TypeScript is the client. No broker integration, trades, paid data, paid compute, or performance improvement is assumed. CPU smoke reporting, historical evidence and task-level completion remain outstanding.

## Confirmed Scope and Proposed Defaults

Confirmed: deep-learning direction, resume objective, Spring Boot/Expo application direction, Python/PyTorch training, and continuous OpenSpec updates.
Confirmed mobile platform: physical Android phone. Reviewed engineering defaults: one CPU-capable experiment at a time and a bounded research milestone before distributed execution. Dataset provider and exact instrument mapping must be resolved during the documented data audit before historical-result claims.

Connection refinement: use Tailscale between the physical phone and PC for private remote access. This is part of the later API/mobile milestone and does not expand the first numerical-research milestone. Proposed HTTPS exposure uses Tailscale Serve; PC installation/enrollment occurred, but Tailscale is now disconnected at the user's request; phone access remains deferred.
