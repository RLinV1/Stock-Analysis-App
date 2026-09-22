## Why
The user wants another AI agent to be able to continue the project using consistently updated repository documentation rather than prior chat history.

## What Changes
- Add a concise handoff document with current status and unresolved decisions.
- Require agents to read project context at session start and reconcile documentation after changes and before handoff.
- Explicitly separate accepted decisions from suggestions and record unfinished work and verification limitations.

## Capabilities
### New Capabilities
None.
### Modified Capabilities
- `change-documentation`: Maintain sufficient current context for another agent to resume work.

## Impact
Documentation only: AGENTS.md, openspec/HANDOFF.md, and the change-documentation specification. No application behavior changes.
