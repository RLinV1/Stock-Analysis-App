# Implementation record

Planned on 2026-10-10 before changing the tracked lock or ignore rules. The previous archive completed but left a new PID in the tracked transient lock. Verification is pending.

The lock recorded PID 5184, which was absent when checked. Removed that single stale file and added an exact `.gitignore` rule for `openspec/changes/archive/.openspec-archive.lock`. Git now shows the tracked lock as deleted; `git check-ignore --no-index` resolves the new rule, while the completed mobile archive remains visible as an untracked directory. This prevents future transient PIDs entering commits. Final validation remains.

`openspec validate --all --strict` passed 7/7 with this skip-specs tooling change. `git diff --check` exited 0; existing line-ending warnings are unrelated. Git shows exactly the intended lock deletion and ignore-rule edit for this workflow fix. All three tasks are complete; archive pending.

On 2026-10-11, strict change validation passed and OpenSpec archived the change as `2026-10-11-ignore-archive-lock` with spec sync skipped because this workflow fix has no behavioral delta. Archiving recreated the transient lock at the same path. Removed that exact file again; the ignore rule prevents future archive claims from being staged, while Git retains the intended tracked-file deletion. No runtime product behavior changed.
