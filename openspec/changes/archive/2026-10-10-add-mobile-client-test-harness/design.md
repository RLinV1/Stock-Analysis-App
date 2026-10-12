## Context

The approved client is Expo/React Native/TypeScript. The user clarified that this change should implement Android and web now; iOS is a later port. `docs/UI-DESIGN.md` sets the eventual full-flow acceptance matrix. The current host has Node 22.12.0 while current Expo SDK 57 requires Node 22.13.x or newer. No API or client exists.

## Decisions

1. Use an Expo SDK-compatible blank TypeScript app, native React Native controls, and Jest with `jest-expo` plus React Native Testing Library. Pin versions with a lockfile and verify on a supported Node LTS runtime.
2. Start with the four named surfaces: Experiments, New experiment, Experiment detail, Results. Share the TypeScript screens across Android and web, while using native platform controls. Use one small synthetic fixture to let the user inspect the intended presentation. Show a prominent demo badge and research-only notice on results.
3. The default app has no configured API and therefore disables submit/cancel. It never manufactures a job ID, completion state, or live metric. A service boundary, network-backed behavior and persistence wait for the API change.
4. Test user-visible outcomes, navigation, accessible action names, validation and offline safety rather than snapshots of implementation markup. Avoid custom gesture/motion primitives in this first slice.

## Risks and tradeoffs

- Host Node upgrade and package fetch may fail; record exact unrun checks if so.
- Component tests are not physical Android, browser accessibility or live API tests. Keep those marked open in `docs/UI-DESIGN.md`. iOS compatibility remains a later port and will need a separate build/device path.
- The demo is deliberately not a usable experiment service. It establishes an honest UI and a test seam for later integration.
