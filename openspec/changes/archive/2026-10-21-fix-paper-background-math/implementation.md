# Implementation record

## Summary and LaTeX equations — 2026-10-21

Branched `docs/paper-background-latex` from main (d8c4305). Added a "What this project does" summary to the top of docs/PAPER-BACKGROUND.md, phrased as intended scope and pointing to the README and handoff for implemented status. Rewrote Equations 1-4 and 6-8 as GitHub `math` fences and the inline math (weight constraint, volatility multiplier, population standard deviation, one-step lag, volatility target, cost levels, learning rate) as `$...$`. Table values, findings and the risk list are unchanged.

Verification: `openspec validate fix-paper-background-math --strict` passed. Rendered on GitHub in the built-in browser: the first push showed GitHub rejects `\operatorname` (replaced with `\mathrm`), and `\tag{n}` made display equations stack one symbol per line because Chrome's native MathML cannot lay out labeled rows (replaced with `\qquad (n)` labels). After both fixes there are no math errors and all seven display equations render as single-line blocks 29-59 px tall. Not checked in other Markdown viewers (for example VS Code preview).
