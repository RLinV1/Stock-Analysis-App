## What changed

## Integrated verification — 2026-10-09
- Current combined research suite passed 59 tests in 54.22 seconds, including all 10 provenance tests after the ignored-bytecode fix. A0's previously stale implementation checkboxes are reconciled with evidence; task 3.4 is complete.
- Source revision remains descriptive and read-only. Project Git history/configuration, remotes and OneDrive settings are unchanged. Relocation and publication-scanning follow-ups remain open.

## Source identity documentation — 2026-09-23
- Updated REPRODUCTION, README, READINESS and TOOLCHAIN to reflect the actual initialized repository and descriptive source-revision metadata. Documented source scope and the dirty-source/snapshot limitation; historical records below remain intact.
- Task 3.3 complete. Project history/configuration and OneDrive settings are unchanged. Combined source/repeat tests and retained measured evidence are being collected under reproduce-portfolio-learning.

## Source-provenance implementation — 2026-09-23
- Added descriptive source_revision metadata to new A0 manifests, outside the numerical identity digest. It records the current commit and staged/unstaged/untracked (including ignored) source changes within research Python files and package declarations, or an explicit missing-Git/no-repository/no-commit/error state.
- Git inspection is read-only, bounded by subprocess timeouts, and does not expose raw Git error output in manifests. Metadata explicitly states that dirty source requires more than the commit for recovery. Existing source fingerprints and immutable resume manifests are unchanged in behavior.
- Added isolated temporary-repository tests for source/package changes, documentation edits/commits, unavailable Git/repository, Git timeout and actual manifest/resume integration. Tests create commits only in temporary fixtures; no project commit or configuration change is made.
- Verification: the first targeted run hit nine fixture-setup errors because pytest could not access its pre-existing default temporary directory (WinError 5); no test body ran. Retried with a new uniquely named temporary directory, without modifying existing permissions or files: `python -m pytest research/tests/test_provenance.py -q -p no:cacheprovider --tb=short --basetemp <fresh-temp-directory>` passed all 9 tests in 15.92 seconds.
- Tasks 5.1 and 5.2 complete. The integration test retained the original manifest across a resume after a documentation-only commit and produced identical numerical identity with the newer descriptive revision on a new run. Source snapshots, full dependency locks, publication scanning and historical performance remain outside this continuation. Added source bytes change the fingerprint; old checkpoints still require their original source.
- Follow-up live-tree probe caught Git's `--ignored=matching` reporting an ignored __pycache__ directory despite the Python path filter. Switched to `--ignored=traditional` with full untracked enumeration and added a regression distinguishing ignored bytecode from ignored Python source. The absent-repository test now bounds Git discovery with an environment-only ceiling so it also works with a workspace-local temporary root. Task 5.2 reopened pending targeted re-verification.
- Final targeted verification passed all 10 tests in 15.36 seconds using a fresh ignored `runs/provenance-tests-*` temporary root. Live-tree inspection then recorded commit eab38cc573db43c27ed97bc2420580a57b78464d, expected unstaged/untracked source changes, and ignored_source=false despite bytecode caches. Task 5.2 is complete again. No further source changes followed these checks.

## Continuation scope — 2026-09-23
- Inspected actual clean working tree and commits: 602d615 initialization, 957c7d8 LF attributes, and eab38cc implementation record. The prior no-Git handoff is stale.
- Added section 5 before implementation to emit source revision/dirty metadata and test the existing behavioral delta. No new commit, remote, global configuration or relocation performed in this continuation. Implementation checks pending.

Version control established at the project root. Two commits on `main`.

**`602d615` — Initialize repository for Portfolio Lab**
74 files, 4,360 insertions. Captures the Python research package (`model.py`, `runner.py`, `metrics.py`, `data.py`, `cli.py` plus three test modules), the OpenSpec workflow with its archived and active changes, the eleven-document `docs/` set, the seven agent skill files, and the root documents.

**`957c7d8` — Pin line endings to LF for stable source fingerprints**
Adds `.gitattributes`; sets `core.autocrlf` to `false`.

**Files modified**
- `.gitignore` — replaced. Previously eight lines covering Python artifacts, `data/`, `runs/` and `.env`. Now also covers model and checkpoint binaries (`*.pt`, `*.pth`, `*.onnx`, `*.pkl`, `*.safetensors`, `*.ckpt`), tabular vendor data (`*.csv`, `*.parquet`, `*.feather`), additional secret shapes (`*.pem`, `*.key`, `*.p12`, `credentials.json`), and the JVM and Node trees that milestones B and C introduce. Negated patterns reserve `data/sample/**` and `**/fixtures/**` for synthetic fixtures the project generates itself.
- `.gitattributes` — new.

**Configuration** — repository-local only. `user.name`, `user.email`, `core.autocrlf`. Global Git configuration was unset before this change and remains unset.

## A defect found and corrected during the change

`core.autocrlf` was set to `true` during initialization, matching common Windows practice. That was wrong for this project.

With `autocrlf=true`, Git stores LF in the repository but writes CRLF into the working tree on checkout. `docs/REPRODUCTION.md` fingerprints numerical source files as part of run provenance, so identical logical source would have produced different fingerprints on Windows and Linux — silently defeating the cross-platform replay comparison the reproducibility contract depends on. The failure would have surfaced as an unexplained mismatch between two correct runs.

Corrected in `957c7d8`: `core.autocrlf=false`, plus `.gitattributes` normalizing text to LF in both the repository and the working tree, with binary types excluded from conversion.

## Verification performed

| Check | Result |
|---|---|
| Staged-file review before commit | 74 files: 41 `openspec`, 11 `research`, 11 `docs`, 7 `.agents`, 4 root |
| Ignored paths leaking into tracking | 0 — `git ls-files` matches no `.venv`, `__pycache__`, `runs/`, `*.pt`, `*.csv` or `.env` |
| Secret scan before commit | Pattern scan for credentials, keys and tokens across the tree excluding `.venv` returned only documentation *discussing* such material. No `.env` file exists anywhere |
| Tree size | 547K excluding `.venv`; no file over 1MB; no `.pt`, `.onnx`, `.csv` or `.parquet` present |
| Line endings after correction | `git ls-files --eol` reports `i/lf w/lf attr/text=auto eol=lf`; `file` reports ASCII text with no CRLF |
| Python suite after initialization | 17 passed |
| Strict OpenSpec validation | 5 passed, 0 failed |
| Working tree | Clean; 75 tracked files |

## Verification NOT performed

- **No secret-scanning tool was run.** The pre-commit scan was a manual pattern grep, not `gitleaks`, `detect-secrets` or `trufflehog`. The `docs/SECURITY.md` requirement for automated scanning before publication remains unmet.
- No pre-commit hook framework was installed.
- No remote was configured; nothing was pushed anywhere.
- No numerical behavior was exercised beyond re-running the existing suite.

## Limitations and open items

- **OneDrive sync remains active on this tree.** Relocation was deliberately excluded — moving invalidates the absolute paths inside `.venv` and the active session's working directory. `design.md` records three options; excluding the folder from OneDrive sync in place is the recommendation, as it removes the hazard without an environment rebuild. Unresolved.
- `docs/REPRODUCTION.md` still justifies fingerprint-only source identity by the absence of a repository. That justification is now historical and the document needs updating; the spec delta in this change requires a commit identifier to be recorded alongside the fingerprint, and no code yet emits one.
- The spec delta is a requirement, not an implementation. No run currently records a commit identifier or working-tree cleanliness.
- `reproduce-portfolio-learning` reports 2 of 17 tasks complete while working code with 17 passing tests exists. Its own task 4.3 covers reconciling status against actual outputs; still outstanding.
- The `.pytest_cache` `WinError 5: Access is denied` warning observed during verification was not investigated. It may indicate OneDrive or permission interference and is a data point for the relocation decision.
