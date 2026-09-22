## 1. Repository initialization

- [ ] 1.1 Replace the minimal ignore list with one covering Python artifacts, vendor data, model binaries, secrets, and the JVM/Node trees later milestones add
- [ ] 1.2 Initialize the repository and set repository-local commit identity without modifying global Git configuration
- [ ] 1.3 Verify the staged file list before committing; confirm no vendor data, model artifact, virtual environment or secret is staged
- [ ] 1.4 Record the initial commit

## 2. Verification

- [ ] 2.1 Confirm `.venv/`, `runs/` and `__pycache__/` are absent from tracked files
- [ ] 2.2 Confirm the Python suite still passes unchanged after initialization
- [ ] 2.3 Run strict OpenSpec validation

## 3. Follow-up, not performed here

- [ ] 3.1 Decide the relocation question; OneDrive sync remains active on this tree (design.md records three options)
- [ ] 3.2 Install pre-commit secret scanning before any public publication (`docs/SECURITY.md` requirement, unmet)
- [ ] 3.3 Update `docs/REPRODUCTION.md` so source identity cites a commit alongside the content fingerprint
- [ ] 3.4 Reconcile `reproduce-portfolio-learning` task status against actual source and test evidence (its own task 4.3)
