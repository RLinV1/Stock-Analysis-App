"""Unrun fold artifact boundary cases with stub training and forbidden aggregation."""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from portfolio_lab import walk_forward
from portfolio_lab.data import load_dataset, synthetic_dataset
from portfolio_lab.walk_forward import WalkForwardConfig, run_walk_forward


def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def guarded(tmp_path, monkeypatch):
    manifest = synthetic_dataset(tmp_path / "data", observations=420)
    data = load_dataset(manifest)
    config = WalkForwardConfig(str(data.dates[330]), str(data.dates[334]), 10, 4, 1, 64, 0.001, 7, 0, "cpu")
    monkeypatch.setattr(walk_forward, "source_revision", lambda: {"test_stub": True})
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid child must fail before allocations are read or aggregated")
    monkeypatch.setattr(walk_forward, "_allocations", forbidden)

    def child(dataset_path, selected, fold_root, *, fold):
        directory = fold_root / "stub"
        directory.mkdir(parents=True)
        parent = read(fold_root.parent.parent / "manifest.json")
        write(directory / "manifest.json", {
            **{key: parent[key] for key in ("dataset_manifest_sha256", "source_sha256", "versions")},
            "evaluation_protocol": {"kind": "expanding-walk-forward-fold", "fold": asdict(fold)},
            "config": asdict(selected), "method_label": "synthetic-smoke",
            "conventions": walk_forward.CONVENTIONS, "deviations": ["stub child"],
            "objective": walk_forward.OBJECTIVE_CONVENTIONS,
        })
        write(directory / "status.json", {"state": "completed"})
        write(directory / "report.json", {
            "test_dates": data.dates[list(fold.test_indices)].tolist(), "cost_bps": selected.cost_bps,
            "method_label": "synthetic-smoke", "conventions": walk_forward.CONVENTIONS,
            "objective": walk_forward.OBJECTIVE_CONVENTIONS,
            "strategies": {"lstm": {}, "equal_weight": {}, "stock_bond_60_40": {}},
            "baseline_omissions": [],
        })
        return directory

    monkeypatch.setattr(walk_forward, "run_experiment", child)
    return manifest, config, child


@pytest.mark.parametrize("target,mutation", [
    ("manifest.json", "config_boolean"), ("manifest.json", "fold_boolean"),
    ("manifest.json", "convention_boolean"), ("manifest.json", "wrong_method"),
    ("report.json", "convention_boolean"), ("report.json", "wrong_method"),
    ("report.json", "boolean_cost"), ("report.json", "missing_lstm"),
    ("report.json", "reordered_strategies"),
    ("manifest.json", "wrong_objective"), ("report.json", "wrong_objective"),
    ("report.json", "omission_object"), ("report.json", "omission_none"),
    ("report.json", "wrong_omission"), ("report.json", "missing_omissions"),
])
def test_child_context_rejection_precedes_allocation_reads(tmp_path, monkeypatch, guarded, target, mutation):
    manifest, config, child = guarded
    def tampered(*args, **kwargs):
        directory = child(*args, **kwargs)
        payload = read(directory / target)
        if mutation == "config_boolean":
            payload["config"]["epochs"] = True
        elif mutation == "fold_boolean":
            payload["evaluation_protocol"]["fold"]["number"] = False
        elif mutation == "convention_boolean":
            payload["conventions"]["risk_free_rate"] = False
        elif mutation == "wrong_method":
            payload["method_label"] = "unverified-historical-proof"
        elif mutation == "boolean_cost":
            payload["cost_bps"] = False
        elif mutation == "missing_lstm":
            del payload["strategies"]["lstm"]
        elif mutation == "wrong_objective":
            payload["objective"]["transaction_costs"] = "included_in_training"
        elif mutation == "missing_omissions":
            del payload["baseline_omissions"]
        elif mutation.startswith("omission_") or mutation == "wrong_omission":
            payload["baseline_omissions"] = {
                "omission_object": {}, "omission_none": None,
                "wrong_omission": ["60/40 unavailable: missing stock/bond roles"],
            }[mutation]
        else:
            payload["strategies"] = {"equal_weight": {}, "lstm": {}, "stock_bond_60_40": {}}
        write(directory / target, payload)
        return directory
    monkeypatch.setattr(walk_forward, "run_experiment", tampered)
    output = tmp_path / "runs"
    with pytest.raises(ValueError):
        run_walk_forward(manifest, config, output)
    group, = output.iterdir()
    assert read(group / "status.json")["state"] == "failed"
    assert not (group / "report.json").exists()


@pytest.mark.parametrize("sibling", [False, True])
def test_foreign_or_sibling_directory_is_rejected_before_contents(tmp_path, monkeypatch, guarded, sibling):
    manifest, config, _ = guarded
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "report.json").write_bytes(b"foreign evidence must remain unread")
    forbidden_root = foreign
    def wrong_directory(dataset, selected, fold_root, *, fold):
        nonlocal forbidden_root
        if sibling:
            forbidden_root = fold_root.parent / "different-fold"
            forbidden_root.mkdir(parents=True)
            (forbidden_root / "report.json").write_bytes(b"sibling evidence must remain unread")
        return forbidden_root
    original_read = Path.read_text
    original_read_bytes = Path.read_bytes
    def guarded_read(self, *args, **kwargs):
        if self.resolve().is_relative_to(forbidden_root.resolve()):
            pytest.fail("Must reject the directory before reading foreign child contents")
        return original_read(self, *args, **kwargs)
    def guarded_read_bytes(self, *args, **kwargs):
        if self.resolve().is_relative_to(forbidden_root.resolve()):
            pytest.fail("Must reject the directory before reading foreign child bytes")
        return original_read_bytes(self, *args, **kwargs)
    monkeypatch.setattr(walk_forward, "run_experiment", wrong_directory)
    monkeypatch.setattr(Path, "read_text", guarded_read)
    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    with pytest.raises(ValueError, match="outside its owned"):
        run_walk_forward(manifest, config, tmp_path / "runs")


@pytest.mark.parametrize("filename,key", [("status.json", "state"), ("report.json", "cost_bps"), ("manifest.json", "config")])
def test_duplicate_child_fields_fail_before_aggregation(tmp_path, monkeypatch, guarded, filename, key):
    manifest, config, child = guarded
    def ambiguous(*args, **kwargs):
        directory = child(*args, **kwargs)
        payload = read(directory / filename)
        text = (directory / filename).read_text(encoding="utf-8")
        (directory / filename).write_text(text[:-1] + ', ' + json.dumps(key) + ': ' + json.dumps(payload[key]) + '}', encoding="utf-8")
        return directory
    monkeypatch.setattr(walk_forward, "run_experiment", ambiguous)
    with pytest.raises(ValueError, match="duplicate JSON field"):
        run_walk_forward(manifest, config, tmp_path / "runs")
