# Implementation record

## Plain-language comparison - 2026-10-21

Branch `docs/paper-plain-comparison` from main (ad7098c, after PRs #1-#4 merged). Added "In plain terms: the usual approach vs this paper" under section 1 of docs/PAPER-BACKGROUND.md: forecast-then-optimize and how its forecast is graded, the paper's direct portfolio output graded on Sharpe, a weather/clothing analogy, a three-row comparison table, a one-line summary and the trade-off (inspectability, overfitting, costs absent from training). Claims match the existing sections 1, 3, 4 and 6 of the same document.

Verification: `openspec validate add-paper-plain-comparison --strict` passed. Documentation only; nothing was run.
