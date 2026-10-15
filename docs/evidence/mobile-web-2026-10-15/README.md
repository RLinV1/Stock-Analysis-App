# Mobile web evidence — 2026-10-15

Playwright 1.62.1 (Codex bundled runtime), installed Chrome 155.0.8059.79, Windows, Expo 57.0.27/React Native 0.86.3. App served on localhost:8081 after explicit user startup authorization. The Results review below uses intercepted synthetic fixtures; a separate actual API smoke is recorded afterward. No LocalStack/S3 check ran.

[Machine-readable results](results.json) records two browser scenarios: light 1280×844 and dark 390×844. Both passed offline submission-disabled state, lookback validation, keyboard Enter activation, 401 rejection, measured-report 503/retry, independent equity 503/retry while allocations remained available, strategy/date values, control/heading bounds and no page errors. CSS text was doubled on the narrow Results screen and inspected for wrapping. It does not emulate Android `fontScale` or TalkBack.

Screenshots capture the viewport of the native-style scrolling container, not every offscreen row at once. Scroll positions deliberately cover different parts of Results. Inspected report, equity and allocation screenshots: responsive metrics/controls, labels, focus/selection borders, light/dark surfaces and doubled browser text remain legible with no visible horizontal clipping in these views. This is a bounded visual review, not all accessibility/performance/recovery acceptance.

- [Light report](light-desktop-measured-report.png), [light equity](light-desktop-results.png), [light allocations](light-desktop-allocations.png)
- [Dark narrow report](dark-phone-measured-report.png), [dark narrow equity](dark-phone-results.png), [dark narrow allocations](dark-phone-allocations.png)
- [Doubled browser text](dark-phone-large-text.png), [doubled allocation text](dark-phone-large-text-allocations.png)
- [Light offline](light-desktop-offline.png), [dark offline](dark-phone-offline.png), [light report failure](light-desktop-report-error.png), [dark report failure](dark-phone-report-error.png)

Repeat with [browser-check.cjs](../../../mobile/browser-check.cjs); see [mobile README](../../../mobile/README.md). It requires an already authorized running app, Playwright available to Node and installed Chrome. Physical Android, native large-text/TalkBack, motion, keyboard traversal/focus restoration across every flow and release performance remain separate checks.

## Actual API/PostgreSQL smoke

[Live check results](live-results.json) and the [cancelled-state screenshot](real-api-cancelled.png) come from a separate non-intercepted browser run at dark 390×844. The packaged Spring Boot API on localhost:8080 automatically migrated fresh PostgreSQL 17.11. Authenticated connect/list, POST 202, explicit GET status 200 with matching run ID/QUEUED, cancellation to CANCELLED and refreshed list passed with no page errors. The screenshot was visually inspected: wrapped run ID, state and actions remain readable within the narrow viewport. No worker was started; the run stayed queued until cancellation. Completed Results above remain fixture evidence.

Repeat with [browser-live-check.cjs](../../../mobile/browser-live-check.cjs). Supply the token through ignored `.env.runtime-test` in the project root (or `PORTFOLIO_RUNTIME_ENV_PATH` and `PORTFOLIO_RUNTIME_TOKEN_KEY`), configure the API's exact CORS origin and run already-authorized servers. The harness reads the credential without printing it or taking entry screenshots. Evidence excludes LocalStack, S3, worker training, completed-result publication and physical Android. The first attempt failed when Docker Desktop exited; the passing retry followed Docker restart and the Boot Liquibase starter correction.
