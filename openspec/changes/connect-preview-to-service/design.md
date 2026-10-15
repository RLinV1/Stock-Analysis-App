## Context

See proposal.md for scope. The authenticated API now exposes measured report, equity-curve and allocations views. Android/web remain the client targets. On 2026-10-15 the user authorized Docker and app startup/Playwright; LocalStack checks remain explicitly excluded and phone/Tailscale access stays deferred. Runtime client dependencies remain unchanged; pinned development lint tooling is added.

## Goals / Non-Goals

Make measured results inspectable with platform controls and explicit synthetic labels. Live-service, physical-device and rendered review are separate acceptance gates; component tests cannot satisfy them. Raw model outputs and historical research remain outside this client slice.

## Decisions

- Read result endpoints through the existing bearer client; validate finite values, ordered calendar dates, unique strategies/assets and long-only weight dimensions/sums. Bind these views to the loaded report's dates, costs and strategy set before display, so incompatible artifacts cannot appear to be a valid comparison.
- Keep independent loading/error/retry states for equity and allocations. Reuse connection-generation and selected-run guards. A missing optional result view must not hide a valid measured report.
- Show one strategy's equity curve at a time, with named strategy controls and numerical per-date values for every strategy. This avoids relying on overlapping colored lines. Native View segments avoid a chart dependency; selectable dates expose allocation weights in original asset order with labelled bars.
- Preserve text scaling, opaque system light/dark surfaces, immediate press feedback and targets of at least 48 logical pixels. Existing Android Back remains authoritative.
- Typography/accessibility continuation (2026-10-14): use the current window width and font scale to stack metric columns and strategy/date controls on narrow screens or at large text sizes. Scale related spacing without capping native text scaling; give wrapped actions vertical padding, expose disabled/busy states and group metric labels with values for assistive reading. Preserve the existing system-font hierarchy and opaque surfaces.
- Add standard Expo flat ESLint configuration and development dependencies selected from Expo 57's CLI defaults and registry compatibility metadata. Pin direct tool versions, keep runtime dependencies fixed, update the full npm lock and lint source/tests without an automatic setup mutation.
- Keep mocked browser and real API browser checks in separate harnesses. The fixture harness intercepts same-origin synthetic requests; the live harness reads an ignored ephemeral credential and targets opt-in exact-origin CORS for actual connect/list/submit/status/cancel. Never save credentials or treat mocked Results as real worker/artifact validation.

## Risks / Trade-offs

- Native chart layout and large text may clip on devices → leave rendered/Android checks open and provide all chart values as text.
- Optional endpoints can fail independently → show named retry controls and never estimate missing values.
- Real service checks are bounded to API/PostgreSQL → retain fixtures/component race tests for completed Results and label their provenance; LocalStack/artifact publication and phone flow remain open.
- `mobile/AGENTS.md` asks for Expo Router, while the already accepted preview uses a local native stack and BackHandler without that dependency. Record this discrepancy; this bounded typography pass preserves navigation rather than silently adding a router migration. Lint now uses pinned Expo 57-compatible development tooling after the initial non-installing probe showed prerequisites missing.

## Migration Plan

Client-only additive methods and UI, with development lint lockfile updates. No persisted client data or runtime dependency migration. Revert the Results component and its calls to roll back.
