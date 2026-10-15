## Why

The project has no version control. Independent review on 2026-09-21 recorded this under required next steps, and `docs/REPRODUCTION.md` already documents a workaround: "Content fingerprints capture the numerical source files, not just a git commit, since this directory was not a git repository at initial implementation."

This is a direct contradiction of the project's stated purpose. The planned run manifest binds a result to the code that produced it; without a commit there is no stable source identity to bind to, only a fingerprint of whatever files happened to be on disk. Every further day of implementation is a day of unrecoverable history.

The A0 milestone does not require version control to proceed, but reproducibility claims do, and the cost of establishing it now is minutes.

## What Changes

- Initialize a Git repository at the project root.
- Replace the minimal `.gitignore` with one covering Python artifacts, vendor data snapshots, model/checkpoint binaries, secrets, and the JVM and Node trees that later milestones introduce.
- Configure repository-local commit identity. Global Git configuration is not modified.
- Record an initial commit capturing the existing documentation, OpenSpec artifacts, and Python research package.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `portfolio-research`: source identity for a recorded run becomes a Git commit plus working-tree cleanliness, rather than a file fingerprint alone.

## Impact

No numerical behavior changes. No dependency is installed, upgraded, or removed. No file outside `.gitignore` is modified, moved, or deleted. The Python package and its 17 passing tests are untouched.

The initial implementation excluded pre-commit scanning. The 2026-10-14 continuation adds a repository-owned staged-content hook and stdlib full-history scan as local safeguards. A dedicated publication scanner, CI controls, restricted-data review and licensing remain publication prerequisites.

## Publication safeguards continuation — 2026-10-14

Extend the existing scanner with an explicit history mode covering objects reachable from every local reference, HEAD and reflogs, including removed content, commit/tag messages and sensitive historical filenames. Reject shallow repositories rather than imply a full scan. Output must contain identifiers, rules and line numbers, never matched values or Git diagnostics. Preserve staged mode as the default and the existing detector/allowlist/size/binary limitations. Provide and test a repo-local pre-commit hook; installation is a separate local configuration step after review. No remote, history rewrite, publication, relocation or service startup is included.

## Verification performed before proposing

- Candidate tree measured at 547K excluding `.venv`; no files over 1MB, and no `.pt`, `.onnx`, `.csv` or `.parquet` files present.
- Pattern scan for credentials, keys and tokens across the tree excluding `.venv` returned only documentation discussing such material; no secret values found. No `.env` file exists anywhere in the tree.
- `runs/` contains two local test-run directories and is ignored.

## Confirmed Scope and Proposed Defaults

Confirmed: the user directed this work after being shown the absent-version-control finding and the OneDrive risk.

Proposed default: repository-local commit identity taken from the name and address already present in the project owner's own résumé and session context, so no new personal data is introduced.

**Deliberately excluded and still open — the relocation question.** The project sits under a synchronised OneDrive path. OneDrive and Git interact badly (sync locks, conflict copies of `.git` internals), and a symptom may already be visible: the verification test run emitted `WinError 5: Access is denied` while creating `.pytest_cache`. Relocation is **not** performed by this change because moving the tree invalidates the absolute paths baked into `.venv`, requiring the environment to be rebuilt, and would change the working directory of the active session. Options are recorded in the design document for a separate decision.
