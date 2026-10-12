# Implementation record

Planning completed 2026-10-09 before code or package changes. User first added iOS, then clarified to implement Android and web now while leaving iOS for later. No client implementation or checks have run yet. The change targets a truthful synthetic Expo shell and executable UI tests; real API and device verification remain follow-up work.

## Toolchain setup

Installed and selected Node.js 22.23.2 (64-bit) through nvm on 2026-10-09. This clears Expo SDK 57's published 22.13.x minimum. No client packages or tests have run yet.

## Initial client shell

On 2026-10-10, scaffolded Expo 57.0.27 / React Native 0.86.3 / TypeScript with an npm lockfile. Added the Android/web local preview screens in `mobile/src/PortfolioApp.tsx`: Experiments, New experiment, Experiment detail, and Results. Native press controls have named labels and 52-pixel minimum height; Android hardware Back and visible Back are wired. The demo exposes no job ID or measured return, disables submission while no service exists, and labels synthetic content. Results show unavailable model/baseline metrics with reasons and the research-only notice. This is not yet verified by TypeScript, Jest, web render or Android device checks.

## Automated test harness added

Added Expo-compatible web packages, Jest 29, `jest-expo` 57 and React Native Testing Library 14. The new component suite covers synthetic labeling, navigation/back, offline-disabled submission, undefined model/baseline metrics with notice, and invalid draft fields. `mobile/package.json` now exposes test, typecheck and web-export commands and declares Node >=22.13 <23; `mobile/.nvmrc` selects the installed 22.23.2. Fresh shells still resolve old Node 22.12.0 from the existing nvm symlink, so verification commands explicitly prepend the 22.23.2 binary directory. Lockfile reconciliation and all checks are pending; dependency installation reported 59 advisories, which need triage before publication or network exposure.

TypeScript `tsc --noEmit` passed on Node 22.23.2. First Jest attempt failed before loading tests: sandbox Temp denied atomic cache rename (`EPERM`). Redirected Jest cache into ignored `mobile/.jest-cache`; rerun pending. This was an environment failure, not a passing suite.

The next Jest run loaded the suite: 1/7 passed and 6 failed because React Native Testing Library 14 event helpers use asynchronous `act`, while the tests asserted before updates settled. Awaited each event and asserted the host control's accessibility-disabled state; a verification rerun is pending. No production behavior changed for this test correction.

The verification rerun passed all 7 component tests on Node 22.23.2 (`npm test -- --watch=false`, 49.371 s). The four preview screens and behavior tests are complete for this bounded shell. TypeScript passed before the async test fix; final typecheck, Expo dependency check, web export and rendered visual review are pending. These seven checks do not cover a live API, a physical Android device, or the broader planned client-state matrix.

Final typecheck passed. `expo install --check` reported dependencies up to date using its bundled map, with an explicit warning that offline validation is less reliable. Web export passed (199 modules, 379 KB bundle). A localhost render was visually inspected at desktop width and 390×844 dark phone width: Experiments, New experiment, detail and Results showed readable layout, disabled submission and research labels. This is a web visual review, not an Android device result; light theme and browser accessibility remain unreviewed. npm audit with dev packages omitted reported 12 moderate and 23 high advisories, many through Expo tooling; no blind upgrade was applied. Publication or network exposure needs advisory triage.

Android export bundled JavaScript but Hermes failed to write bytecode into the sandbox Temp directory (`permission denied` on `index.hbc`). Added an ignored workspace-local `.expo-tmp/` destination and will rerun with TEMP/TMP pointing there. The Android export is not yet passing.

Android export passed on rerun with TEMP/TMP set to `mobile/.expo-tmp` (581 modules; 1.4 MB Hermes bundle). This verifies packaging of JavaScript for Android, not app launch on a phone. Reconciled README, START-HERE, READINESS, TOOLCHAIN and DESIGN to distinguish this synthetic client shell from the unbuilt API/live app. The current checks for this change are 7/7 component tests, TypeScript, bundled dependency-map check, web export, Android export and web visual inspection. OpenSpec validation and final repository checks remain.

Final checks on 2026-10-10: `openspec validate --all --strict` passed 6/6; `git diff --check` exited 0 (existing line-ending conversion warnings only); `npm ls --depth=0` resolved the pinned direct dependencies; 56 Markdown files had zero missing local links. Current-scope tasks are complete. This does not close live API, device, browser keyboard/TalkBack, light/large-text/motion, or security-advisory checks. npm's production-dependency audit reported 12 moderate and 23 high advisories; release/network exposure remains gated on triage. The full mobile client is not complete.

The OpenSpec archive instruction snapshot exposed an outdated `config.yaml` sentence claiming the preview was untested. Corrected it to the verified seven tests and two exports before syncing/archiving. Actual test evidence controls over stale context text.

The delta's demo scenario had called the synthetic preview a historical research example. Corrected it before sync to match the UI's explicit “not a historical result” label. No runtime behavior changed.

Synced all four added `mobile-experiment-shell` requirements and scenarios into the new main spec under `openspec/specs/`, with a concrete Purpose. `openspec validate --specs --strict` passed 2/2 and the four requirement names match the delta. Archive remains pending.

First archive attempt failed on an existing `.openspec-archive.lock` dated 2026-09-12. Its recorded PID 23228 is not running and the target archive directory does not exist. Remove this stale single-file claim, then retry archive without reapplying the already-synced spec.

Verified the old PID remained absent, removed that stale lock, and archived the completed change as `2026-10-10-add-mobile-client-test-harness` on 2026-10-10. The main spec was synced and validated before archive, so archive skipped duplicate spec updates. All five bounded tasks are complete; broader mobile/service acceptance remains open in the project roadmap.
