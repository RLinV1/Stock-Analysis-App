## Why

`npm audit --omit=dev` in `mobile/` reports 12 moderate and 23 high advisories. The handoff required triage before network exposure or publication. Upgrading blindly is unsafe: npm's suggested fixes are downgrades to Expo 44 and React Native 0.84.1.

## What Changes

- Trace every reported advisory to its root package and decide fix, override or accept.
- Record the decision and the recheck trigger in docs and the handoff. No dependency changes unless a safe patched version exists.

## Capabilities

No behavioral capability changes. This is dependency hygiene; `skip_specs: true` applies.

## Impact

Documentation only unless a safe fix exists. The Expo client source and tests are unchanged.
