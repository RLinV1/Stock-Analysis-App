"""Unrun model-free producer cases for owned fold accounting consistency.

The child model file is only a hashable stub; these tests make no model-replay or
artifact-authenticity claim. Real producer compatibility is a separate gate.
"""

import csv
import json
from dataclasses import asdict

import numpy as np
import pytest

from portfolio_lab import walk_forward
from portfolio_lab.data import load_dataset, save_json, synthetic_dataset
from portfolio_lab.metrics import baseline_weights, evaluate
from portfolio_lab.protocol import make_fold_samples
from portfolio_lab.walk_forward import WalkForwardConfig, run_walk_forward


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def produced(tmp_path, monkeypatch):
    manifest = synthetic_dataset(tmp_path / "data", observations=420)
    dataset = load_dataset(manifest)
    config = WalkForwardConfig(str(dataset.dates[330]), str(dataset.dates[334]),
                               10, 4, 1, 64, 0.001, 7, 10, "cpu")
    calls = []
    monkeypatch.setattr(walk_forward, "source_revision", lambda: {"test_stub": True})

    def child(dataset_path, selected, output, *, fold):
        owned = load_dataset(dataset_path)
        samples = make_fold_samples(owned, fold)
        returns = samples.y[samples.test]
        count = len(fold.test_indices)
        portfolios = {"lstm": np.tile([0.2, 0.3, 0.5], (count, 1)),
                      **baseline_weights(owned.manifest["assets"], count)}
        directory = output / "stub"
        directory.mkdir(parents=True)
        parent = read(output.parent.parent / "manifest.json")
        save_json(directory / "manifest.json", {
            **{key: parent[key] for key in ("dataset_manifest_sha256", "source_sha256", "versions")},
            "evaluation_protocol": {"kind": "expanding-walk-forward-fold", "fold": asdict(fold)},
            "config": asdict(selected), "method_label": "synthetic-smoke",
            "conventions": walk_forward.CONVENTIONS, "objective": walk_forward.OBJECTIVE_CONVENTIONS,
            "deviations": ["Model-free accounting fixture; no learned-model evidence"],
        })
        save_json(directory / "status.json", {"state": "completed"})
        save_json(directory / "report.json", {
            "test_dates": owned.dates[list(fold.test_indices)].tolist(), "cost_bps": selected.cost_bps,
            "method_label": "synthetic-smoke", "conventions": walk_forward.CONVENTIONS,
            "objective": walk_forward.OBJECTIVE_CONVENTIONS, "baseline_omissions": [],
            "strategies": {name: evaluate(weights, returns, selected.cost_bps,
                                           allow_single_observation=True)
                           for name, weights in portfolios.items()},
        })
        with (directory / "allocations.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["return_date", "strategy", *owned.symbols])
            for name, weights in portfolios.items():
                writer.writerows([day, name, *row.tolist()]
                                 for day, row in zip(owned.dates[list(fold.test_indices)], weights))
        (directory / "model.pt").write_bytes(b"Hashable stub; never load as a model")
        calls.append(directory)
        return directory

    monkeypatch.setattr(walk_forward, "run_experiment", child)
    return manifest, config, child, calls


def test_consistent_owned_accounting_can_complete_without_model_execution(tmp_path, produced):
    manifest, config, _, calls = produced
    group = run_walk_forward(manifest, config, tmp_path / "runs")
    assert len(calls) == 1
    assert read(group / "status.json")["state"] == "completed"
    aggregate, child = read(group / "report.json"), read(calls[0] / "report.json")
    assert aggregate["strategies"] == child["strategies"]
    assert aggregate["folds"][0]["deviations"] == ["Model-free accounting fixture; no learned-model evidence"]


@pytest.mark.parametrize("case", ["metric", "gross", "net", "cost", "turnover", "wealth",
                                   "missing_metrics", "extra_field", "float_observations",
                                   "bool_observations", "null_reason", "empty_result"])
def test_inconsistent_owned_accounting_prevents_group_completion(tmp_path, monkeypatch, produced, case):
    manifest, config, child, _ = produced
    def tampered(*args, **kwargs):
        directory = child(*args, **kwargs)
        report = read(directory / "report.json")
        result = report["strategies"]["lstm"]
        paths = {"gross": "gross_returns", "net": "net_returns", "cost": "costs",
                 "turnover": "turnover", "wealth": "wealth"}
        if case == "metric":
            result["metrics"]["cumulative_return"] += 0.001
        elif case in paths:
            result[paths[case]][0] += 0.001
        elif case == "missing_metrics":
            del result["metrics"]
        elif case == "extra_field":
            result["unrecognized_account"] = 1
        elif case == "float_observations":
            result["metrics"]["observations"] = float(result["metrics"]["observations"])
        elif case == "bool_observations":
            result["metrics"]["observations"] = True
        elif case == "null_reason":
            result["metrics"].update(sharpe=None, sharpe_note="Invented explanation")
        else:
            report["strategies"]["lstm"] = {}
        save_json(directory / "report.json", report)
        return directory
    monkeypatch.setattr(walk_forward, "run_experiment", tampered)
    output = tmp_path / "runs"
    with pytest.raises(ValueError, match="reported accounting differs"):
        run_walk_forward(manifest, config, output)
    group, = output.iterdir()
    status = read(group / "status.json")
    assert status["state"] == "failed"
    assert status["completed_folds"] == 0
    assert not (group / "report.json").exists()
    assert not (group / "folds.json").exists()
