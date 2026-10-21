## Why

The first complete run of the research test suite (2026-10-21) failed 5 fold/walk-forward tests. The walk-forward planner validated dataset dates with `isinstance(value, str)`, which `numpy.str_` passes, and returned those NumPy strings unchanged. Fold split dates then reached each fold's saved `model.pt`, and PyTorch's weights-only loader rejects the pickled NumPy global, so every saved fold model failed to load safely.

## What Changes

- `protocol._dates` still validates every date as before, then returns plain Python `str` values. One shared fix covers all planner callers (walk-forward groups and sweeps).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Saved files now contain plain strings; dates, folds and numerical behavior are unchanged.

## Impact

research/src/portfolio_lab/protocol.py. The five previously failing tests act as regression tests.
