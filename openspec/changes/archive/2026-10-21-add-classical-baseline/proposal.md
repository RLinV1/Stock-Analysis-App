## Why

The user asked for a classical base case to compare against the paper's LSTM. The walk-forward runs only compared against equal-weight and 60/40. The paper's main classical comparison is Markowitz mean-variance (MV), and the project had no MV implementation (SPEC section 9 lists baseline estimators as open).

## What Changes

- Add `portfolio_lab.classical`: an exact long-only maximum-Sharpe solver and a daily mean-variance weight series estimated from the previous 50 daily returns.
- Add a `compare` CLI command that evaluates MV on a finished walk-forward run's exact test dates, returns and cost, recomputes the recorded strategies as a self-check, and writes a new comparison JSON.
- Add tests, including a cross-check against SciPy's optimizer; add `scipy==1.16.2` to the research test requirements (the user asked for SciPy to be installed).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `portfolio-research`: adds the mean-variance comparison requirement.

## Impact

research/src/portfolio_lab (classical.py, cli.py), research/tests/test_classical.py, research/requirements-cpu.txt, docs. Training and existing run outputs are unchanged; the comparison only reads finished runs.
