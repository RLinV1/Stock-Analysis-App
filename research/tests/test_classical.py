import json
from itertools import product

import numpy as np
import pytest

from portfolio_lab.classical import compare_run, max_sharpe_long_only, mean_variance_weights
from portfolio_lab.data import load_dataset, synthetic_dataset
from portfolio_lab.walk_forward import WalkForwardConfig, run_walk_forward


def sharpe(weights, mean, cov):
    return weights @ mean / np.sqrt(weights @ cov @ weights)


def test_uncorrelated_equal_risk_assets_weight_by_mean():
    # Tangency weights are proportional to cov^-1 mean = mean here: 2:1.
    weights = max_sharpe_long_only(np.array([0.02, 0.01]), np.eye(2) * 0.04)
    np.testing.assert_allclose(weights, [2 / 3, 1 / 3])


def test_negative_mean_asset_is_left_out():
    weights = max_sharpe_long_only(np.array([0.01, -0.02, 0.01]), np.eye(3) * 0.01)
    np.testing.assert_allclose(weights, [0.5, 0.0, 0.5])


def test_matches_brute_force_grid_search():
    rng = np.random.default_rng(3)
    for _ in range(20):
        factors = rng.normal(size=(3, 3))
        cov = factors @ factors.T + np.eye(3) * 0.1
        mean = rng.normal(0.01, 0.02, 3)
        weights = max_sharpe_long_only(mean, cov)
        assert np.all(weights >= 0) and weights.sum() == pytest.approx(1)
        grid = [np.array([a, b, 1 - a - b]) for a, b in product(np.linspace(0, 1, 101), repeat=2) if a + b <= 1]
        assert sharpe(weights, mean, cov) >= max(sharpe(w, mean, cov) for w in grid) - 1e-9


def test_agrees_with_scipy_optimizer_on_four_assets():
    optimize = pytest.importorskip("scipy.optimize")
    rng = np.random.default_rng(11)
    for _ in range(25):
        factors = rng.normal(size=(4, 4))
        cov = factors @ factors.T * 1e-4 + np.eye(4) * 1e-5
        mean = rng.normal(0.0005, 0.001, 4)
        exact = max_sharpe_long_only(mean, cov)
        best = max((optimize.minimize(lambda w: -sharpe(w, mean, cov), start, method="SLSQP",
                                      bounds=[(0, 1)] * 4,
                                      constraints={"type": "eq", "fun": lambda w: w.sum() - 1})
                    for start in np.eye(4) * 0.97 + 0.01), key=lambda result: -result.fun)
        assert sharpe(exact, mean, cov) >= -best.fun - 1e-7


def test_all_negative_means_still_give_valid_weights():
    weights = max_sharpe_long_only(np.array([-0.01, -0.03]), np.diag([0.01, 0.01]))
    np.testing.assert_allclose(weights, [1.0, 0.0])


def test_weights_use_only_prior_returns():
    rng = np.random.default_rng(5)
    prices = 100 * np.cumprod(1 + rng.normal(0.0005, 0.01, (200, 3)), axis=0)
    targets = np.array([120, 150])
    before = mean_variance_weights(prices, targets, window=50)
    changed = prices.copy()
    changed[120:] *= 3  # the target day and later must not matter for target 120
    after = mean_variance_weights(changed, targets, window=50)
    np.testing.assert_array_equal(before[0], after[0])
    with pytest.raises(ValueError, match="full estimation window"):
        mean_variance_weights(prices, np.array([50]), window=50)


def test_compare_run_adds_mean_variance_and_matches_recorded_accounting(tmp_path):
    path = synthetic_dataset(tmp_path / "data", 700)
    data = load_dataset(path)
    config = WalkForwardConfig(str(data.dates[330]), str(data.dates[-1]), lookback=10, hidden_size=8,
                               epochs=1, batch_size=64, learning_rate=0.001, seed=7, cost_bps=1, device="cpu")
    run = run_walk_forward(path, config, tmp_path / "runs")
    output = compare_run(run, tmp_path / "comparison.json")
    summary = json.loads(output.read_text())
    report = json.loads((run / "report.json").read_text())
    assert list(summary["strategies"]) == [*report["strategies"], "mean_variance"]
    for name in report["strategies"]:
        assert summary["strategies"][name] == report["strategies"][name]["metrics"]
    assert summary["strategies"]["mean_variance"]["observations"] == len(report["test_dates"])
    with pytest.raises(FileExistsError):
        compare_run(run, output)
