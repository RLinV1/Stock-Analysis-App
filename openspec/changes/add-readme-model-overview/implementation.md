# Implementation record

## README overview and run-guide move - 2026-10-21

Branch `docs/readme-model-overview`, rebased onto `feat/yahoo-data-2026` so the README can link the run and data guides. The README now opens with what the project tests, how portfolios are normally built (forecast then optimize, or fixed allocations), how the end-to-end LSTM works (inputs, network, softmax long-only weights, Sharpe objective, one-day lag), how training will run (Yahoo data with hashes, Python/PyTorch on CPU, Adam 0.001, batch 64, up to 100 epochs, train-only standardization, two-year walk-forward with 10% validation, paper and 2026 windows with ^VIX and VIXY, shared trading costs, multiple seeds, later phone-submitted jobs) and why the project exists. Every figure comes from docs/PAPER-BACKGROUND.md, docs/SPEC.md section 8 and the run configs.

Removed the README's "Current state" paragraph, the stale "uncommitted research edits" note, the "Experimental walk-forward source" section and the trailing "Explicit research sweep source" section; their status lives in the handoff and the linked WALK-FORWARD and RESEARCH-SWEEPS docs, which stay linked under Read next. Moved the synthetic run/repeat/resume and synthetic-request commands into docs/RUNNING.md with added macOS/Linux shell equivalents.

Verification: `openspec validate add-readme-model-overview --strict` passed; README links checked to exist on this branch. The new macOS/Linux shell commands were not executed, and no model was run.
