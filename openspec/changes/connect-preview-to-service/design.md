## Context

See proposal.md for scope. The authenticated API now exposes measured report, equity-curve and allocations views. Android/web remain the client targets. App startup, Docker and phone access remain deferred by the user. No new client dependency is needed.

## Goals / Non-Goals

Make measured results inspectable with platform controls and explicit synthetic labels. Live-service, physical-device and rendered review are separate acceptance gates; component tests cannot satisfy them. Raw model outputs and historical research remain outside this client slice.

## Decisions

- Read result endpoints through the existing bearer client; validate finite values, ordered calendar dates, unique strategies/assets and long-only weight dimensions/sums. Bind these views to the loaded report's dates, costs and strategy set before display, so incompatible artifacts cannot appear to be a valid comparison.
- Keep independent loading/error/retry states for equity and allocations. Reuse connection-generation and selected-run guards. A missing optional result view must not hide a valid measured report.
- Show one strategy's equity curve at a time, with named strategy controls and numerical per-date values for every strategy. This avoids relying on overlapping colored lines. Native View segments avoid a chart dependency; selectable dates expose allocation weights in original asset order with labelled bars.
- Preserve text scaling, opaque system light/dark surfaces, immediate press feedback and targets of at least 48 logical pixels. Existing Android Back remains authoritative.

## Risks / Trade-offs

- Native chart layout and large text may clip on devices → leave rendered/Android checks open and provide all chart values as text.
- Optional endpoints can fail independently → show named retry controls and never estimate missing values.
- No live service is allowed yet → use realistic contract fixtures and fake-client race tests, explicitly record the limit.

## Migration Plan

Client-only additive methods and UI. No persisted data or dependency migration. Revert the Results component and its calls to roll back.
