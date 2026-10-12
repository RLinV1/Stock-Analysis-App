## Why

The research runner has tests, but the planned Android experiment flow has no client or executable UI checks. Start implementation with a small Expo shell and tests that verify truthful status, safe offline behavior, and research labeling before service integration.

## What Changes

- Create the approved React Native/Expo/TypeScript client for Android and web now; keep iOS compatibility as later work.
- Add component and state tests for list, draft, detail, and result surfaces using synthetic fixtures and an injected service boundary.
- Keep demo fixtures visibly labeled and prevent them from being mistaken for a live accepted run or historical performance.
- Record automated results and outstanding physical-device/API checks immediately in this change and the handoff.

## Capabilities

### New Capabilities
- `mobile-experiment-shell`: a testable, accessible research UI shell with explicit demo/offline states and no fabricated server outcomes.

## Impact

Adds `mobile/` only. No backend endpoint, database, network exposure, or device connection is introduced. Existing research behavior remains unchanged. Real service submission, durable jobs, Android device checks, and iOS verification remain separate follow-up work.
