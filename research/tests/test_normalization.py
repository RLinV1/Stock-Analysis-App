"""Explicit normalization control regressions; written only, all unrun.

These cases validate controls and compatibility, not a paired research finding.
"""

import json
import shutil
from dataclasses import fields, replace

import numpy as np
import pytest
import torch

from portfolio_lab import runner, service_contract
from portfolio_lab.data import Samples, load_dataset, make_samples, synthetic_dataset
from portfolio_lab.protocol import plan_walk_forward
from portfolio_lab.repeat import repeat_experiment
from portfolio_lab.runner import RunConfig, run_experiment
from portfolio_lab.walk_forward import WalkForwardConfig


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def data(tmp_path, observations=140):
    manifest = synthetic_dataset(tmp_path / "data", observations=observations)
    return manifest, load_dataset(manifest)


def test_default_samples_equal_explicit_train_only_and_raw_preserves_alignment(tmp_path):
    _, dataset = data(tmp_path)
    arguments = (dataset, 10, str(dataset.dates[90]), str(dataset.dates[110]))
    default = make_samples(*arguments)
    standard = make_samples(*arguments, normalization="train-only")
    raw = make_samples(*arguments, normalization="raw")
    for field in fields(Samples):
        np.testing.assert_array_equal(getattr(default, field.name), getattr(standard, field.name))
    for name in ("y", "dates", "train", "validation", "test"):
        np.testing.assert_array_equal(getattr(raw, name), getattr(standard, name))
    np.testing.assert_array_equal(raw.mean, np.zeros(2 * len(dataset.symbols)))
    np.testing.assert_array_equal(raw.scale, np.ones(2 * len(dataset.symbols)))
    returns = np.zeros_like(dataset.prices)
    returns[1:] = dataset.prices[1:] / dataset.prices[:-1] - 1
    expected = np.stack([dataset.prices, returns], axis=2).reshape(len(dataset.dates), -1)
    np.testing.assert_array_equal(raw.x[0], expected[:10].astype(np.float32))
    np.testing.assert_array_equal(raw.y[0], returns[10].astype(np.float32))
    assert not np.array_equal(raw.x, standard.x)


def test_raw_future_change_cannot_change_prior_inputs_or_first_test_decision(tmp_path):
    _, dataset = data(tmp_path)
    arguments = (10, str(dataset.dates[90]), str(dataset.dates[110]))
    original = make_samples(dataset, *arguments, normalization="raw")
    dataset.prices[111:, 0] *= 3
    changed = make_samples(dataset, *arguments, normalization="raw")
    prior = original.train | original.validation
    np.testing.assert_array_equal(original.x[prior], changed.x[prior])
    np.testing.assert_array_equal(original.y[prior], changed.y[prior])
    np.testing.assert_array_equal(original.x[original.test][0], changed.x[changed.test][0])
    np.testing.assert_array_equal(original.mean, changed.mean)
    np.testing.assert_array_equal(original.scale, changed.scale)
    assert not np.array_equal(original.y[original.test], changed.y[changed.test])


def test_raw_float32_overflow_rejects_instead_of_implicitly_normalizing(tmp_path):
    _, dataset = data(tmp_path)
    dataset.prices *= 1e40
    with np.errstate(over="ignore", invalid="ignore"):
        with pytest.raises(ValueError, match="conversion overflowed"):
            make_samples(dataset, 10, str(dataset.dates[90]), str(dataset.dates[110]), normalization="raw")


@pytest.mark.parametrize("mode", [None, True, 1, [], {}, "standard", "RAW", "", "train-only "])
def test_invalid_sampler_modes_reject_before_dataset_access(mode):
    with pytest.raises(ValueError, match="normalization"):
        make_samples(None, 10, "2020-01-01", "2020-02-01", normalization=mode)


@pytest.mark.parametrize("mode", [None, True, [], "RAW", "unknown"])
def test_invalid_run_modes_reject_before_data_device_or_training(tmp_path, monkeypatch, mode):
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid normalization must reject before runtime access")
    monkeypatch.setattr(runner, "load_dataset", forbidden)
    monkeypatch.setattr(runner, "_train", forbidden)
    monkeypatch.setattr(runner.torch.cuda, "is_available", forbidden)
    config = RunConfig("2020-01-01", "2020-02-01", normalization=mode, device="cuda")
    with pytest.raises(ValueError, match="normalization"):
        run_experiment(tmp_path / "missing.json", config, tmp_path / "runs")
    assert not (tmp_path / "runs").exists()


def test_raw_direct_fold_is_rejected_before_runtime(tmp_path, monkeypatch):
    manifest, dataset = data(tmp_path, observations=420)
    fold = plan_walk_forward(dataset.dates, str(dataset.dates[330]), str(dataset.dates[334]), lookback=10).folds[0]
    config = RunConfig(fold.train_end, fold.validation_end, lookback=10, normalization="raw", device="cuda")
    def forbidden(*args, **kwargs):
        pytest.fail("Raw fold must reject before data/device/training access")
    monkeypatch.setattr(runner, "load_dataset", forbidden)
    monkeypatch.setattr(runner, "_train", forbidden)
    monkeypatch.setattr(runner.torch.cuda, "is_available", forbidden)
    with pytest.raises(ValueError, match="fixed-holdout"):
        run_experiment(manifest, config, tmp_path / "runs", fold=fold)
    assert not (tmp_path / "runs").exists()


def test_fold_config_explicitly_retains_train_only_mode(tmp_path):
    _, dataset = data(tmp_path, observations=420)
    config = WalkForwardConfig(str(dataset.dates[330]), str(dataset.dates[334]),
                               10, 4, 1, 64, 0.001, 7, 1, "cpu")
    fold = plan_walk_forward(dataset.dates, config.test_start, config.test_end, lookback=config.lookback).folds[0]
    assert config.for_fold(fold).normalization == "train-only"
    assert config.for_fold(fold).objective_window == "minibatch"


def test_service_adapter_explicitly_retains_train_only_mode(tmp_path, monkeypatch):
    request = service_contract.load_request(service_contract.SCHEMA_PATH.parent / "examples/synthetic-smoke.v1.json")
    captured = []
    def no_training(dataset_path, config, output, **kwargs):
        captured.append(config)
        directory = output / "stub"
        directory.mkdir()
        return directory
    monkeypatch.setattr(service_contract, "run_experiment", no_training)
    run = service_contract.execute_synthetic_request(request, tmp_path / "runs")
    assert captured[0].normalization == "train-only"
    assert captured[0].objective_window == "minibatch"
    assert "normalization" not in request["model"]
    assert (run / "request.json").is_file()


@pytest.fixture(scope="module")
def raw_reference(tmp_path_factory):
    directory = tmp_path_factory.mktemp("raw-normalization")
    manifest, dataset = data(directory)
    config = RunConfig(str(dataset.dates[90]), str(dataset.dates[110]), lookback=10,
                       hidden_size=4, epochs=2, batch_size=64, device="cpu", normalization="raw")
    full = run_experiment(manifest, config, directory / "runs")
    partial = run_experiment(manifest, config, directory / "runs", stop_after_epochs=1)
    return manifest, config, full, partial


def test_raw_artifacts_and_epoch_resume_preserve_mode_and_results(tmp_path, raw_reference):
    dataset_path, config, full, partial = raw_reference
    run = tmp_path / "resume-copy"
    shutil.copytree(partial, run)
    manifest_before = (run / "manifest.json").read_bytes()
    run_experiment(dataset_path, config, tmp_path / "unused-output", resume=run)
    assert (run / "manifest.json").read_bytes() == manifest_before
    manifest, report = read(run / "manifest.json"), read(run / "report.json")
    assert manifest["config"]["normalization"] == "raw"
    assert any("identity transform" in item for item in manifest["deviations"])
    np.testing.assert_array_equal(manifest["scaler"]["mean"], np.zeros(6))
    np.testing.assert_array_equal(manifest["scaler"]["scale"], np.ones(6))
    model = torch.load(run / "model.pt", map_location="cpu", weights_only=True)
    assert model["config"]["normalization"] == "raw"
    np.testing.assert_array_equal(model["mean"].numpy(), manifest["scaler"]["mean"])
    np.testing.assert_array_equal(model["scale"].numpy(), manifest["scaler"]["scale"])
    assert read(run / "status.json")["state"] == "completed"
    assert report["history"] == read(full / "report.json")["history"]
    assert report["strategies"] == read(full / "report.json")["strategies"]


def test_raw_reference_can_use_current_local_repeat(tmp_path, raw_reference):
    _, _, full, _ = raw_reference
    result = read(repeat_experiment(full, tmp_path / "repeats"))
    assert result["outcome"] == "matched"
    assert result["mismatch_count"] == 0


def test_changed_normalization_resume_preserves_paused_evidence(tmp_path, monkeypatch, raw_reference):
    dataset_path, config, _, partial = raw_reference
    before = {name: (partial / name).read_bytes() for name in ("manifest.json", "status.json", "checkpoint.pt")}
    monkeypatch.setattr(runner, "_train", lambda *args, **kwargs: pytest.fail("Changed mode must reject"))
    with pytest.raises(ValueError, match="mismatch"):
        run_experiment(dataset_path, replace(config, normalization="train-only"), tmp_path / "unused-output", resume=partial)
    assert {name: (partial / name).read_bytes() for name in before} == before
    assert read(partial / "status.json")["state"] == "paused"
