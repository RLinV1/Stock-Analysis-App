"""Saved-run comparison tests using a tiny real CPU reference and isolated copies."""

import csv
import hashlib
import json
import shutil
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from portfolio_lab import cli
from portfolio_lab import repeat as repeat_module
from portfolio_lab.data import load_dataset, save_json, synthetic_dataset
from portfolio_lab.repeat import ABSOLUTE_TOLERANCE, IncompatibleInput, compare_runs, repeat_experiment
from portfolio_lab.runner import RunConfig, run_experiment


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot(directory):
    return {str(path.relative_to(directory)): path.read_bytes()
            for path in directory.rglob("*") if path.is_file()}


@pytest.fixture(scope="module")
def completed_reference(tmp_path_factory):
    directory = tmp_path_factory.mktemp("repeat-reference")
    dataset_path = synthetic_dataset(directory / "data", observations=120, seed=23)
    dataset = load_dataset(dataset_path)
    config = RunConfig(str(dataset.dates[75]), str(dataset.dates[95]),
                       lookback=7, hidden_size=4, epochs=2, batch_size=23,
                       learning_rate=0.002, seed=19, cost_bps=10)
    return run_experiment(dataset_path, config, directory / "runs")


@pytest.fixture
def reference(completed_reference, tmp_path):
    return Path(shutil.copytree(completed_reference, tmp_path / "reference"))


def test_repeat_uses_saved_settings_and_data_without_altering_reference(reference, tmp_path, monkeypatch):
    before = snapshot(reference)
    manifest = read_json(reference / "manifest.json")
    calls = []
    original = repeat_module.run_experiment

    def record_inputs(dataset_path, config, output_root):
        calls.append((dataset_path, asdict(config)))
        return original(dataset_path, config, output_root)

    monkeypatch.setattr(repeat_module, "run_experiment", record_inputs)
    comparison_path = repeat_experiment(reference, tmp_path / "repeats")
    comparison = read_json(comparison_path)
    repeated = Path(comparison["repeated_run"])

    assert calls == [(reference / "dataset" / "manifest.json", manifest["config"])]
    assert comparison["scope"] == "a0-local-repeat"
    assert comparison["outcome"] == "matched"
    assert comparison["absolute_tolerance"] == ABSOLUTE_TOLERANCE == 1e-7
    assert comparison["relative_tolerance"] == 0
    assert comparison["mismatch_count"] == 0
    assert comparison["max_absolute_difference"] <= ABSOLUTE_TOLERANCE
    assert comparison["comparisons"]
    assert all(entry["matches"] for entry in comparison["comparisons"])
    assert repeated != reference
    assert repeated.is_relative_to(comparison_path.parent)
    assert read_json(repeated / "manifest.json")["config"] == manifest["config"]
    assert read_json(repeated / "manifest.json")["objective"] == manifest["objective"]
    identity = {name: manifest[name] for name in repeat_module.IDENTITY_FIELDS}
    assert hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest() == manifest["identity_sha256"]
    assert snapshot(repeated / "dataset") == snapshot(reference / "dataset")
    assert read_json(repeated / "report.json")["history"] == read_json(reference / "report.json")["history"]
    assert snapshot(reference) == before


@pytest.mark.parametrize("case,outcome", [
    ("schema", "unavailable"),
    ("incomplete_state", "unavailable"),
    ("missing_manifest_field", "unavailable"),
    ("missing_objective", "unavailable"),
    ("missing_report_objective", "unavailable"),
    ("duplicate_manifest", "unavailable"),
    ("typed_config", "unavailable"),
    ("huge_numeric", "unavailable"),
    ("missing_report", "unavailable"),
    ("missing_allocations", "unavailable"),
    ("missing_dataset", "unavailable"),
    ("missing_model", "unavailable"),
    ("missing_checkpoint", "unavailable"),
    ("nonfinite_report", "unavailable"),
    ("overflow_report", "unavailable"),
    ("count_float", "unavailable"),
    ("count_bool", "unavailable"),
    ("count_huge", "unavailable"),
    ("count_mismatch", "unavailable"),
    ("source", "incompatible"),
    ("runtime", "incompatible"),
    ("config", "incompatible"),
    ("objective", "incompatible"),
    ("conventions", "incompatible"),
    ("method_label", "incompatible"),
    ("report_objective", "incompatible"),
    ("report_conventions", "incompatible"),
    ("report_cost", "incompatible"),
    ("dataset_manifest", "incompatible"),
    ("dataset_bytes", "incompatible"),
])
def test_repeat_rejects_invalid_reference_before_training(reference, tmp_path, monkeypatch, case, outcome):
    manifest_path = reference / "manifest.json"
    manifest = read_json(manifest_path)
    if case == "schema":
        manifest["schema_version"] = 2
        save_json(manifest_path, manifest)
    elif case == "incomplete_state":
        save_json(reference / "status.json", {"state": "paused"})
    elif case == "missing_manifest_field":
        del manifest["scaler"]
        save_json(manifest_path, manifest)
    elif case == "missing_objective":
        del manifest["objective"]
        save_json(manifest_path, manifest)
    elif case == "missing_report_objective":
        report = read_json(reference / "report.json")
        del report["objective"]
        save_json(reference / "report.json", report)
    elif case == "duplicate_manifest":
        raw = manifest_path.read_text(encoding="utf-8").rstrip()
        manifest_path.write_text(raw[:-1] + ', "schema_version": 1}', encoding="utf-8")
    elif case in {"typed_config", "huge_numeric"}:
        if case == "typed_config":
            manifest["config"]["epochs"] = float(manifest["config"]["epochs"])
        else:
            manifest["config"]["learning_rate"] = 10**400
        save_json(manifest_path, manifest)
    elif case in {"objective", "conventions", "method_label"}:
        if case == "objective":
            manifest["objective"]["transaction_costs"] = "included_in_training"
        elif case == "conventions":
            manifest["conventions"]["risk_free_rate"] = ABSOLUTE_TOLERANCE / 2
        else:
            manifest["method_label"] = "paper-inspired"
        identity = {name: manifest[name] for name in repeat_module.IDENTITY_FIELDS}
        manifest["identity_sha256"] = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        save_json(manifest_path, manifest)
    elif case in {"report_objective", "report_conventions", "report_cost"}:
        report = read_json(reference / "report.json")
        if case == "report_objective":
            report["objective"]["variance_epsilon"] += ABSOLUTE_TOLERANCE / 2
        elif case == "report_conventions":
            report["conventions"]["risk_free_rate"] = ABSOLUTE_TOLERANCE / 2
        else:
            report["cost_bps"] += ABSOLUTE_TOLERANCE / 2
        save_json(reference / "report.json", report)
    elif case in {"missing_report", "missing_allocations", "missing_dataset", "missing_model", "missing_checkpoint"}:
        relative = {"missing_report": "report.json", "missing_allocations": "allocations.csv",
                    "missing_dataset": "dataset/manifest.json", "missing_model": "model.pt",
                    "missing_checkpoint": "checkpoint.pt"}[case]
        (reference / relative).unlink()
    elif case in {"nonfinite_report", "overflow_report"}:
        report = read_json(reference / "report.json")
        report["strategies"]["lstm"]["metrics"]["sharpe"] = float("nan") if case == "nonfinite_report" else 1234.56789
        serialized = json.dumps(report).replace("1234.56789", "1e400") if case == "overflow_report" else json.dumps(report)
        (reference / "report.json").write_text(serialized, encoding="utf-8")
    elif case.startswith("count_"):
        report = read_json(reference / "report.json")
        count = report["strategies"]["lstm"]["metrics"]["observations"]
        report["strategies"]["lstm"]["metrics"]["observations"] = {
            "count_float": float(count), "count_bool": True,
            "count_huge": 10**400, "count_mismatch": count + 1,
        }[case]
        save_json(reference / "report.json", report)
    elif case == "source":
        monkeypatch.setattr(repeat_module, "source_fingerprint", lambda: "0" * 64)
    elif case == "runtime":
        changed = {**manifest["versions"], "torch": "different-runtime"}
        monkeypatch.setattr(repeat_module, "runtime_versions", lambda: changed)
    elif case == "config":
        manifest["config"]["seed"] += 1
        save_json(manifest_path, manifest)
    elif case == "dataset_manifest":
        path = reference / "dataset" / "manifest.json"
        data = read_json(path)
        data["source"] = "different source description"
        save_json(path, data)
    else:
        path = reference / "dataset" / manifest["dataset"]["csv"]
        with path.open("a", encoding="utf-8") as handle:
            handle.write("\n")
    before = snapshot(reference)
    calls = []

    def forbidden_training(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Invalid references must be rejected before training")

    monkeypatch.setattr(repeat_module, "run_experiment", forbidden_training)
    comparison = read_json(repeat_experiment(reference, tmp_path / "repeats"))
    assert comparison["outcome"] == outcome
    assert comparison["repeated_run"] is None
    assert comparison.get("differences") or comparison.get("reason")
    assert calls == []
    assert snapshot(reference) == before


@pytest.mark.parametrize("case,expected_path", [
    ("dates", "report.test_dates[0]"),
    ("null_reason", "report.strategies.lstm.metrics.sharpe_note"),
    ("metric", "report.strategies.lstm.metrics.cumulative_return"),
    ("return_series", "report.strategies.lstm.net_returns[0]"),
    ("allocation", "allocations[0][2]"),
    ("preprocessing", "manifest.scaler.mean[0]"),
    ("count_type", "report.strategies.lstm.metrics.observations"),
    ("missing_strategy", "report.strategies.equal_weight"),
])
def test_compare_detects_output_changes_on_identical_inputs(reference, tmp_path, case, expected_path):
    candidate = Path(shutil.copytree(reference, tmp_path / "candidate"))
    if case == "allocation":
        path = candidate / "allocations.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        rows[1][2] = str(float(rows[1][2]) + 0.001)
        rows[1][3] = str(float(rows[1][3]) - 0.001)
        with path.open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerows(rows)
    elif case == "preprocessing":
        path = candidate / "manifest.json"
        manifest = read_json(path)
        manifest["scaler"]["mean"][0] += 0.001
        save_json(path, manifest)
    else:
        path = candidate / "report.json"
        report = read_json(path)
        metrics = report["strategies"]["lstm"]["metrics"]
        if case == "dates":
            report["test_dates"][0], report["test_dates"][1] = report["test_dates"][1], report["test_dates"][0]
        elif case == "null_reason":
            original = read_json(reference / "report.json")
            original["strategies"]["lstm"]["metrics"].update(sharpe=None, sharpe_note="Zero variance")
            save_json(reference / "report.json", original)
            metrics.update(sharpe=None, sharpe_note="Insufficient observations")
        elif case == "metric":
            metrics["cumulative_return"] += 0.001
        elif case == "return_series":
            report["strategies"]["lstm"]["net_returns"][0] += 0.001
        elif case == "count_type":
            metrics["observations"] = float(metrics["observations"])
        else:
            del report["strategies"]["equal_weight"]
        save_json(path, report)
    before = snapshot(reference)
    result = compare_runs(reference, candidate)
    assert result["outcome"] == "different"
    assert result["mismatch_count"] >= 1
    assert any(entry["path"] == expected_path and not entry["matches"] for entry in result["comparisons"])
    if case in {"metric", "return_series", "allocation", "preprocessing"}:
        assert result["max_absolute_difference"] >= 0.0009
    assert snapshot(reference) == before


def test_compare_honors_numerical_tolerance_and_ignores_run_measurements(reference, tmp_path):
    candidate = Path(shutil.copytree(reference, tmp_path / "candidate"))
    path = candidate / "manifest.json"
    manifest = read_json(path)
    manifest.update(run_id="different-run", created_at="different-creation-time")
    manifest["hardware"]["ram_bytes"] = 1
    save_json(path, manifest)
    path = candidate / "report.json"
    report = read_json(path)
    report["run_id"] = "different-run"
    report["runtime"] = {"training_and_evaluation_seconds": 999, "peak_observed_rss_bytes": 1}
    report["strategies"]["lstm"]["metrics"]["cumulative_return"] += ABSOLUTE_TOLERANCE / 2
    save_json(path, report)
    result = compare_runs(reference, candidate)
    assert result["outcome"] == "matched"
    assert result["mismatch_count"] == 0
    assert 0 < result["max_absolute_difference"] <= ABSOLUTE_TOLERANCE


@pytest.mark.parametrize("field,expected_path", [
    ("objective", "report.objective.variance_epsilon"),
    ("conventions", "report.conventions.risk_free_rate"),
    ("cost_bps", "report.cost_bps"),
])
def test_report_metadata_has_zero_tolerance(reference, tmp_path, field, expected_path):
    candidate = Path(shutil.copytree(reference, tmp_path / "candidate"))
    report = read_json(candidate / "report.json")
    if field == "objective":
        report[field]["variance_epsilon"] += ABSOLUTE_TOLERANCE / 2
    elif field == "conventions":
        report[field]["risk_free_rate"] = ABSOLUTE_TOLERANCE / 2
    else:
        report[field] += ABSOLUTE_TOLERANCE / 2
    save_json(candidate / "report.json", report)
    result = compare_runs(reference, candidate)
    assert result["outcome"] == "different"
    entry, = [entry for entry in result["comparisons"] if entry["path"] == expected_path]
    assert entry["matches"] is False
    assert entry["absolute_tolerance"] == 0


@pytest.mark.parametrize("field", ["config", "objective"])
def test_immutable_input_types_and_values_compare_exactly(reference, tmp_path, field):
    candidate = Path(shutil.copytree(reference, tmp_path / "candidate"))
    manifest = read_json(candidate / "manifest.json")
    if field == "config":
        manifest[field]["epochs"] = float(manifest[field]["epochs"])
    else:
        manifest[field]["variance_epsilon"] += ABSOLUTE_TOLERANCE / 2
    save_json(candidate / "manifest.json", manifest)
    with pytest.raises(IncompatibleInput) as rejected:
        compare_runs(reference, candidate)
    assert rejected.value.differences[0]["path"] == field


@pytest.mark.parametrize("expected,actual,overflow,difference", [
    (1e308, -1e308, True, None),
    (10**400, 1, True, None),
    (10**400, 10**400 + 1, False, 1),
])
def test_comparison_retains_serializable_extreme_diagnostics(
        reference, tmp_path, expected, actual, overflow, difference):
    # Direct output comparison is diagnostic, not reference authenticity validation.
    candidate = Path(shutil.copytree(reference, tmp_path / "candidate"))
    for directory, value in ((reference, expected), (candidate, actual)):
        report = read_json(directory / "report.json")
        report["strategies"]["lstm"]["metrics"]["cumulative_return"] = value
        save_json(directory / "report.json", report)
    before = snapshot(reference)
    result = compare_runs(reference, candidate)
    entry, = [entry for entry in result["comparisons"]
              if entry["path"] == "report.strategies.lstm.metrics.cumulative_return"]
    assert result["outcome"] == "different"
    assert entry["matches"] is False
    assert bool(entry.get("absolute_difference_overflow")) is overflow
    if overflow:
        assert "absolute_difference" not in entry
        assert result["max_absolute_difference"] is None
    else:
        assert entry["absolute_difference"] == difference
        assert result["max_absolute_difference"] == difference
    output = tmp_path / "comparison.json"
    save_json(output, result)
    assert read_json(output) == result
    assert snapshot(reference) == before


def test_huge_integer_numeric_type_mismatch_needs_no_float_conversion():
    entries = []
    repeat_module._compare("count", 10**400, 1.0, entries)
    assert entries == [{"path": "count", "expected": 10**400, "actual": 1.0,
                        "absolute_tolerance": 0, "matches": False,
                        "reason": "Different numeric types"}]
    json.dumps(entries, allow_nan=False)


def test_failed_training_retains_comparison_and_failed_artifacts(reference, tmp_path, monkeypatch):
    before = snapshot(reference)

    def failing_training(dataset_path, config, output_root):
        failed = output_root / "failed-attempt"
        failed.mkdir(parents=True)
        save_json(failed / "status.json", {"state": "failed", "error_type": "RuntimeError"})
        raise RuntimeError("Deliberate compute failure")

    monkeypatch.setattr(repeat_module, "run_experiment", failing_training)
    path = repeat_experiment(reference, tmp_path / "repeats")
    result = read_json(path)
    assert result["outcome"] == "failed"
    assert result["repeated_run"] is None
    assert result["error_type"] == "RuntimeError"
    assert "Deliberate compute failure" in result["reason"]
    assert read_json(path.parent / "runs" / "failed-attempt" / "status.json")["state"] == "failed"
    assert snapshot(reference) == before


@pytest.mark.parametrize("relative", [".", "nested/repeats"])
def test_repeat_refuses_output_inside_reference(reference, relative):
    before = snapshot(reference)
    with pytest.raises(ValueError, match="outside the immutable reference"):
        repeat_experiment(reference, reference / relative)
    assert snapshot(reference) == before


@pytest.mark.parametrize("outcome", ["different", "incompatible", "unavailable", "failed"])
def test_repeat_cli_nonmatch_exits_one(tmp_path, monkeypatch, capsys, outcome):
    report = tmp_path / "comparison.json"
    save_json(report, {"outcome": outcome})
    monkeypatch.setattr(cli, "repeat_experiment", lambda reference, output: report)
    monkeypatch.setattr(sys, "argv", ["portfolio-lab", "repeat", str(tmp_path / "reference"),
                                     "--output", str(tmp_path / "repeats")])
    with pytest.raises(SystemExit) as result:
        cli.main()
    assert result.value.code == 1
    captured = capsys.readouterr()
    assert str(report) in captured.out
    assert outcome in captured.err
