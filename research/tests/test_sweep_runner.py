"""Unrun orchestration cases with stub training; not real-run integration."""

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from portfolio_lab import sweep_runner as runner
from portfolio_lab.metrics import evaluate
from portfolio_lab.sweep import SweepSettings


@dataclass(frozen=True)
class StubFold:
    number: int = 0
    train_end: str = "2023-01-01"
    validation_end: str = "2023-02-01"
    test_indices: tuple = (0, 1, 2)


@dataclass(frozen=True)
class StubPlan:
    folds: tuple = (StubFold(),)


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def setup(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    manifest = {"csv": "prices.csv", "kind": "synthetic", "deviations": ["synthetic fixture"],
                "assets": [{"symbol": "A", "role": "stock"}, {"symbol": "B", "role": "stock"}]}
    write(source / "manifest.json", manifest)
    (source / "prices.csv").write_bytes(b"fixture prices\n")
    dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
    plan, calls = StubPlan(), []
    config = runner.SweepModelConfig(dates[0], dates[-1], 10, 8, 1, 32, 0.001, "cpu")

    def load(manifest_path):
        return SimpleNamespace(manifest=read(manifest_path), manifest_path=manifest_path, dates=dates)

    def snapshot(dataset, destination):
        destination.mkdir()
        shutil.copyfile(dataset.manifest_path, destination / "manifest.json")
        shutil.copyfile(dataset.manifest_path.parent / "prices.csv", destination / "prices.csv")
        return load(destination / "manifest.json")

    def child(dataset_path, child_config, output):
        calls.append({"dataset_path": dataset_path, "config": child_config,
                      "csv": (dataset_path.parent / "prices.csv").read_bytes()})
        directory = output / "walk-forward-stub"
        directory.mkdir()
        child_manifest = {
            "config": asdict(child_config),
            "dataset_manifest_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
            "source_sha256": "a" * 64, "versions": {"runtime": "stub"},
            "evaluation_protocol": json.loads(json.dumps({"kind": "expanding-walk-forward", "plan": asdict(plan)})),
            "method_label": "synthetic-walk-forward", "conventions": runner.CONVENTIONS,
            "objective": runner.OBJECTIVE_CONVENTIONS,
        }
        write(directory / "manifest.json", child_manifest)
        write(directory / "status.json", {"state": "completed", "completed_folds": 1, "fold_budget": 1})
        result = evaluate([[0.5, 0.5]] * 3, [[0.01, 0.02], [0.02, 0.01], [0.01, -0.01]],
                          child_config.cost_bps)
        write(directory / "report.json", {
            "test_dates": dates, "cost_bps": child_config.cost_bps,
            "method_label": "synthetic-walk-forward", "conventions": runner.CONVENTIONS,
            "objective": runner.OBJECTIVE_CONVENTIONS,
            "strategies": {"lstm": result, "equal_weight": result},
            "baseline_omissions": ["60/40 unavailable: missing stock/bond roles"],
        })
        return directory

    monkeypatch.setattr(runner, "load_dataset", load)
    monkeypatch.setattr(runner, "snapshot_dataset", snapshot)
    monkeypatch.setattr(runner, "plan_walk_forward", lambda *args, **kwargs: plan)
    monkeypatch.setattr(runner, "source_fingerprint", lambda: "a" * 64)
    monkeypatch.setattr(runner, "runtime_versions", lambda: {"runtime": "stub"})
    monkeypatch.setattr(runner, "run_walk_forward", child)
    return SimpleNamespace(source=source, manifest=source / "manifest.json", config=config,
                           settings=SweepSettings((7, 3), (5, 0), 4), output=tmp_path / "runs",
                           calls=calls, child=child)


def test_sequential_grid_has_matching_identity_and_retained_hashes(setup):
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert [(call["config"].seed, call["config"].cost_bps) for call in setup.calls] == [(7, 5), (7, 0), (3, 5), (3, 0)]
    assert len({call["dataset_path"] for call in setup.calls}) == 1
    assert all(call["dataset_path"] == group / "dataset/manifest.json" for call in setup.calls)
    inventory = read(group / "candidates.json")
    for row in inventory:
        directory = group / row["run_directory"]
        for filename, field in (("manifest.json", "manifest_sha256"), ("report.json", "report_sha256"), ("status.json", "status_sha256")):
            assert row[field] == hashlib.sha256((directory / filename).read_bytes()).hexdigest()
    status = read(group / "status.json")
    assert status["state"] == "completed"
    assert status["coverage_complete"] is True
    assert status["all_successful"] is True
    assert status["planned_fold_runs"] == 4
    assert status["resume_supported"] is False
    assert read(group / "report.json")["completed"] == 4
    first = inventory[0]
    child_report = read(group / first["run_directory"] / "report.json")
    assert first["strategies"]["lstm"] == child_report["strategies"]["lstm"]["metrics"]
    assert "wealth" not in first["strategies"]["lstm"]


@pytest.mark.parametrize("replacement", [None, [], {}, {"lstm": {}}, {"lstm": {"metrics": []}}])
def test_missing_or_malformed_nested_strategy_metrics_are_invalid(setup, monkeypatch, replacement):
    def tampered(*args):
        directory = setup.child(*args)
        payload = read(directory / "report.json")
        payload["strategies"] = replacement
        write(directory / "report.json", payload)
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", tampered)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert read(group / "report.json")["invalid"] == 4


def test_flat_metrics_do_not_masquerade_as_walk_forward_results(setup, monkeypatch):
    def tampered(*args):
        directory = setup.child(*args)
        payload = read(directory / "report.json")
        payload["strategies"] = {name: result["metrics"] for name, result in payload["strategies"].items()}
        write(directory / "report.json", payload)
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", tampered)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert read(group / "report.json")["invalid"] == 4


@pytest.mark.parametrize("section", ["config", "protocol", "conventions"])
def test_boolean_numeric_identity_aliases_are_invalid(setup, monkeypatch, section):
    def tampered(*args):
        directory = setup.child(*args)
        payload = read(directory / "manifest.json")
        if section == "config":
            payload["config"]["epochs"] = True
        elif section == "protocol":
            payload["evaluation_protocol"]["plan"]["folds"][0]["number"] = False
        else:
            payload["conventions"]["risk_free_rate"] = False
        write(directory / "manifest.json", payload)
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", tampered)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert read(group / "report.json")["invalid"] == 4


def test_invalid_common_settings_fail_before_group_creation(setup):
    with pytest.raises(ValueError):
        runner.run_sweep(setup.manifest, replace(setup.config, epochs=True), setup.settings, setup.output)
    assert not setup.output.exists()
    assert not setup.calls


def test_excess_candidate_budget_fails_before_loading_or_output(setup, monkeypatch):
    monkeypatch.setattr(runner, "load_dataset", lambda _: pytest.fail("grid must validate first"))
    with pytest.raises(ValueError, match="max_runs"):
        runner.run_sweep(setup.manifest, setup.config, SweepSettings((7, 3), (5, 0), 3), setup.output)
    assert not setup.output.exists()


def test_original_mutation_does_not_change_later_candidate_inputs(setup, monkeypatch):
    def mutate(*args):
        directory = setup.child(*args)
        (setup.source / "prices.csv").write_bytes(b"changed original\n")
        write(setup.manifest, {"csv": "different.csv"})
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", mutate)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert len(setup.calls) == 4
    assert all(call["csv"] == b"fixture prices\n" for call in setup.calls)
    assert read(group / "status.json")["all_successful"] is True


def test_training_failure_is_retained_and_later_candidates_continue(setup, monkeypatch):
    attempted = []
    def failing(dataset, config, output):
        attempted.append((config.seed, config.cost_bps))
        if len(attempted) == 2:
            raise RuntimeError("operator credential must not appear in retained error")
        return setup.child(dataset, config, output)
    monkeypatch.setattr(runner, "run_walk_forward", failing)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert len(attempted) == 4
    inventory = read(group / "candidates.json")
    assert [row["status"] for row in inventory] == ["completed", "failed", "completed", "completed"]
    assert inventory[1]["error_type"] == "RuntimeError"
    assert "operator credential" not in (group / "candidates.json").read_text()
    report, status = read(group / "report.json"), read(group / "status.json")
    assert (report["completed"], report["failed"]) == (3, 1)
    assert status["state"] == "completed_with_failures"
    assert status["coverage_complete"] is True
    assert status["all_successful"] is False


@pytest.mark.parametrize("target,key,value", [
    ("manifest.json", "source_sha256", "b" * 64),
    ("manifest.json", "dataset_manifest_sha256", "c" * 64),
    ("manifest.json", "method_label", "historical-proof"),
    ("manifest.json", "versions", {"runtime": "different"}),
    ("manifest.json", "evaluation_protocol", {}),
    ("manifest.json", "objective", {}),
    ("report.json", "test_dates", ["2024-01-02"]),
    ("report.json", "cost_bps", 99),
    ("report.json", "cost_bps", False),
    ("report.json", "method_label", "historical-proof"),
    ("report.json", "conventions", {}),
    ("report.json", "objective", {}),
    ("status.json", "state", "running"),
    ("status.json", "completed_folds", 0),
    ("status.json", "completed_folds", True),
    ("status.json", "fold_budget", 2),
])
def test_bad_returned_artifact_is_invalid_not_success(setup, monkeypatch, target, key, value):
    def tampered(*args):
        directory = setup.child(*args)
        payload = read(directory / target)
        payload[key] = value
        write(directory / target, payload)
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", tampered)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    report = read(group / "report.json")
    assert report["invalid"] == 4
    assert report["completed"] == 0
    assert report["context"] is None
    assert read(group / "status.json")["state"] == "completed_with_failures"


@pytest.mark.parametrize("case", ["missing_equal_weight", "missing_lstm", "extra_strategy",
                                   "omission_object", "omission_none", "wrong_omission"])
def test_first_candidate_cannot_narrow_baselines_or_invent_omissions(setup, monkeypatch, case):
    def tampered(*args):
        directory = setup.child(*args)
        payload = read(directory / "report.json")
        if case.startswith("missing_"):
            del payload["strategies"][case.removeprefix("missing_")]
        elif case == "extra_strategy":
            payload["strategies"]["cash"] = payload["strategies"]["equal_weight"]
        else:
            payload["baseline_omissions"] = {
                "omission_object": {}, "omission_none": None, "wrong_omission": [],
            }[case]
        write(directory / "report.json", payload)
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", tampered)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert read(group / "report.json")["invalid"] == 4
    assert read(group / "report.json")["completed"] == 0


@pytest.mark.parametrize("include_baseline", [False, True])
def test_declared_stock_bond_roles_require_the_available_baseline(setup, monkeypatch, include_baseline):
    manifest = read(setup.manifest)
    manifest["assets"][1]["role"] = "bond"
    write(setup.manifest, manifest)
    def produced(*args):
        directory = setup.child(*args)
        payload = read(directory / "report.json")
        payload["baseline_omissions"] = []
        if include_baseline:
            payload["strategies"]["stock_bond_60_40"] = payload["strategies"]["equal_weight"]
        write(directory / "report.json", payload)
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", produced)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    report = read(group / "report.json")
    assert report["completed"] == (4 if include_baseline else 0)
    assert report["invalid"] == (0 if include_baseline else 4)


def test_candidate_config_drift_is_invalid(setup, monkeypatch):
    def tampered(*args):
        directory = setup.child(*args)
        payload = read(directory / "manifest.json")
        payload["config"]["seed"] += 1
        write(directory / "manifest.json", payload)
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", tampered)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert read(group / "report.json")["invalid"] == 4


def test_baseline_omissions_are_not_pooled(setup, monkeypatch):
    def tampered(*args):
        directory = setup.child(*args)
        if len(setup.calls) > 1:
            payload = read(directory / "report.json")
            payload["baseline_omissions"] = ["changed baseline availability"]
            write(directory / "report.json", payload)
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", tampered)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert [row["status"] for row in read(group / "candidates.json")] == ["completed", "invalid", "invalid", "invalid"]


def test_strategy_set_drift_is_invalid(setup, monkeypatch):
    def tampered(*args):
        directory = setup.child(*args)
        if len(setup.calls) > 1:
            payload = read(directory / "report.json")
            payload["strategies"]["cash"] = dict(payload["strategies"]["equal_weight"])
            write(directory / "report.json", payload)
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", tampered)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert [row["status"] for row in read(group / "candidates.json")] == ["completed", "invalid", "invalid", "invalid"]


def test_nonfinite_metrics_are_invalid_even_when_group_says_completed(setup, monkeypatch):
    def tampered(*args):
        directory = setup.child(*args)
        payload = read(directory / "report.json")
        payload["strategies"]["lstm"]["metrics"]["cumulative_return"] = float("nan")
        write(directory / "report.json", payload)
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", tampered)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    report = read(group / "report.json")
    assert report["invalid"] == 4
    assert report["context"] is None
    assert report["by_cost"][0]["strategies"] == {}


def test_changed_owned_snapshot_prevents_later_training(setup, monkeypatch):
    def mutate(dataset_path, config, output):
        directory = setup.child(dataset_path, config, output)
        payload = read(dataset_path)
        payload["changed_after_first_candidate"] = True
        write(dataset_path, payload)
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", mutate)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert len(setup.calls) == 1
    assert [row["status"] for row in read(group / "candidates.json")] == ["completed", "failed", "failed", "failed"]
    report = read(group / "report.json")
    assert report["completed"] == 1
    assert report["failed"] == 3
    assert report["all_successful"] is False


def test_entirely_failed_execution_retains_grid_without_metrics(setup, monkeypatch):
    attempted = []
    def fail(dataset, config, output):
        attempted.append((config.seed, config.cost_bps))
        raise RuntimeError("training failed")
    monkeypatch.setattr(runner, "run_walk_forward", fail)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert attempted == [(7, 5), (7, 0), (3, 5), (3, 0)]
    report = read(group / "report.json")
    assert (report["completed"], report["failed"], report["invalid"]) == (0, 4, 0)
    assert report["context"] is None
    assert all(cost["strategies"] == {} for cost in report["by_cost"])
    assert report["tested_cost_intervals"] == []
    assert read(group / "status.json")["state"] == "completed_with_failures"


def test_foreign_returned_directory_is_rejected_before_reading(setup, monkeypatch, tmp_path):
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "manifest.json").write_text("do not read as experiment evidence")
    monkeypatch.setattr(runner, "run_walk_forward", lambda *args: foreign)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert read(group / "report.json")["invalid"] == 4
    assert (foreign / "manifest.json").read_text() == "do not read as experiment evidence"


def test_escaped_candidate_root_is_rejected_before_artifact_reads(tmp_path, monkeypatch):
    group = tmp_path / "sweep"
    group.mkdir()
    candidate_root = group / "candidates" / "candidate-0000"
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    child = foreign / "walk-forward"
    child.mkdir()
    original_resolve = Path.resolve
    def resolved(self, *args, **kwargs):
        if self == candidate_root:
            return foreign
        return original_resolve(self, *args, **kwargs)
    def forbidden_read(*args, **kwargs):
        pytest.fail("Escaped ownership must reject before any child artifact read")
    monkeypatch.setattr(Path, "resolve", resolved)
    monkeypatch.setattr(runner, "_read", forbidden_read)
    with pytest.raises(ValueError, match="outside its owned"):
        runner._candidate_record(child, candidate_root, group, None, None, {}, [], "", "", [])


def test_interruption_retains_partial_inventory_and_no_complete_summary(setup, monkeypatch):
    attempted = 0
    def interrupted(*args):
        nonlocal attempted
        attempted += 1
        if attempted == 2:
            raise KeyboardInterrupt()
        return setup.child(*args)
    monkeypatch.setattr(runner, "run_walk_forward", interrupted)
    with pytest.raises(KeyboardInterrupt):
        runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    group, = setup.output.iterdir()
    assert [row["status"] for row in read(group / "candidates.json")] == ["completed", "interrupted", "pending", "pending"]
    status = read(group / "status.json")
    assert status["state"] == "interrupted"
    assert status["coverage_complete"] is False
    assert status["terminal_candidates"] == 1
    assert not (group / "report.json").exists()


@pytest.mark.parametrize("filename,key", [("status.json", "state"), ("manifest.json", "config"), ("report.json", "cost_bps")])
def test_duplicate_owned_artifact_fields_are_invalid(setup, monkeypatch, filename, key):
    def ambiguous(*args):
        directory = setup.child(*args)
        payload = read(directory / filename)
        raw = (directory / filename).read_text(encoding="utf-8")
        (directory / filename).write_text(raw[:-1] + ', ' + json.dumps(key) + ': ' + json.dumps(payload[key]) + '}', encoding="utf-8")
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", ambiguous)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    report = read(group / "report.json")
    assert report["invalid"] == 4
    assert report["completed"] == 0


@pytest.mark.parametrize("token", ["NaN", "Infinity", "1e9999"])
def test_nonfinite_unused_artifact_field_cannot_bypass_validation(setup, monkeypatch, token):
    def ambiguous(*args):
        directory = setup.child(*args)
        raw = (directory / "report.json").read_text(encoding="utf-8")
        (directory / "report.json").write_text(raw[:-1] + ', "unused": ' + token + '}', encoding="utf-8")
        return directory
    monkeypatch.setattr(runner, "run_walk_forward", ambiguous)
    group = runner.run_sweep(setup.manifest, setup.config, setup.settings, setup.output)
    assert read(group / "report.json")["invalid"] == 4
