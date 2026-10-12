# Project handoff

Updated 2026-10-11.

## Latest direction
- User requested continued implementation after Claude's Git work, thorough preparation/testing, the supplied apple-design UI skill, then continuation on GPT-6-Sol. Planning/research checks are complete. The app accepted a continuation message to this task with model gpt-6-sol on 2026-10-09; this records the accepted request, not an independent runtime-model inspection.
- Keep replies concise per the user-invoked caveman skill. Do not spawn sub-agents without explicit user or applicable repository/skill authorization.
- Approved stack: React Native/Expo/TypeScript for Android and web now, iOS port later; available physical phone is Android; Java 21/Spring Boot; Python/PyTorch; PostgreSQL/Liquibase; LocalStack S3; standalone Compose and later k3d/K3s. PC hosts computation, initially one CPU run.
- Apply [UI-DESIGN](../docs/UI-DESIGN.md) and the preserved [apple-design skill](../docs/reference/apple-design.md) for UI. Preserve Android navigation/accessibility. Seven preview component tests pass; full live-state/device checks remain planned.
- A Transformer comparison was discussed as a proposed later experiment, not an approved replacement for the LSTM paper baseline.

## Actual implementation and checks
- Python A0 includes data manifests, causal windows/scaling, two baselines, a 64-unit LSTM, fixed-holdout training, epoch recovery, Git revision metadata and local saved-run repeat comparison.
- All 59 tests passed in 54.22s. Independent code review found no material blockers. Final OpenSpec validation passed 5/5; 49 Markdown documents had zero link/heading/duplicate-requirement issues. Git diff --check passed; retained source/artifact/skill hashes verified.
- [A0-EVIDENCE](../docs/A0-EVIDENCE.md) links retained runs under runs/cpu-evidence-2026-10-09-a3ea8ef5. Fresh CLI repeat and one-epoch interruption/resume matched with zero maximum absolute difference; reference hashes and resumed manifest remained unchanged.
- Synthetic 420 rows, three epochs, lookback 50, hidden size 64, seed 7, 1 bps: 5.899s reference call, 0.421s narrower training/evaluation timer, 284.81 MiB maximum sampled RSS. Not a continuous peak, historical result or performance benchmark; GPU untested.
- Git HEAD remains eab38cc573db43c27ed97bc2420580a57b78464d. Implementation is uncommitted. Dirty-source metadata is explicit; no source snapshot/full lock or external v2 replay exists.
- No API, Compose, durable worker, K3s, ONNX or historical research verification. The Expo shell has seven passing component tests and Android/web exports, but no physical-device check. No services, remotes, commits or network access configuration.

## Active changes
- [build-synthetic-service-slice](changes/build-synthetic-service-slice/tasks.md): task 1 complete. Spring contract/HTTP source, bearer filter, Liquibase migration and JDBC repository added; 7 Java tests pass (including offline changelog parse). Python claim/lease/S3 worker source and 3 fake-S3 tests added; pinned psycopg/boto3 imports, pip check and combined 77-test research/worker suite pass. Compose/Dockerfiles added; config parses with throwaway values, images/startup unrun. Docker engine pipe absent after elevated launch; LocalStack token unconfigured. Tasks 2–5 remain open.
- [reproduce-portfolio-learning](changes/reproduce-portfolio-learning/tasks.md): 17/18 tasks complete: tested runner, repeat, evidence and final validation. Historical seed/cost task 4.2 remains open. Do not archive as fully complete.
- [initialize-version-control](changes/initialize-version-control/tasks.md): Claude's Git/LF setup plus verified source-revision continuation. OneDrive relocation choice and publication secret-scanning follow-ups remain open.
- [define-product-and-stack](changes/define-product-and-stack/tasks.md): section 10 UI skill/acceptance plan complete and validated. Broader research/default tasks remain open.
- [setup-tailscale-access](changes/setup-tailscale-access/tasks.md): deferred. Tailscale was disconnected at user request; no Serve endpoint/phone verification. Do not reconnect during local work.

## Completed change
- [add-mobile-client-test-harness](changes/archive/2026-10-10-add-mobile-client-test-harness/implementation.md) was archived 2026-10-10 after five completed tasks. The main [mobile shell spec](specs/mobile-experiment-shell/spec.md) was synced. Expo 57 Android/web synthetic preview, seven passing Jest/RNTL tests, TypeScript, web/Android exports and dark desktop/390×844 web visual review are recorded there. iOS and live API/physical-device checks remain separate.
- [ignore-archive-lock](changes/archive/2026-10-11-ignore-archive-lock/implementation.md) was archived 2026-10-11 after strict validation. The transient archive lock is ignored and its tracked copy removed.
- [add-synthetic-run-contract](changes/archive/2026-10-11-add-synthetic-run-contract/implementation.md) was archived 2026-10-11 with three requirements synced to the main [synthetic run spec](specs/synthetic-run-contract/spec.md). The Python local adapter and CLI passed 15 targeted tests, 74 full research tests, and a separate one-epoch CLI smoke. Corrected a generated Purpose placeholder; final strict spec validation passed 3/3, all OpenSpec 7/7, and diff check passed. It is not an API, durable worker or v2 replay verifier.

## Environment and boundaries
- Python 3.12.14, CPU PyTorch 2.8.0+cpu, NumPy 2.2.6, psutil 7.0.0, filelock 3.32.6; dependency checks passed. Use unique workspace-local pytest temporary directories and disable its cache to avoid prior permission failures.
- Earlier host checks: Java 21 installed but old patch, PATH Java 24; Docker installed but engine unavailable. Node 22.23.2 was installed via nvm on 2026-10-09, but new shells still select 22.12.0; prefix the newer binary directory for Expo commands. npm audit with dev packages omitted reported 12 moderate/23 high advisories; triage before network exposure/publication. LocalStack token/persistence and complete dependency locks remain unverified.
- No paid services, public deployment, broker integration or public license selected. No provenance-validated historical dataset located; synthetic data enables app development while that study stays open.

## Next concrete step
Lock the service environment and implement the first Spring/PostgreSQL/Python/LocalStack synthetic Compose slice using the bounded request contract. Verify Java/Python canonical hash agreement and publish the HTTP/job schemas before connecting client submission/status/results. Preserve the v2 replay, later research/app/K3s and phone-access requirements; record evidence after each logical change.
