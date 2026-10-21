"""Classical mean-variance baseline evaluated on a finished walk-forward run.

The paper's MV baseline: 50-day moving estimates of mean returns and covariance,
updated daily, with Sharpe-maximizing long-only weights. It needs no training,
so it is computed afterwards on exactly the run's test dates and accounting.
"""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np

from .data import load_dataset
from .json_io import load_json_object
from .walk_forward import _allocations, continuous_results


def max_sharpe_long_only(mean: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Exact long-only maximum-Sharpe weights summing to one.

    The optimum's nonzero weights equal the unconstrained tangency solution on
    that subset, so checking every subset is exact for a handful of assets.
    Single assets are always candidates, so a valid portfolio always exists
    unless every asset has zero volatility.
    """
    count = len(mean)
    best, best_sharpe = None, -np.inf
    for size in range(1, count + 1):
        for subset in combinations(range(count), size):
            index = list(subset)
            if size == 1:
                raw = np.ones(1)
            else:
                try:
                    raw = np.linalg.solve(cov[np.ix_(index, index)], mean[index])
                except np.linalg.LinAlgError:
                    continue
                if np.any(raw <= 0):
                    continue
            weights = np.zeros(count)
            weights[index] = raw / raw.sum()
            variance = weights @ cov @ weights
            if variance <= 1e-18:
                continue
            sharpe = weights @ mean / np.sqrt(variance)
            if sharpe > best_sharpe:
                best, best_sharpe = weights, sharpe
    if best is None:
        raise ValueError("No asset has nonzero volatility in the estimation window")
    return best


def mean_variance_weights(prices: np.ndarray, targets: np.ndarray, window: int = 50) -> np.ndarray:
    """Weights for each target row, estimated only from the `window` returns before it."""
    if window < 2 or np.min(targets) - window < 1:
        raise ValueError("Each target needs a full estimation window of prior returns")
    returns = prices[1:] / prices[:-1] - 1  # returns[k - 1] is the return into row k
    result = []
    for target in targets:
        history = returns[target - 1 - window:target - 1]
        result.append(max_sharpe_long_only(history.mean(axis=0), np.cov(history, rowvar=False)))
    return np.array(result)


def compare_run(run_dir: Path, output: Path, *, window: int = 50) -> Path:
    """Add the mean-variance baseline to a completed walk-forward run's results."""
    run_dir = Path(run_dir)
    report = load_json_object(run_dir / "report.json")
    dataset = load_dataset(run_dir / "dataset" / "manifest.json")
    dates = report["test_dates"]
    positions = {day: index for index, day in enumerate(dataset.dates.tolist())}
    targets = np.array([positions[day] for day in dates])
    # Same arithmetic and float32 targets as the walk-forward evaluator.
    returns = (dataset.prices[targets] / dataset.prices[targets - 1] - 1).astype(np.float32)
    recorded = _allocations(run_dir, dataset.symbols, dates, list(report["strategies"]))
    weights = {**recorded, "mean_variance": mean_variance_weights(dataset.prices, targets, window)}
    results = continuous_results(weights, returns, report["cost_bps"])
    for name in recorded:
        if (json.dumps(results[name]["metrics"], sort_keys=True)
                != json.dumps(report["strategies"][name]["metrics"], sort_keys=True)):
            raise ValueError(f"Recomputed {name} accounting differs from the run report")
    summary = {
        "run_id": report["run_id"], "test_start": dates[0], "test_end": dates[-1],
        "cost_bps": report["cost_bps"],
        "mean_variance": f"Long-only maximum Sharpe from the previous {window} daily returns, re-estimated daily",
        "strategies": {name: result["metrics"] for name, result in results.items()},
    }
    output = Path(output)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    return output
