# Implementation record

## Forecast versus end-to-end walkthrough - 2026-10-21

Branch `docs/forecast-vs-end-to-end-explainer`, from `main`. Added docs/PAPER-BACKGROUND.md section 1.1, a plain-language walkthrough of the classical forecast-then-optimize pipeline on the project's four ETFs, a hand-worked two-stock sensitivity example (81/19 versus 21/79 from a one-point forecast change), the end-to-end training loop step by step, what the end-to-end model changes and does not fix, and what the repo implements. Added one link to it from the README's "How portfolios are normally built" section.

Statements about the code were read from `research/src/portfolio_lab/model.py` and `runner.py`: one-layer LSTM with softmax weights, negative-Sharpe loss on gross returns, Adam updating network parameters, gradient clipping at 1.0, best-validation-epoch selection, costs at evaluation only, and equal-weight and 60/40 baselines only. A grep of `research/src` found no forecast or mean-variance code.

Verification: example arithmetic checked by hand (weights proportional to the inverse-covariance times expected-return vector; both weights positive, so the long-only constraint does not bind). `openspec validate add-forecast-vs-end-to-end-explainer --strict` passed. The README anchor was derived from the heading by the GitHub slug rule and not clicked. No code, tests or model were run.

Limitations: the example figures are illustrative, not project results. The doc makes no claim that the end-to-end model outperforms classical methods; it states that as open.
