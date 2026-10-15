## Why

The mobile preview cannot submit or follow a run, although the API, its contract and a typed client now exist. Connecting them is the first live mobile flow.

## What Changes

- Add an in-app service connection form (base URL and operator token held in memory only) that becomes connected only after a successful run list response.
- When connected: list live runs, submit a validated synthetic request with a per-draft idempotency key, read status on demand, cancel queued or running runs, and list a completed run's artifact files.
- When not connected, keep today's offline preview unchanged.

## Capabilities

### Modified Capabilities

- `mobile-experiment-shell`: live service connection and run flow; the offline behavior and demo labeling stay.

## Impact

2026-10-15 rendered verification continuation: the user explicitly authorized app startup and Playwright testing. Use the bundled Playwright runtime to inspect light/dark, 390-pixel, browser large-text and keyboard behavior, offline and mocked connected result/error states. Retain evidence and a repeatable harness without adding a browser dependency if the bundled runtime suffices. Browser interception is mocked HTTP evidence, separate from the real service and physical Android. Tailscale remains disconnected.

2026-10-15 bounded live browser continuation: when the coordinator's local API/PostgreSQL and exact-origin CORS are ready, exercise authenticated connect/list/submit/status/cancel through the actual browser fetch client. Read the ephemeral credential from an ignored runtime file without logging/persisting it. Do not test LocalStack, artifacts, worker training or real result publication; the user excluded LocalStack.

2026-10-14 continuation: extend Results to the existing equity-curve and allocations routes, with strict client validation, report-context matching, strategy/date controls and independent retry states. This follows the handoff's next step and the planned Results contract. Native charts expose numerical alternatives and preserve declared conventions/asset order.

Client UI, tests, documentation and development lint tooling; runtime dependencies remain unchanged. No persisted credential. Physical-device and real-service checks remain separate from fixtures.

2026-10-14 typography continuation: finish source-level UI refinement with responsive metric/control layouts, text-scaled spacing and explicit assistive-reading states. Existing fixed two-column metrics and minimally padded actions can become cramped with large fonts. Cover narrow/200% text layouts and release-only activation at component level, then run available local checks/static exports without starting the app or services. Reconcile the mobile README's obsolete seven-test/offline-only status with actual source and evidence. Rendered/device acceptance stays open.

2026-10-14 lint scope: add standard Expo-compatible development-only ESLint tooling/configuration because mobile/AGENTS.md and the existing verification task require lint. Check primary registry metadata and installed Expo 57 defaults, pin selected direct versions and retain package-lock integrity. Do not upgrade runtime packages or run Expo's implicit installation/bootstrap path.

Decisions taken without user input (user asked not to be asked): memory-only credentials, manual refresh instead of polling, fixed synthetic dataset/execution values shown on screen (observations 420, seed 2026, hidden size 64, execution seed 7, cost 1 bp).

## 2026-10-13 continuation scope

The user requested Apple-inspired UI improvements and work across the project requirements, with maximum GPT-6 Sol subagents and no process execution. Extend this active client change with a typed completed-report reader, requested-run identity validation, and a Results screen showing only returned metrics, dates, costs and undefined-metric explanations. Refine system typography, neutral light/dark surfaces, spacing and action hierarchy using the preserved Apple guidance while retaining native Android interaction and explicit synthetic labels. No added dependency, persisted token or fabricated result.
