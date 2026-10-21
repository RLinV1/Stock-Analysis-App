"""Actual-file causality/snapshot regressions, drafted without execution."""

import csv
import json
import shutil

import numpy as np
import pytest
import torch

from portfolio_lab import walk_forward
from portfolio_lab.data import file_hash, load_dataset, synthetic_dataset
from portfolio_lab.protocol import plan_walk_forward
from portfolio_lab.walk_forward import WalkForwardConfig, run_walk_forward


def fixture(tmp_path):
    path = synthetic_dataset(tmp_path / "original", 1000)
    data = load_dataset(path)
    config = WalkForwardConfig(str(data.dates[330]), str(data.dates[-1]),
                               lookback=10, hidden_size=8, epochs=1, batch_size=64,
                               learning_rate=.001, seed=7, cost_bps=1, device="cpu")
    return path, data, config


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def changed_future_copy(path, destination, boundary):
    """Alter only future prices and update the manifest's exact CSV hash references.

    Using the recorded digest, rather than guessing a manifest field name,
    preserves unrelated metadata. The public loader must validate the result.
    """
    dataset = load_dataset(path)
    shutil.copytree(path.parent, destination)
    copied_manifest = destination / path.name
    csv_path = destination / dataset.manifest["csv"]
    original_hash = file_hash(csv_path)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    column = rows[0].index(dataset.symbols[0])
    for index, row in enumerate(rows[1:]):
        if index >= boundary:
            row[column] = format(float(row[column]) * (1.01 + (index - boundary) * .002), ".17g")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    new_hash = file_hash(csv_path)
    assert new_hash != original_hash
    replacements = 0
    def rehash(value):
        nonlocal replacements
        if isinstance(value, dict):
            return {key: rehash(child) for key, child in value.items()}
        if isinstance(value, list):
            return [rehash(child) for child in value]
        if value == original_hash:
            replacements += 1
            return new_hash
        return value
    manifest = rehash(read(copied_manifest))
    assert replacements > 0, "Validated dataset manifest must record its CSV digest"
    copied_manifest.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    changed = load_dataset(copied_manifest)
    np.testing.assert_array_equal(changed.prices[:boundary], dataset.prices[:boundary])
    assert not np.array_equal(changed.prices[boundary:], dataset.prices[boundary:])
    return copied_manifest


def lstm_rows(path, before_date):
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))[1:]
    return [row for row in rows if row[1] == "lstm" and row[0] < before_date]


@pytest.mark.parametrize("mutation_position", ["inside_first_fold", "after_first_fold"])
def test_on_disk_future_changes_preserve_first_model_scaler_and_earlier_predictions(tmp_path, mutation_position):
    path, dataset, config = fixture(tmp_path)
    plan = plan_walk_forward(dataset.dates, config.test_start, config.test_end, lookback=config.lookback)
    boundary = (plan.folds[0].test_indices[20] if mutation_position == "inside_first_fold"
                else plan.folds[0].test_indices[-1] + 1)
    altered_path = changed_future_copy(path, tmp_path / "altered", boundary)
    reference = run_walk_forward(path, config, tmp_path / "runs")
    altered = run_walk_forward(altered_path, config, tmp_path / "runs")
    before_record = read(reference / "folds.json")["completed_folds"][0]
    after_record = read(altered / "folds.json")["completed_folds"][0]
    before_run, after_run = reference / before_record["run_directory"], altered / after_record["run_directory"]
    before = torch.load(before_run / "model.pt", weights_only=True)
    after = torch.load(after_run / "model.pt", weights_only=True)
    for key in before["model"]:
        torch.testing.assert_close(before["model"][key], after["model"][key], rtol=0, atol=0)
    torch.testing.assert_close(before["mean"], after["mean"], rtol=0, atol=0)
    torch.testing.assert_close(before["scale"], after["scale"], rtol=0, atol=0)
    assert lstm_rows(before_run / "allocations.csv", str(dataset.dates[boundary])) == lstm_rows(
        after_run / "allocations.csv", str(dataset.dates[boundary]))
    if mutation_position == "after_first_fold":
        assert read(before_run / "report.json")["strategies"] == read(after_run / "report.json")["strategies"]
    # Distinct file inputs must retain distinct identities despite invariant fitting.
    assert read(reference / "manifest.json")["identity_sha256"] != read(altered / "manifest.json")["identity_sha256"]


def test_later_folds_use_snapshot_when_original_input_changes(tmp_path, monkeypatch):
    path, data, config = fixture(tmp_path)
    original_csv = path.parent / data.manifest["csv"]
    original_hash = file_hash(original_csv)
    real = walk_forward.run_experiment
    calls = 0
    def mutate_original_after_first_fold(*args, **kwargs):
        nonlocal calls
        result = real(*args, **kwargs)
        calls += 1
        if calls == 1:
            original_csv.write_text("Deliberately invalid original after snapshot\n", encoding="utf-8")
        return result
    monkeypatch.setattr(walk_forward, "run_experiment", mutate_original_after_first_fold)
    group = run_walk_forward(path, config, tmp_path / "runs")
    assert calls >= 2
    assert read(group / "status.json")["state"] == "completed"
    assert file_hash(group / "dataset" / data.manifest["csv"]) == original_hash
    assert file_hash(original_csv) != original_hash
