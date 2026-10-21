"""Unrun local objective-window control/compatibility gates, not study results."""

import json
import math
import shutil
from dataclasses import replace

import pytest
import torch

from portfolio_lab import runner
from portfolio_lab.data import load_dataset, synthetic_dataset
from portfolio_lab.model import (OBJECTIVE_CONVENTIONS, SHARPE_VARIANCE_EPSILON,
                                 negative_sharpe, objective_conventions)
from portfolio_lab.protocol import plan_walk_forward
from portfolio_lab.repeat import repeat_experiment
from portfolio_lab.runner import RunConfig, run_experiment


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_fixed_weight_minibatch_mean_differs_from_full_window_by_hand():
    weights = torch.tensor([[1.0, 0.0]] * 4, dtype=torch.float64)
    returns = torch.tensor([[0.01, 0.0], [0.03, 0.0], [-0.01, 0.0], [0.01, 0.0]], dtype=torch.float64)
    first = float(negative_sharpe(weights[:2], returns[:2]))
    second = float(negative_sharpe(weights[2:], returns[2:]))
    full = float(negative_sharpe(weights, returns))
    assert first == pytest.approx(-0.02 / math.sqrt(0.0001 + SHARPE_VARIANCE_EPSILON), rel=0, abs=1e-12)
    assert second == pytest.approx(0, rel=0, abs=1e-12)
    assert full == pytest.approx(-0.01 / math.sqrt(0.0002 + SHARPE_VARIANCE_EPSILON), rel=0, abs=1e-12)
    assert (first + second) / 2 != pytest.approx(full)
    # This is arithmetic at fixed weights; actual minibatch training also updates
    # parameters between batches, so it is not an isolated batch-size experiment.


def test_default_objective_metadata_is_unchanged_and_independently_copied():
    default = objective_conventions("minibatch")
    assert default == OBJECTIVE_CONVENTIONS
    alternate = objective_conventions("full-training")
    assert alternate["training_scope"] == "all training targets; one optimizer update per epoch"
    assert {key: value for key, value in alternate.items() if key != "training_scope"} == {
        key: value for key, value in default.items() if key != "training_scope"}
    alternate["transaction_costs"] = "edited test value"
    assert OBJECTIVE_CONVENTIONS["transaction_costs"] == "evaluation_only"


@pytest.mark.parametrize("window", [None, True, 1, [], {}, "full", "MINIBATCH", "", "minibatch "])
def test_invalid_window_rejects_before_data_device_or_training(tmp_path, monkeypatch, window):
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid objective window must reject before runtime access")
    monkeypatch.setattr(runner, "load_dataset", forbidden)
    monkeypatch.setattr(runner, "_train", forbidden)
    monkeypatch.setattr(runner.torch.cuda, "is_available", forbidden)
    config = RunConfig("2020-01-01", "2020-02-01", objective_window=window, device="cuda")
    with pytest.raises(ValueError, match="objective_window"):
        run_experiment(tmp_path / "missing.json", config, tmp_path / "runs")
    assert not (tmp_path / "runs").exists()


@pytest.mark.parametrize("control", ["raw", "full-training"])
@pytest.mark.parametrize("field,value", [
    ("epochs", True), ("epochs", 1.5), ("batch_size", 32.0), ("hidden_size", False),
    ("seed", 7.0), ("learning_rate", True), ("learning_rate", 10**400),
    ("cost_bps", True), ("cost_bps", float("inf")), ("device", []),
])
def test_alternate_control_strict_settings_precede_runtime(tmp_path, monkeypatch, control, field, value):
    def forbidden(*args, **kwargs):
        pytest.fail("Malformed diagnostic settings must reject before runtime access")
    monkeypatch.setattr(runner, "load_dataset", forbidden)
    monkeypatch.setattr(runner, "_train", forbidden)
    monkeypatch.setattr(runner.torch.cuda, "is_available", forbidden)
    config = RunConfig("2020-01-01", "2020-02-01", device="cuda",
                       normalization="raw" if control == "raw" else "train-only",
                       objective_window="full-training" if control == "full-training" else "minibatch")
    config = replace(config, **{field: value})
    with pytest.raises(ValueError, match=field):
        run_experiment(tmp_path / "missing.json", config, tmp_path / "runs")
    assert not (tmp_path / "runs").exists()


def test_full_training_direct_fold_rejects_before_runtime(tmp_path, monkeypatch):
    manifest = synthetic_dataset(tmp_path / "data", observations=420)
    dataset = load_dataset(manifest)
    fold = plan_walk_forward(dataset.dates, str(dataset.dates[330]), str(dataset.dates[334]), lookback=10).folds[0]
    config = RunConfig(fold.train_end, fold.validation_end, lookback=10,
                       objective_window="full-training", device="cuda")
    def forbidden(*args, **kwargs):
        pytest.fail("Alternate fold window must reject before runtime access")
    monkeypatch.setattr(runner, "load_dataset", forbidden)
    monkeypatch.setattr(runner, "_train", forbidden)
    monkeypatch.setattr(runner.torch.cuda, "is_available", forbidden)
    with pytest.raises(ValueError, match="fixed-holdout"):
        run_experiment(manifest, config, tmp_path / "runs", fold=fold)
    assert not (tmp_path / "runs").exists()


@pytest.fixture(scope="module", params=["train-only", "raw"])
def references(tmp_path_factory, request):
    directory = tmp_path_factory.mktemp("objective-window-" + request.param)
    manifest = synthetic_dataset(directory / "data", observations=140)
    dataset = load_dataset(manifest)
    common = RunConfig(str(dataset.dates[90]), str(dataset.dates[110]), lookback=10,
                       hidden_size=4, epochs=2, batch_size=128, learning_rate=0.001,
                       seed=19, cost_bps=1, device="cpu", normalization=request.param,
                       objective_window="minibatch")
    minibatch = run_experiment(manifest, common, directory / "runs")
    config = replace(common, objective_window="full-training")
    full = run_experiment(manifest, config, directory / "runs")
    paused = run_experiment(manifest, config, directory / "runs", stop_after_epochs=1)
    return manifest, config, minibatch, full, paused


def test_one_batch_controls_have_identical_numerics_with_declared_different_scope(references):
    _, config, minibatch, full, _ = references
    reports = [read(path / "report.json") for path in (minibatch, full)]
    assert reports[0]["history"] == reports[1]["history"]
    assert reports[0]["strategies"] == reports[1]["strategies"]
    assert all(entry["optimizer_steps"] == 1 for report in reports for entry in report["history"])
    assert reports[0]["objective"] == OBJECTIVE_CONVENTIONS
    assert reports[1]["objective"] == objective_conventions("full-training")
    models = [torch.load(path / "model.pt", map_location="cpu", weights_only=True) for path in (minibatch, full)]
    for name, tensor in models[0]["model"].items():
        torch.testing.assert_close(tensor, models[1]["model"][name], rtol=0, atol=0)
    retained = read(full / "manifest.json")
    assert retained["config"]["objective_window"] == models[1]["config"]["objective_window"] == "full-training"
    assert retained["config"]["normalization"] == config.normalization
    assert retained["objective"] == reports[1]["objective"]
    assert any("full training graph" in item for item in retained["deviations"])


def test_full_training_local_repeat_and_epoch_resume(references, tmp_path):
    dataset_path, config, _, full, paused = references
    resumed = tmp_path / "resumed"
    shutil.copytree(paused, resumed)
    manifest_before = (resumed / "manifest.json").read_bytes()
    run_experiment(dataset_path, config, tmp_path / "unused-output", resume=resumed)
    assert (resumed / "manifest.json").read_bytes() == manifest_before
    assert read(resumed / "report.json")["history"] == read(full / "report.json")["history"]
    assert read(resumed / "report.json")["strategies"] == read(full / "report.json")["strategies"]
    comparison = read(repeat_experiment(full, tmp_path / "repeats"))
    assert comparison["outcome"] == "matched"
    assert comparison["mismatch_count"] == 0


def test_changed_window_resume_preserves_paused_evidence(references, tmp_path, monkeypatch):
    dataset_path, config, _, _, paused = references
    before = {name: (paused / name).read_bytes() for name in ("manifest.json", "status.json", "checkpoint.pt")}
    monkeypatch.setattr(runner, "_train", lambda *args, **kwargs: pytest.fail("Changed window must reject"))
    with pytest.raises(ValueError, match="mismatch"):
        run_experiment(dataset_path, replace(config, objective_window="minibatch"),
                       tmp_path / "unused-output", resume=paused)
    assert {name: (paused / name).read_bytes() for name in before} == before
    assert read(paused / "status.json")["state"] == "paused"


def test_actual_training_records_different_update_counts_for_small_batches(tmp_path):
    manifest = synthetic_dataset(tmp_path / "data", observations=140)
    dataset = load_dataset(manifest)
    config = RunConfig(str(dataset.dates[90]), str(dataset.dates[110]), lookback=10,
                       hidden_size=4, epochs=1, batch_size=32, device="cpu", objective_window="minibatch")
    minibatch = run_experiment(manifest, config, tmp_path / "runs")
    full = run_experiment(manifest, replace(config, objective_window="full-training"), tmp_path / "runs")
    assert read(minibatch / "manifest.json")["split_counts"]["train"] == 81
    assert read(minibatch / "report.json")["history"][0]["optimizer_steps"] == 3
    assert read(full / "report.json")["history"][0]["optimizer_steps"] == 1
