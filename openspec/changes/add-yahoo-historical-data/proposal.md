## Why

The user wants to test the paper's method on real market data through 2026, and also on the paper's own evaluation window. No acquisition code exists yet: every run so far uses synthetic data. The user selected Yahoo Finance via yfinance as the source and asked for both volatility tiers (raw ^VIX and VIXY), with the reasoning behind every decision written down.

## What Changes

- Add `portfolio_lab.yahoo`, which downloads daily history per ticker, keeps the exact downloaded CSV bytes with SHA-256 hashes, builds a total-return price index per ticker, keeps only dates every ticker traded, and writes a standard historical dataset manifest that the existing loader validates.
- Add a `fetch-yahoo` CLI command for the two SPEC section 8 tiers: tier1 (VTI, AGG, DBC, ^VIX) and tier2 (VTI, AGG, DBC, VIXY).
- Add four explicit walk-forward configs: paper window (test through 2020-04-30) and extended window (test through 2026) for each tier, using the SPEC A0 hyperparameters.
- Add offline unit tests with hand-calculated cases; no test touches the network.
- Add docs/HISTORICAL-DATA.md explaining each decision and how to run it.
- yfinance becomes an optional `data` extra; it is not installed or run by this change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `portfolio-research`: adds historical acquisition requirements.

## Impact

research/src/portfolio_lab (new yahoo.py, cli.py), research/pyproject.toml, research/tests, research/configs, docs, this change. Downloaded data stays under the git-ignored data/ directory and is never committed. The user said not to run the ML model yet, so no training, fetch or walk-forward run happens in this change.
