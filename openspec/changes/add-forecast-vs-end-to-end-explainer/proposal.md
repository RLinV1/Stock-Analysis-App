## Why

The user asked for the Q&A from this session to be summarized into docs/PAPER-BACKGROUND.md or the README. The session worked through how the classical forecast-then-optimize pipeline operates, why the handoff between its steps is fragile, how the paper's end-to-end network is trained instead, and what that does and does not fix. The existing background doc states the argument in two sentences; a newcomer cannot follow it without this walkthrough.

## What Changes

- Add a plain-language walkthrough subsection to docs/PAPER-BACKGROUND.md section 1: the classical pipeline, a worked two-stock example of forecast sensitivity, how the end-to-end model trains, what it changes and what it does not fix, and what the repo implements.
- Add one link from the README's "How portfolios are normally built" section to that walkthrough.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Documentation only.

## Impact

docs/PAPER-BACKGROUND.md, README.md and this change record. No code, behavior or spec changes.
