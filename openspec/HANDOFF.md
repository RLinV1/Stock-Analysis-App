# Project handoff

Updated 2026-10-15. Read actual source, Git status and active change records before editing.

## Confirmed direction and boundaries

- Build a small synthetic vertical slice for Deep Learning for Portfolio Optimization and an Android/web experiment lab. [DESIGN](../DESIGN.md) is the roadmap; [SPEC](../docs/SPEC.md) is the planned technical contract. Never describe planned work as implemented.
- Stack: Expo/React Native/TypeScript, Java 21/Spring Boot, Python/PyTorch, PostgreSQL/Liquibase, LocalStack, standalone Compose first and additional K3s later. Physical Android phone; PC hosts computation; initially one CPU run. iOS later.
- User authorized Docker Desktop/app startup and Playwright checks on 2026-10-15, then explicitly said “just don't check localstack”. No LocalStack/S3 check or token setup is included. Full publication/Compose acceptance stays open. Tailscale remains disconnected; phone/private HTTPS is deferred. Do not reconnect it.
- Earlier user instructions persist: concise replies, no confirmation for authorized work, frequent local Conventional Commits, no remote/push. Existing branch is `feat/synthetic-service-slice`; `main` remains eab38cc. Prior user requested subagents; this continuation used no new agents.
- Apply [UI-DESIGN](../docs/UI-DESIGN.md) and preserved [apple-design](../docs/reference/apple-design.md), retaining native Android behavior and honest synthetic/experiment states. Broad Android cleartext permission is not an accepted decision. Existing local stack/BackHandler differs from mobile/AGENTS.md's Expo Router instruction; discrepancy is recorded in the client design, migration remains unresolved.
- Historical data rights/provenance, proposed numeric defaults, paper rebalancing interpretation and publication/license choices remain open. A Transformer comparison is proposed later work, not a replacement for the LSTM baseline.

## Latest verified state

- **Java 76/76**, zero failures/errors/skips, full package in 46.116 s: 14 repository PostgreSQL cases, eight CORS cases and actual Boot-context fresh migration/reopen/transaction rollback. Replaced bare liquibase-core with Boot 4's Liquibase starter; prior manually constructed migrations masked missing auto-configuration. Packaged API also automatically applied both migrations on fresh smoke PostgreSQL.
- **Research/worker 194/194**, zero skips, 64.26 s: 111 research, 43 worker unit/actual-child tests and 40 PostgreSQL cases. SQL includes lease/token expiry, rollback, cancellation/publication and competing-lock expiry guards. Supervised training has a two-hour deadline, bounded stop/reap and independently renewed ownership. Retained stopped checkpoints do not yet implement durable service resume. [Service implementation](changes/build-synthetic-service-slice/implementation.md) contains exact evidence and limitations.
- **Mobile 91/91**, TypeScript/lint clean; Android Hermes/web exports pass. Current continuation reran lint/TypeScript after tightening the live smoke. Bounded light/dark, 390-pixel, browser doubled-text/keyboard and fixture Results/error review passes; these are separate from native Android/TalkBack.
- **Real browser/API/PostgreSQL smoke passes**: authenticated connect/list, synthetic POST 202, explicit GET 200/QUEUED with matching run ID, queued cancellation to CANCELLED and refreshed list; no page errors. Opt-in exact-origin CORS preserves actual bearer auth and defaults disabled. [JSON/screenshots and repeat instructions](../docs/evidence/mobile-web-2026-10-15/README.md) distinguish real mutations from mocked completed Results. No worker training or artifact endpoint was called in the live smoke.
- Verified service/worker changes are committed locally as `8682938`; client/accessibility/browser evidence as `6db3bbb`. Final documentation reconciliation follows in a separate local commit. No remote or push.
- First browser attempt failed when Docker Desktop exited; restarted it and restored disposable PostgreSQL before the passing retry. Stopped this task's API, Expo server and disposable PostgreSQL afterward; Docker Desktop and unrelated containers are left alone. Removed the generated database password; preserved the pre-existing ignored operator credential file.
- Secret safeguards previously passed 121/121, actual pre-commit hook and history scan; `.githooks` is configured locally, mode 100755. Four exact reviewed mocked-token history exclusions remain documented. Current tracked/new-source scans pass; strict OpenSpec passes10/10; 108 Markdown files have zero broken local links/anchors. Final staged scans run through the installed pre-commit hook.
- Retained [A0 evidence](../docs/A0-EVIDENCE.md): synthetic repeat/resume zero maximum absolute difference; 420 rows, three epochs, lookback50/hidden64, seed7/cost1bps; 5.899 s reference call, narrower training/evaluation0.421 s and maximum sampled RSS284.81 MiB. Not historical evidence, a continuous peak, current-source replay or a performance benchmark. Retained runs contain prior dirty-source metadata; no full external v2 replay exists.

## Active changes and remaining gates

- [build-synthetic-service-slice](changes/build-synthetic-service-slice/tasks.md): schema, repository, paginated list, worker SQL, supervised child and CORS/startup corrections verified in stated scopes. LocalStack/S3 routes/publication, graceful service/recovery behavior under Compose, images and full submit-to-result/restart checks remain. User excluded LocalStack; keep those gates open and do not archive.
- [connect-preview-to-service](changes/connect-preview-to-service/tasks.md): real bounded browser smoke and fixture Results review complete. Android transport decision, physical-phone/live completed-result acceptance and final archive remain open; no client completion claim.
- [reproduce-portfolio-learning](changes/reproduce-portfolio-learning/tasks.md): 17/18 complete; historical seed/cost task4.2 open. Retain synthetic-only evidence.
- [define-product-and-stack](changes/define-product-and-stack/tasks.md): section11 coverage reconciliation complete; broader A1/default/data/replay requirements remain. Coverage inventory now distinguishes passed database/browser gates from unverified storage/deployment/device work.
- [initialize-version-control](changes/initialize-version-control/tasks.md): local staged/current/history scanner and real hooks verified. Publication CI, independent scanning and OneDrive relocation remain open.
- [setup-tailscale-access](changes/setup-tailscale-access/tasks.md): deferred, disconnected, no Serve endpoint/phone check.
- Archived [walk-forward protocol](changes/archive/2026-10-15-add-walk-forward-protocol/implementation.md): causal expanding24-month planner/sample adapter and explicit single-target opt-in. Default A0 fixed holdout preserved; full per-fold training/historical studies remain A1. Earlier client/contract archives are in changes/archive; do not reopen them without a new scoped change.

## Environment and verification notes

- Python3.12.14, PyTorch2.8.0+cpu, NumPy2.2.6, psutil7.0.0/filelock3.32.6; root `.venv`. Use external unique TMP/TEMP/pytest basetemp and disable cache: OneDrive can lock os.replace. PostgreSQL tests create/drop their own isolated schema.
- JDK21.0.2 is explicitly selected; shell PATH may use Java24. Maven3.9.10 runs via its Java/classworlds entry point, workspace-local `.maven-repo`/`.maven-tmp`; wrapper was denied in sandbox. Local networking/Docker checks require approved execution outside network isolation.
- Node22.23.2 is explicitly selected from nvm; fresh shells may use22.12.0. Expo57.0.27, React Native0.86.3. Bundled Playwright1.62.1 and installed Chrome155.0.8059.79. No Playwright runtime dependency added to mobile.
- ESLint/config are pinned development dependencies; mobile runtime package versions unchanged. Existing npm tooling advisory exceptions are in the archived triage change; recheck before exposure/publication or Expo upgrade. Complete transitive locks, container builds and GPU checks remain open.

## Next concrete step

Continue independently testable image/startup/recovery or A1 work within a scoped OpenSpec change. Full Compose/S3 remains unverified while LocalStack is skipped; physical Android/private transport stays deferred. The verified source/evidence is integrated into local commits. Do not mark active changes complete or archive them while their required gates remain.
