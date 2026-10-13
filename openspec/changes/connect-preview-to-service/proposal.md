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

Mobile UI and tests only. No new dependency and no persisted credential. Physical-device and live-service checks remain separate.

Decisions taken without user input (user asked not to be asked): memory-only credentials, manual refresh instead of polling, fixed synthetic dataset/execution values shown on screen (observations 420, seed 2026, hidden size 64, execution seed 7, cost 1 bp).

## 2026-10-13 continuation scope

The user requested Apple-inspired UI improvements and work across the project requirements, with maximum GPT-6 Sol subagents and no process execution. Extend this active client change with a typed completed-report reader, requested-run identity validation, and a Results screen showing only returned metrics, dates, costs and undefined-metric explanations. Refine system typography, neutral light/dark surfaces, spacing and action hierarchy using the preserved Apple guidance while retaining native Android interaction and explicit synthetic labels. No added dependency, persisted token or fabricated result.
