## Why

The user asked for the README to open with a high-level explanation of how the model works, how it differs from the usual way portfolios are built, how it will be trained and with what, and why the project exists. They also asked to remove the status ("current state") text and to move the run instructions out of the README into the run guide.

## What Changes

- Replace the README's status paragraphs with plain-language sections: how portfolios are normally built, how this model works, how it will be trained and what it uses, and why the project exists. Planned work is worded as planned.
- Move the synthetic run/repeat/resume/request commands from the README into docs/RUNNING.md, adding macOS/Linux equivalents, and leave a link in the README.
- Remove the stale "uncommitted/unverified source" status sections from the README; the handoff and linked docs keep that status.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Documentation only.

## Impact

README.md, docs/RUNNING.md and this change record. Stacked on `feat/yahoo-data-2026` because docs/RUNNING.md and docs/HISTORICAL-DATA.md exist only there.
