## 1. Repository initialization

- [x] 1.1 Replace the minimal ignore list with one covering Python artifacts, vendor data, model binaries, secrets, and the JVM/Node trees later milestones add
- [x] 1.2 Initialize the repository and set repository-local commit identity without modifying global Git configuration
- [x] 1.3 Verify the staged file list before committing; confirm no vendor data, model artifact, virtual environment or secret is staged
- [x] 1.4 Record the initial commit

## 2. Verification

- [x] 2.1 Confirm `.venv/`, `runs/` and `__pycache__/` are absent from tracked files
- [x] 2.2 Confirm the Python suite still passes unchanged after initialization
- [x] 2.3 Run strict OpenSpec validation

## 3. Follow-up, not performed here

- [ ] 3.1 Decide the relocation question; OneDrive sync remains active on this tree (design.md records three options)
- [ ] 3.2 Install pre-commit secret scanning before any public publication (`docs/SECURITY.md` requirement, unmet)
- [x] 3.3 Update `docs/REPRODUCTION.md` so source identity cites a commit alongside the content fingerprint
- [x] 3.4 Reconcile `reproduce-portfolio-learning` task status against actual source and test evidence (its own task 4.3)

## 4. Discovered during implementation

- [x] 4.1 Correct `core.autocrlf`, initially set to `true`, which would have made source fingerprints platform-dependent and broken cross-platform replay comparison. Added `.gitattributes` pinning LF in both repository and working tree

## 5. Source revision in run evidence — 2026-09-23 continuation

- [x] 5.1 Record Git commit and dirty state for numerical source/package declarations, with explicit unavailable/no-repository state; keep this descriptive metadata separate from content-based numerical identity.
- [x] 5.2 Test clean, staged/unstaged source changes, untracked source, documentation-only edits, and missing Git/repository; verify run manifests retain revision metadata without claiming dirty source is retrievable from a commit alone.

Scope: implement the existing source-revision spec against Claude's initialized repository. No history rewrite, global Git configuration, remote publication, relocation or OneDrive setting change. Source snapshots/full locks remain later work.
