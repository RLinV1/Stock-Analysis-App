## Context

`docs/READINESS.md` lists "Establish version control/source snapshots and tested locks before reproducibility claims" as required next work. `docs/REPRODUCTION.md` records a content-fingerprint scheme adopted specifically because no repository existed. The fingerprint is a reasonable fallback, not a substitute: it identifies the bytes of the numerical source files at run time, but carries no history, no authorship, no branch, and no way to recover the state that produced an earlier result.

## Decisions

### Initialize in place; do not relocate in this change

The OneDrive risk is real and was raised before the user authorized this work. It is nonetheless separable, and bundling it here would be the riskier choice:

- Python virtual environments record absolute paths in `pyvenv.cfg` and in the console scripts under `Scripts/`. Moving the tree breaks `.venv`, requiring a rebuild that re-downloads PyTorch.
- The active session's working directory would become invalid mid-change.
- A partially-synced OneDrive folder can move incompletely.

Version control is the urgent, low-risk half. Relocation is the disruptive half and needs its own change, run when the environment can be rebuilt and the session restarted. Establishing history first is also strictly safer: after this change, a botched move is recoverable.

### Repository-local identity only

`git config --global user.name` and `user.email` are unset on this machine. Rather than set a global identity — which would silently apply to every other repository the user creates — identity is set with `--local`, scoped to this repository alone.

### The ignore list is a licensing control, not only hygiene

`docs/FINDING-DATA-SOURCING.md` records that no examined free provider grants redistribution rights for vendor price history. A committed CSV is therefore a licensing problem, not an untidy repository. The ignore list blocks `*.csv`, `*.parquet`, `*.feather`, `data/` and `snapshots/` by default, with negated patterns reserving `data/sample/` and `**/fixtures/` for synthetic fixtures that the project itself generates.

`.gitignore` is not a scanner. It does not stop `git add -f`, and it inspects names rather than content. The secret-scanning requirement in `docs/SECURITY.md` is unaffected by this change and must be satisfied before publication.

### Artifacts and checkpoints stay out

`*.pt`, `*.onnx`, `*.safetensors` and `*.ckpt` are ignored. Model artifacts belong in the artifact store described in `docs/SPEC.md`, addressed by hash, not in Git history where they would bloat the repository permanently and cannot be removed without rewriting it.

## Consequences

### Run provenance continuation — 2026-09-23

Record the commit plus tracked/untracked numerical-source and package-declaration dirtiness. Distinguish unavailable Git/no repository explicitly. Documentation-only edits do not change the numerical identity; descriptive Git metadata is outside its digest. The existing source fingerprint and pinned runtime checks still gate resume/repeat. A dirty tree requires a source snapshot before claiming retrieval from that revision; neither a commit nor a fingerprint substitutes for the later full replay contract.

- `docs/REPRODUCTION.md`'s justification for fingerprint-only source identity becomes historical. The fingerprint may remain as a complement — it captures uncommitted working-tree edits that a commit hash alone would miss — but a commit is now available and should be recorded alongside it.
- A future run manifest can record commit plus cleanliness, enabling the `UNVERIFIABLE` status for dirty-tree runs that `docs/SPEC.md` specifies.
- The relocation decision remains open. Three options, for a separate change:
  1. **Exclude the folder from OneDrive sync** via OneDrive settings, leaving the path unchanged. Lowest disruption; keeps the backup convenience elsewhere in OneDrive while removing sync from this tree. Requires no environment rebuild.
  2. **Move to a non-synced path** such as `C:\dev\portfolio-lab`. Cleanest long-term; requires rebuilding `.venv` and restarting the session.
  3. **Accept the risk** and rely on Git history to recover from any sync corruption. Viable precisely because this change exists, but sync conflicts inside `.git` can still be disruptive.

Option 1 is the recommendation: it removes the actual hazard at the lowest cost.

## Alternatives considered

**Defer until A0 completes.** Rejected. Every day without history is unrecoverable, and A0's deliverables include saved run comparisons whose provenance would be weaker without a commit to cite.

**Set global Git identity.** Rejected as an unnecessary change to machine-wide configuration the user did not ask for.

**Commit `runs/` for provenance.** Rejected. Run outputs are reproducible artifacts belonging in the artifact store; committing them conflates the record of the code with the record of its executions and would grow without bound.
