## Context
The project remains in discovery. An older finance design exists, while the user is exploring other domains. A new agent must not mistake suggestions for approved scope.

## Goals / Non-Goals
Goals: maintain accurate context, explicit decision status, and evidence of completed or unfinished work.
Non-goals: choose an app, implement features, or guarantee that an external agent obeys instructions.

## Decisions
Use root AGENTS.md as the entry point and openspec/HANDOFF.md as a concise current-state index. Detailed evidence stays in change implementation records; archived specs describe current requirements. Agents verify repository state when resuming because interrupted sessions can leave stale documentation.

## Risks / Trade-offs
This is an agent workflow requirement, not an automated enforcement mechanism. Prevent duplicate sources of truth by keeping the handoff short and linking to detailed artifacts.
