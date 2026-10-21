"""Unrun source regressions for continuous accounting and local fold groups."""

import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pytest

from portfolio_lab import cli, data as data_module, protocol, walk_forward
from portfolio_lab.data import file_hash, load_dataset, synthetic_dataset
from portfolio_lab.protocol import plan_walk_forward
from portfolio_lab.model import OBJECTIVE_CONVENTIONS
from portfolio_lab.walk_forward import WalkForwardConfig, continuous_results, run_walk_forward


def fixture(tmp_path):
    path = synthetic_dataset(tmp_path / "data", 1000)
    data = load_dataset(path)
    config = WalkForwardConfig(str(data.dates[330]), str(data.dates[-1]),
                               lookback=10, hidden_size=8, epochs=1, batch_size=64,
                               learning_rate=0.001, seed=7, cost_bps=1, device="cpu")
    return path, data, config


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_cross_fold_account_uses_actual_previous_target_once():
    # Two conceptual folds meet between rows 1 and 2 with unchanged weights.
    weights = np.array([[1., 0.], [.5, .5], [.5, .5], [0., 1.]])
    returns = np.array([[.1, 0.], [.02, .04], [.02, .04], [0., .1]])
    result = continuous_results({"lstm": weights}, returns, 10)["lstm"]
    np.testing.assert_allclose(result["turnover"], [1., 1., 0., 1.])
    np.testing.assert_allclose(result["costs"], [.001, .001, 0., .001])
    np.testing.assert_allclose(result["net_returns"], [.099, .029, .03, .099])
    assert result["metrics"]["cumulative_return"] == pytest.approx(1.099 * 1.029 * 1.03 * 1.099 - 1)
    assert result["metrics"]["observations"] == 4


@pytest.mark.parametrize("single_target", [False, True])
def test_aggregation_returns_match_samples_without_rebuilding_features(tmp_path, monkeypatch, single_target):
    _, data, config = fixture(tmp_path)
    if single_target:
        config = replace(config, test_end=config.test_start)
    plan = plan_walk_forward(data.dates, config.test_start, config.test_end, lookback=config.lookback)
    expected = []
    for fold in plan.folds:
        samples = protocol.make_fold_samples(data, fold)
        expected.append(samples.y[samples.test])
    def forbidden(*args, **kwargs):
        pytest.fail("Aggregation must not construct feature windows or fit another scaler")
    monkeypatch.setattr(data_module, "make_samples", forbidden)
    monkeypatch.setattr(protocol, "make_samples", forbidden)
    for fold, targets in zip(plan.folds, expected):
        actual = walk_forward._evaluation_returns(data, fold)
        assert actual.dtype == targets.dtype == np.float32
        np.testing.assert_array_equal(actual, targets)


@pytest.mark.parametrize("field,value", [("epochs", True), ("epochs", 1.5), ("seed", False),
                                        ("hidden_size", 8.1), ("learning_rate", True),
                                        ("cost_bps", float("nan")), ("device", 1)])
def test_invalid_explicit_settings_fail_before_creating_group(tmp_path, field, value):
    path, _, config = fixture(tmp_path)
    output = tmp_path / "runs"
    with pytest.raises(ValueError):
        run_walk_forward(path, replace(config, **{field: value}), output)
    assert not output.exists()


def test_group_retains_each_frozen_model_and_every_planned_date(tmp_path):
    path, data, config = fixture(tmp_path)
    plan = plan_walk_forward(data.dates, config.test_start, config.test_end, lookback=config.lookback)
    assert len(plan.folds) >= 2
    group = run_walk_forward(path, config, tmp_path / "runs")
    manifest, report, status = (read(group / name) for name in ("manifest.json", "report.json", "status.json"))
    assert status == {"state": "completed", "completed_folds": len(plan.folds), "fold_budget": len(plan.folds)}
    assert manifest["evaluation_protocol"]["kind"] == "expanding-walk-forward"
    assert report["test_dates"] == [str(data.dates[i]) for fold in plan.folds for i in fold.test_indices]
    assert len(set(report["test_dates"])) == len(report["test_dates"])
    assert report["method_label"] == "synthetic-walk-forward"
    assert manifest["objective"] == report["objective"] == OBJECTIVE_CONVENTIONS
    assert len(report["folds"]) == len(plan.folds)
    child_gross = {name: [] for name in report["strategies"]}
    for record, fold in zip(report["folds"], plan.folds):
        child = group / record["run_directory"]
        assert child.resolve().is_relative_to(group.resolve())
        assert file_hash(child / "model.pt") == record["model_and_scaler_sha256"]
        assert file_hash(child / "manifest.json") == record["manifest_sha256"]
        assert file_hash(child / "report.json") == record["report_sha256"]
        assert read(child / "report.json")["test_dates"] == data.dates[list(fold.test_indices)].tolist()
        assert record["deviations"] == read(child / "manifest.json")["deviations"]
        assert report["baseline_omissions"] == read(child / "report.json")["baseline_omissions"]
        for name, result in read(child / "report.json")["strategies"].items():
            child_gross[name].extend(result["gross_returns"])
    for name, result in report["strategies"].items():
        assert result["gross_returns"] == child_gross[name]


def test_group_with_one_target_keeps_one_observation_and_explained_null_sharpe(tmp_path):
    path, _, config = fixture(tmp_path)
    config = replace(config, test_end=config.test_start)
    group = run_walk_forward(path, config, tmp_path / "runs")
    report = read(group / "report.json")
    assert report["test_dates"] == [config.test_start]
    assert len(report["folds"]) == 1
    for result in report["strategies"].values():
        assert result["metrics"]["observations"] == 1
        assert result["metrics"]["sharpe"] is None
        assert result["metrics"]["sharpe_note"]
        assert len(result["wealth"]) == 1


def test_group_rejects_wrong_child_protocol_before_publishing_aggregate(tmp_path, monkeypatch):
    path, _, config = fixture(tmp_path)
    real = walk_forward.run_experiment
    def wrong_protocol(*args, **kwargs):
        child = real(*args, **kwargs)
        manifest = read(child / "manifest.json")
        manifest["evaluation_protocol"]["fold"]["number"] += 1
        (child / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return child
    monkeypatch.setattr(walk_forward, "run_experiment", wrong_protocol)
    output = tmp_path / "runs"
    with pytest.raises(ValueError, match="provenance"):
        run_walk_forward(path, config, output)
    group, = output.iterdir()
    assert read(group / "status.json")["state"] == "failed"
    assert not (group / "report.json").exists()


def test_failed_later_fold_preserves_partial_evidence_without_completion(tmp_path, monkeypatch):
    path, _, config = fixture(tmp_path)
    real = walk_forward.run_experiment
    calls = 0
    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("Deliberate second-fold failure")
        return real(*args, **kwargs)
    monkeypatch.setattr(walk_forward, "run_experiment", fail_second)
    output = tmp_path / "runs"
    with pytest.raises(RuntimeError, match="second-fold"):
        run_walk_forward(path, config, output)
    group, = output.iterdir()
    status = read(group / "status.json")
    assert status["state"] == "failed" and status["completed_folds"] == 1
    assert status["error_type"] == "RuntimeError"
    assert status["active_fold"] == 1
    assert len(status["completed_runs"]) == 1
    retained = group / status["completed_runs"][0]["run_directory"]
    assert retained.is_dir()
    assert file_hash(retained / "model.pt") == status["completed_runs"][0]["model_and_scaler_sha256"]
    assert len(read(group / "folds.json")["completed_folds"]) == 1
    assert not (group / "report.json").exists()


def test_cli_requires_complete_explicit_config_and_calls_local_group(tmp_path, monkeypatch, capsys):
    config = {"test_start": "2015-01-01", "test_end": "2018-01-01", "lookback": 10,
              "hidden_size": 8, "epochs": 1, "batch_size": 64, "learning_rate": .001,
              "seed": 7, "cost_bps": 1, "device": "cpu"}
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps(config), encoding="utf-8")
    dataset, output = tmp_path / "dataset.json", tmp_path / "runs"
    calls = []
    def run(path, selected, destination):
        calls.append((path, asdict(selected), destination))
        return destination / "walk-forward-fixture"
    monkeypatch.setattr(cli, "run_walk_forward", run)
    monkeypatch.setattr(sys, "argv", ["portfolio-lab", "walk-forward", str(dataset),
                                      "--config", str(settings), "--output", str(output)])
    cli.main()
    assert calls == [(dataset, config, output)]
    assert "walk-forward-fixture" in capsys.readouterr().out
    settings.write_text(json.dumps({"test_start": "2015-01-01"}), encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
    assert len(calls) == 1


def test_relative_output_root_keeps_resolvable_child_hashes(tmp_path, monkeypatch):
    path, _, config = fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    group = run_walk_forward(path, replace(config, test_end=config.test_start), Path("runs"))
    assert not group.is_absolute()
    record, = read(group / "report.json")["folds"]
    child = group / record["run_directory"]
    assert child.resolve().is_relative_to(group.resolve())
    assert file_hash(child / "model.pt") == record["model_and_scaler_sha256"]
    assert file_hash(child / "report.json") == record["report_sha256"]
