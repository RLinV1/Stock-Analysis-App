# Implementation record

## Classical mean-variance comparison - 2026-10-21

Added `research/src/portfolio_lab/classical.py` (`max_sharpe_long_only`, `mean_variance_weights`, `compare_run`), the `compare RUN --output FILE` CLI command and `research/tests/test_classical.py`. Installed `scipy==1.16.2` into the project .venv at the user's request (NumPy stayed 2.2.6; `pip check` clean) and pinned it in `research/requirements-cpu.txt` for tests. The code was written and tested in a scratch copy of the package while tier1-paper trained, because every fold re-checks a fingerprint of the package's `.py` files and adding a file mid-run would fail the next fold.

Verification: `tests/test_classical.py` 7/7 (hand-calculated tangency weights, negative-mean exclusion, all-negative fallback, brute-force grid, SciPy SLSQP cross-check on 25 random four-asset cases, prior-data-only causality, end-to-end compare with exact recomputation and exclusive output). Full research suite 706/706 on this branch. `compare` ran on all four Yahoo runs; each time the recomputed LSTM, equal-weight and 60/40 metrics matched the run report exactly. Results are in docs/RESULTS.md.

Limitations: raw textbook MV (no shrinkage, no risk-free rate, long-only by choice); the paper's other classical baselines (four annually rebalanced allocations, maximum diversification, DWP) are not implemented.
