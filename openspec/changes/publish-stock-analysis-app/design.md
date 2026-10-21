## Decisions

Publish the complete existing app/supporting project to the user-selected empty public repository, preserving all existing commits and the current unverified source documentation. The old main is an ancestor of the current branch, so moving this branch to main preserves its history; no force push or history rewrite is needed. Commit the publication snapshot as Conventional Commits (user instruction 2026-10-21, superseding the pasted "first commit" message) while retaining its ancestors. Skip the pasted `git init` and README append: the repository exists and the README title is already set.

Adopt the explicitly selected official Apache-2.0 code license and keep vendor/data rights separate. Exclude local graph outputs, environments, generated data, checkpoints and portable scanner downloads. Reuse the existing staged/history redacted scanner and pre-commit hook; independently scan with the checksum-verified official Gitleaks release. Add only a pinned read-only secret-check CI workflow, not unrequested application builds or training.

After push, compare the remote main commit with local HEAD and check CI. Preserve source-only research task status; publication is not compatibility or reproduction evidence. Stop rather than overwrite unexpected remote history.
