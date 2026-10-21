"""Fold execution regressions; written during the code-only continuation.

Future-price injection here isolates fitting from ingestion. Full on-disk
multi-fold mutation/CLI verification remains an additional acceptance gate.
"""

import json
from dataclasses import replace

import numpy as np
import pytest
import torch

from portfolio_lab import runner
from portfolio_lab.data import Dataset, file_hash, load_dataset, synthetic_dataset
from portfolio_lab.protocol import plan_walk_forward
from portfolio_lab.repeat import repeat_experiment
from portfolio_lab.runner import RunConfig, run_experiment


def fixture(tmp_path, *, short=False):
    path = synthetic_dataset(tmp_path / "data", 1000)
    dataset = load_dataset(path)
    start = str(dataset.dates[330])
    end = start if short else str(dataset.dates[-1])
    plan = plan_walk_forward(dataset.dates, start, end, lookback=10)
    fold = plan.folds[0]
    config = RunConfig(fold.train_end, fold.validation_end, lookback=10,
                       hidden_size=8, epochs=1, batch_size=32, seed=7, cost_bps=1)
    return path, dataset, fold, config


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_fold_run_retains_bounded_dates_frozen_model_scaler_and_protocol(tmp_path):
    path, dataset, fold, config = fixture(tmp_path)
    run = run_experiment(path, config, tmp_path / "runs", fold=fold)
    manifest, report = read(run / "manifest.json"), read(run / "report.json")
    assert manifest["evaluation_protocol"]["kind"] == "expanding-walk-forward-fold"
    assert manifest["evaluation_protocol"]["fold"]["number"] == fold.number
    assert report["test_dates"] == dataset.dates[list(fold.test_indices)].tolist()
    assert manifest["split_counts"]["train"] == len(fold.train_indices)
    assert manifest["split_counts"]["validation"] == len(fold.validation_indices)
    assert manifest["split_counts"]["test"] == len(fold.test_indices)
    saved = torch.load(run / "model.pt", weights_only=True)
    np.testing.assert_array_equal(saved["mean"].numpy(), manifest["scaler"]["mean"])
    np.testing.assert_array_equal(saved["scale"].numpy(), manifest["scaler"]["scale"])
    assert read(run / "status.json")["state"] == "completed"


@pytest.mark.parametrize("field,value", [("lookback", 11), ("train_end", "1900-01-01"),
                                        ("validation_end", "1900-01-02")])
def test_mismatched_fold_configuration_fails_before_creating_run(tmp_path, field, value):
    path, _, fold, config = fixture(tmp_path)
    output = tmp_path / "runs"
    with pytest.raises(ValueError, match="does not match"):
        run_experiment(path, replace(config, **{field: value}), output, fold=fold)
    assert not output.exists()


def test_one_target_fold_records_null_sharpe_without_extra_dates(tmp_path):
    path, _, fold, config = fixture(tmp_path, short=True)
    run = run_experiment(path, config, tmp_path / "runs", fold=fold)
    report = read(run / "report.json")
    assert report["test_dates"] == [fold.test_start]
    for strategy in report["strategies"].values():
        assert strategy["metrics"]["observations"] == 1
        assert strategy["metrics"]["sharpe"] is None
        assert strategy["metrics"]["sharpe_note"]


def test_fold_resume_requires_the_same_protocol_and_preserves_checkpoint_on_rejection(tmp_path):
    path, _, fold, config = fixture(tmp_path)
    config = replace(config, epochs=2)
    run = run_experiment(path, config, tmp_path / "runs", fold=fold, stop_after_epochs=1)
    assert read(run / "status.json")["state"] == "paused"
    checkpoint = file_hash(run / "checkpoint.pt")
    with pytest.raises(ValueError, match="mismatch"):
        run_experiment(path, config, tmp_path / "runs", resume=run,
                       fold=replace(fold, number=fold.number + 1))
    with pytest.raises(ValueError, match="mismatch"):
        run_experiment(path, config, tmp_path / "runs", resume=run)
    assert file_hash(run / "checkpoint.pt") == checkpoint
    assert read(run / "status.json")["state"] == "paused"
    run_experiment(path, config, tmp_path / "runs", resume=run, fold=fold)
    assert read(run / "status.json")["state"] == "completed"
    assert read(run / "report.json")["test_dates"][0] == fold.test_start
    assert read(run / "report.json")["test_dates"][-1] == fold.test_end


def test_future_evaluation_prices_do_not_change_fit_or_earlier_predictions(tmp_path, monkeypatch):
    path, dataset, fold, config = fixture(tmp_path)
    reference = run_experiment(path, config, tmp_path / "runs", fold=fold)
    changed = dataset.prices.copy()
    boundary = fold.test_indices[20]
    changed[boundary:, 0] *= np.linspace(1.01, 1.8, len(changed) - boundary)
    altered = Dataset(dataset.dates, changed, dataset.manifest, dataset.manifest_path)
    monkeypatch.setattr(runner, "load_dataset", lambda _: altered)
    repeated = run_experiment(path, config, tmp_path / "runs", fold=fold)
    before = torch.load(reference / "model.pt", weights_only=True)
    after = torch.load(repeated / "model.pt", weights_only=True)
    for name, tensor in before["model"].items():
        torch.testing.assert_close(tensor, after["model"][name], rtol=0, atol=0)
    torch.testing.assert_close(before["mean"], after["mean"], rtol=0, atol=0)
    torch.testing.assert_close(before["scale"], after["scale"], rtol=0, atol=0)
    # Inputs before the changed price row must produce the same earlier weights.
    import csv
    def early_weights(run):
        with (run / "allocations.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))[1:]
        return [row for row in rows if row[1] == "lstm" and row[0] < str(dataset.dates[boundary])]
    assert early_weights(reference) == early_weights(repeated)


def test_local_a0_repeat_rejects_fold_protocol_without_training(tmp_path, monkeypatch):
    reference = tmp_path / "reference"
    reference.mkdir()
    (reference / "manifest.json").write_text(json.dumps({
        "schema_version": 1, "evaluation_protocol": {"kind": "expanding-walk-forward-fold"}}),
        encoding="utf-8")
    def forbidden(*args, **kwargs):
        pytest.fail("Unsupported fold repeat must not train")
    monkeypatch.setattr("portfolio_lab.repeat.run_experiment", forbidden)
    comparison = read(repeat_experiment(reference, tmp_path / "comparisons"))
    assert comparison["outcome"] == "unavailable"
    assert "fixed-holdout" in comparison["reason"]


def forbid_runtime_access(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid fold input must fail before data, device, or training access")
    monkeypatch.setattr(runner, "load_dataset", forbidden)
    monkeypatch.setattr(runner, "_train", forbidden)
    monkeypatch.setattr(runner.torch.cuda, "is_available", forbidden)


@pytest.mark.parametrize("field,value", [
    ("lookback", 10.0), ("hidden_size", True), ("epochs", True), ("epochs", 1.5),
    ("batch_size", 32.0), ("seed", False), ("seed", 7.0),
    ("learning_rate", True), ("learning_rate", 10**400),
    ("cost_bps", True), ("cost_bps", float("nan")), ("device", []),
])
def test_direct_fold_strict_settings_fail_before_runtime(tmp_path, monkeypatch, field, value):
    path, _, fold, config = fixture(tmp_path)
    config = replace(config, device="cuda", **{field: value}) if field != "device" else replace(config, device=value)
    forbid_runtime_access(monkeypatch)
    output = tmp_path / "runs"
    with pytest.raises(ValueError, match=field):
        run_experiment(path, config, output, fold=fold)
    assert not output.exists()


@pytest.mark.parametrize("number", [True, -1, 0.0, "0"])
def test_invalid_fold_number_precedes_device_access(tmp_path, monkeypatch, number):
    path, _, fold, config = fixture(tmp_path)
    forbid_runtime_access(monkeypatch)
    with pytest.raises(ValueError, match="explicitly numbered"):
        run_experiment(path, replace(config, device="cuda"), tmp_path / "runs", fold=replace(fold, number=number))


@pytest.mark.parametrize("budget", [True, False, 0, -1, 1.5, "1"])
def test_invalid_fold_stop_budget_precedes_runtime_access(tmp_path, monkeypatch, budget):
    path, _, fold, config = fixture(tmp_path)
    forbid_runtime_access(monkeypatch)
    with pytest.raises(ValueError, match="stop_after_epochs"):
        run_experiment(path, replace(config, device="cuda"), tmp_path / "runs", fold=fold, stop_after_epochs=budget)


def test_rejected_direct_fold_preserves_existing_checkpoint_files(tmp_path, monkeypatch):
    path, _, fold, config = fixture(tmp_path)
    retained = tmp_path / "existing-run"
    retained.mkdir()
    checkpoint, status = retained / "checkpoint.pt", retained / "status.json"
    checkpoint.write_bytes(b"retained checkpoint bytes")
    status.write_bytes(b'{"state":"paused"}\n')
    forbid_runtime_access(monkeypatch)
    with pytest.raises(ValueError, match="seed"):
        run_experiment(path, replace(config, seed=True, device="cuda"), tmp_path / "runs",
                       fold=fold, resume=retained)
    assert checkpoint.read_bytes() == b"retained checkpoint bytes"
    assert status.read_bytes() == b'{"state":"paused"}\n'
