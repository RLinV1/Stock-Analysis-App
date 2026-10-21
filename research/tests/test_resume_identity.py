"""Unrun saved-metadata rejection cases; no extra fit per mutation."""

import json
import shutil
from dataclasses import replace

import pytest

from portfolio_lab import runner
from portfolio_lab.data import load_dataset, save_json, synthetic_dataset
from portfolio_lab.runner import RunConfig, run_experiment


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot(directory):
    return {path.relative_to(directory).as_posix(): path.read_bytes()
            for path in directory.rglob("*") if path.is_file()}


@pytest.fixture(scope="module")
def paused(tmp_path_factory):
    directory = tmp_path_factory.mktemp("resume-metadata")
    manifest = synthetic_dataset(directory / "data", observations=140)
    dataset = load_dataset(manifest)
    config = RunConfig(str(dataset.dates[90]), str(dataset.dates[110]),
                       lookback=10, hidden_size=4, epochs=2, batch_size=64, device="cpu")
    run = run_experiment(manifest, config, directory / "runs", stop_after_epochs=1)
    return manifest, config, run


@pytest.mark.parametrize("case", ["config", "config_type", "dataset", "source", "versions",
                                   "objective", "conventions", "method", "schema", "protocol",
                                   "duplicate_manifest", "duplicate_status", "unknown_state"])
def test_stale_hash_or_ambiguous_resume_metadata_rejects_before_training(
        tmp_path, monkeypatch, paused, case):
    dataset_path, config, reference = paused
    run = tmp_path / "paused-copy"
    shutil.copytree(reference, run)
    manifest_path = run / "manifest.json"
    manifest = read(manifest_path)
    original_digest = manifest["identity_sha256"]
    if case == "duplicate_manifest":
        raw = manifest_path.read_text(encoding="utf-8").rstrip()
        manifest_path.write_text(raw[:-1] + ', "schema_version": 1}', encoding="utf-8")
    elif case == "duplicate_status":
        (run / "status.json").write_text('{"state":"paused","state":"paused"}', encoding="utf-8")
    elif case == "unknown_state":
        save_json(run / "status.json", {"state": "unrecognized"})
    else:
        if case == "config":
            manifest["config"]["seed"] += 1
        elif case == "config_type":
            manifest["config"]["epochs"] = float(manifest["config"]["epochs"])
        elif case == "dataset":
            manifest["dataset"]["source"] = "Edited source label"
        elif case == "source":
            manifest["source_sha256"] = "0" * 64
        elif case == "versions":
            manifest["versions"]["torch"] = "different-runtime"
        elif case == "objective":
            manifest["objective"]["transaction_costs"] = "included_in_training"
        elif case == "conventions":
            manifest["conventions"]["risk_free_rate"] = False
        elif case == "method":
            manifest["method_label"] = "paper-inspired"
        elif case == "schema":
            manifest["schema_version"] = True
        else:
            manifest["evaluation_protocol"] = {"kind": "unexpected-fold"}
        save_json(manifest_path, manifest)
    assert read(manifest_path)["identity_sha256"] == original_digest
    before, reference_before = snapshot(run), snapshot(reference)
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid saved metadata must reject before training/checkpoint loading")
    monkeypatch.setattr(runner, "_train", forbidden)
    with pytest.raises(ValueError):
        run_experiment(dataset_path, config, tmp_path / "unused-output", resume=run)
    assert snapshot(run) == before
    assert snapshot(reference) == reference_before
    assert not (tmp_path / "unused-output").exists()


def test_unchanged_resume_metadata_still_reaches_training(tmp_path, monkeypatch, paused):
    dataset_path, config, reference = paused
    run = tmp_path / "paused-copy"
    shutil.copytree(reference, run)
    calls = []
    monkeypatch.setattr(runner, "_train", lambda *args, **kwargs: calls.append((args, kwargs)))
    assert run_experiment(dataset_path, config, tmp_path / "unused-output", resume=run) == run.resolve()
    assert len(calls) == 1


def test_changed_requested_inputs_remain_rejected(tmp_path, monkeypatch, paused):
    dataset_path, config, reference = paused
    before = snapshot(reference)
    monkeypatch.setattr(runner, "_train", lambda *args, **kwargs: pytest.fail("Must reject changed request"))
    with pytest.raises(ValueError, match="mismatch"):
        run_experiment(dataset_path, replace(config, seed=config.seed + 1), tmp_path / "unused-output", resume=reference)
    assert snapshot(reference) == before
