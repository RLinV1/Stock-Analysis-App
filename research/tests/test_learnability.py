"""Frozen synthetic learnability gates; source only, not executed at authoring.

This intentionally easy constant-return signal checks the local pipeline. It is
not a market forecast, historical experiment, or proposed research default.
"""

import csv
import json
import math
from datetime import date, timedelta

import numpy as np
import pytest
import torch

from portfolio_lab.data import load_dataset, write_dataset
from portfolio_lab.model import SHARPE_VARIANCE_EPSILON, negative_sharpe
from portfolio_lab.runner import RunConfig, run_experiment


PREFERRED_RETURN = 0.002
OTHER_RETURN = -0.001
OBSERVATIONS = 120
MIN_MEAN_PREFERRED_WEIGHT = 0.95
MAX_BEST_VALIDATION_LOSS = -18.0


def controlled_dataset(directory, preferred):
    """Write a test-owned calendar-day fixture, disclosing CSV rounding."""
    daily = np.full(2, OTHER_RETURN, dtype=np.float64)
    daily[preferred] = PREFERRED_RETURN
    prices = 100 * np.power(1 + daily, np.arange(OBSERVATIONS)[:, None])
    dates = [(date(2020, 1, 1) + timedelta(days=index)).isoformat()
             for index in range(OBSERVATIONS)]
    return write_dataset(
        directory, dates, prices,
        [{"symbol": "CONTROL_A", "role": "other"}, {"symbol": "CONTROL_B", "role": "other"}],
        kind="synthetic", source="Project-generated constant-return learnability control",
        license_note="Project-generated fixture; no market data or external license",
        adjustment="None; artificial price paths",
        deviations=[
            "Deliberately easy two-asset signal; not paper data or predictive research",
            "Synthetic calendar-day observations, including weekends; not exchange sessions",
            "CSV price formatting approximates ideal constant returns",
            f"Preferred asset column {preferred}; ideal daily return {PREFERRED_RETURN}; other {OTHER_RETURN}",
        ],
    )


@pytest.mark.parametrize("preferred", [0, 1])
def test_controlled_data_and_stabilized_objective_have_declared_optimum(tmp_path, preferred):
    manifest = controlled_dataset(tmp_path / "data", preferred)
    dataset = load_dataset(manifest)
    ideal = np.full((OBSERVATIONS - 1, 2), OTHER_RETURN, dtype=np.float64)
    ideal[:, preferred] = PREFERRED_RETURN
    observed = dataset.prices[1:] / dataset.prices[:-1] - 1
    np.testing.assert_allclose(observed, ideal, rtol=0, atol=2e-11)
    assert dataset.manifest["kind"] == "synthetic"
    assert dataset.symbols == ["CONTROL_A", "CONTROL_B"]
    assert dataset.manifest["deviations"]
    returns = torch.from_numpy(ideal)
    bound = -PREFERRED_RETURN / math.sqrt(SHARPE_VARIANCE_EPSILON)
    losses = []
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        weights = torch.full_like(returns, 1 - fraction)
        weights[:, preferred] = fraction
        losses.append(float(negative_sharpe(weights, returns)))
    assert all(loss >= bound - 1e-12 for loss in losses)
    assert losses == sorted(losses, reverse=True)
    assert losses[-1] == pytest.approx(bound, rel=0, abs=1e-12)
    varying = torch.zeros_like(returns)
    varying[:, preferred] = torch.linspace(0, 1, len(returns), dtype=torch.float64)
    varying[:, 1 - preferred] = 1 - varying[:, preferred]
    assert float(negative_sharpe(varying, returns)) > bound


@pytest.mark.parametrize("preferred", [0, 1])
def test_actual_cpu_runner_learns_known_allocation_in_both_asset_orders(tmp_path, preferred):
    manifest = controlled_dataset(tmp_path / "data", preferred)
    dataset = load_dataset(manifest)
    # Frozen fixture settings. Do not tune this gate from held-out results.
    config = RunConfig(
        train_end=str(dataset.dates[75]), validation_end=str(dataset.dates[95]),
        lookback=5, hidden_size=8, epochs=64, batch_size=128,
        learning_rate=0.02, seed=19, cost_bps=0, device="cpu", normalization="train-only",
        objective_window="minibatch",
    )
    run = run_experiment(manifest, config, tmp_path / "runs")
    report = json.loads((run / "report.json").read_text(encoding="utf-8"))
    status = json.loads((run / "status.json").read_text(encoding="utf-8"))
    retained = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    assert status["state"] == "completed"
    assert retained["config"]["device"] == "cpu"
    assert retained["config"]["normalization"] == "train-only"
    assert retained["config"]["objective_window"] == "minibatch"
    assert retained["dataset"] == dataset.manifest
    assert report["method_label"] == "synthetic-smoke"
    assert report["objective"]["transaction_costs"] == "evaluation_only"
    assert report["test_dates"] == dataset.dates[96:].tolist()
    assert len(report["history"]) == config.epochs
    selected = min(report["history"], key=lambda entry: entry["validation_loss"])
    assert report["best_validation_epoch"] == selected["epoch"]
    assert selected["validation_loss"] <= MAX_BEST_VALIDATION_LOSS
    with (run / "allocations.csv").open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row["strategy"] == "lstm"]
    assert [row["return_date"] for row in rows] == report["test_dates"]
    weights = np.asarray([[float(row[symbol]) for symbol in dataset.symbols] for row in rows])
    assert np.isfinite(weights).all()
    assert np.all(weights >= 0)
    np.testing.assert_allclose(weights.sum(axis=1), 1, rtol=0, atol=1e-6)
    assert float(weights[:, preferred].mean()) >= MIN_MEAN_PREFERRED_WEIGHT
    results = report["strategies"]
    assert results["lstm"]["metrics"]["observations"] == OBSERVATIONS - 96
    assert (results["lstm"]["metrics"]["cumulative_return"]
            > results["equal_weight"]["metrics"]["cumulative_return"])
    assert (run / "model.pt").is_file()
    assert (run / "checkpoint.pt").is_file()
