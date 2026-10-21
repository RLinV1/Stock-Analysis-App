## Source status — 2026-10-17

Sampler/runner controls, explicit service pin/direct-fold guard and regression source are written. No project imports, tests, models, commands or GPU work ran. Keep all tasks unchecked until required implementation and verification are complete.

- [ ] 1.1 Add explicit train-only/raw sampler controls with unchanged default behavior, exact alignment/targets/masks and retained identity transform for raw inputs.
- [ ] 1.2 Bind local fixed-holdout mode to RunConfig identity/artifacts/deviations and strict invalid-mode preflight; preserve evidence on changed-mode resume rejection.
- [ ] 1.3 Pin the service adapter to train-only and reject raw direct folds before data/device/training access; preserve group/sweep config scope.
- [ ] 1.4 Add sampler/default parity, raw causality/overflow, local raw run/repeat/resume and mode rejection source cases; document empirical limitations and update handoff immediately.
- [ ] 2.1 After execution authorization, run targeted and full sampler/A0/service/fold/group/sweep/repeat compatibility. Record all failures and actual outcomes; controls alone do not complete A1's normalization study.
- [ ] 2.2 Validate OpenSpec/docs and archive only after every implementation/verification gate is complete. Do not push.
