import json
from dataclasses import replace

import pytest
import torch

from portfolio_lab import runner
from portfolio_lab.data import load_dataset, synthetic_dataset
from portfolio_lab.runner import RunConfig, RunStopped, run_experiment
from portfolio_lab.service_contract import SCHEMA_PATH, execute_synthetic_request, load_request


def fixture(tmp_path):
    path = synthetic_dataset(tmp_path / "data", 140)
    d = load_dataset(path)
    cfg = RunConfig(str(d.dates[90]), str(d.dates[110]), lookback=10, hidden_size=8, epochs=4, batch_size=32)
    return path, cfg


def read_json(path):
    return json.loads(path.read_text())


def stop_after(boundaries):
    """Return False for the first `boundaries` checks, then True."""
    calls = []

    def should_stop():
        calls.append(None)
        return len(calls) > boundaries

    return should_stop


def test_stop_after_first_epoch_pauses_with_checkpoint_and_resumes_identically(tmp_path):
    path, cfg = fixture(tmp_path)
    full = run_experiment(path, cfg, tmp_path / "runs")
    with pytest.raises(RunStopped) as stopped:
        run_experiment(path, cfg, tmp_path / "runs", should_stop=stop_after(1))
    run = stopped.value.run_dir
    assert stopped.value.epoch == 1
    assert read_json(run / "status.json") == {"state": "paused", "epoch": 1, "epoch_budget": 4,
                                              "reason": "stop_requested"}
    assert not (run / "report.json").exists()
    assert not (run / "model.pt").exists()
    assert torch.load(run / "checkpoint.pt", weights_only=True)["epoch"] == 1
    before = (run / "manifest.json").read_bytes()
    run_experiment(path, cfg, tmp_path / "runs", resume=run)
    assert (run / "manifest.json").read_bytes() == before
    assert read_json(run / "status.json")["state"] == "completed"
    a, b = read_json(full / "report.json"), read_json(run / "report.json")
    assert a["history"] == b["history"]
    assert a["strategies"] == b["strategies"]


def test_stop_before_first_epoch_writes_no_checkpoint(tmp_path):
    path, cfg = fixture(tmp_path)
    with pytest.raises(RunStopped) as stopped:
        run_experiment(path, cfg, tmp_path / "runs", should_stop=lambda: True)
    run = stopped.value.run_dir
    assert stopped.value.epoch == 0
    assert read_json(run / "status.json")["state"] == "paused"
    assert read_json(run / "status.json")["epoch"] == 0
    assert not (run / "checkpoint.pt").exists()
    assert not (run / "report.json").exists()


def test_false_stop_check_matches_default_run(tmp_path):
    path, cfg = fixture(tmp_path)
    default = run_experiment(path, cfg, tmp_path / "runs")
    checked = run_experiment(path, cfg, tmp_path / "runs", should_stop=lambda: False)
    assert read_json(checked / "status.json")["state"] == "completed"
    a, b = read_json(default / "report.json"), read_json(checked / "report.json")
    assert a["history"] == b["history"]
    assert a["strategies"] == b["strategies"]
    assert read_json(default / "manifest.json")["identity_sha256"] == \
        read_json(checked / "manifest.json")["identity_sha256"]


def test_service_request_passes_stop_check_through(tmp_path):
    request = load_request(SCHEMA_PATH.parent / "examples" / "synthetic-smoke.v1.json")
    with pytest.raises(RunStopped) as stopped:
        execute_synthetic_request(request, tmp_path / "runs", should_stop=lambda: True)
    run = stopped.value.run_dir
    assert read_json(run / "status.json")["state"] == "paused"
    assert not (run / "report.json").exists()
    assert not (run / "request.json").exists()
    assert len(list((tmp_path / "runs").glob(".synthetic-input-*"))) == 0


def test_final_epoch_boundary_stop_retains_checkpoint_and_resumes_identically(tmp_path):
    path, cfg = fixture(tmp_path)
    cfg = replace(cfg, epochs=1)
    reference = run_experiment(path, cfg, tmp_path / "runs")
    with pytest.raises(RunStopped) as stopped:
        run_experiment(path, cfg, tmp_path / "runs", should_stop=stop_after(1))
    run = stopped.value.run_dir
    assert stopped.value.epoch == 1
    assert read_json(run / "status.json") == {"state": "paused", "epoch": 1, "epoch_budget": 1,
                                               "reason": "stop_requested"}
    assert torch.load(run / "checkpoint.pt", weights_only=True)["epoch"] == 1
    for name in ("report.json", "model.pt", "allocations.csv"):
        assert not (run / name).exists()
    checkpoint, manifest = (run / "checkpoint.pt").read_bytes(), (run / "manifest.json").read_bytes()
    run_experiment(path, cfg, tmp_path / "runs", resume=run)
    assert (run / "checkpoint.pt").read_bytes() == checkpoint
    assert (run / "manifest.json").read_bytes() == manifest
    assert read_json(run / "status.json")["state"] == "completed"
    assert read_json(run / "report.json")["history"] == read_json(reference / "report.json")["history"]
    assert read_json(run / "report.json")["strategies"] == read_json(reference / "report.json")["strategies"]


def test_limited_epoch_chunk_checks_its_final_checkpoint(tmp_path):
    path, cfg = fixture(tmp_path)
    with pytest.raises(RunStopped) as stopped:
        run_experiment(path, cfg, tmp_path / "runs", stop_after_epochs=1, should_stop=stop_after(1))
    run = stopped.value.run_dir
    assert stopped.value.epoch == 1
    assert read_json(run / "status.json")["reason"] == "stop_requested"
    assert torch.load(run / "checkpoint.pt", weights_only=True)["epoch"] == 1
    assert not (run / "report.json").exists()


def test_missing_checkpoint_resume_preserves_paused_evidence(tmp_path, monkeypatch):
    path, cfg = fixture(tmp_path)
    with pytest.raises(RunStopped) as stopped:
        run_experiment(path, cfg, tmp_path / "runs", should_stop=lambda: True)
    run = stopped.value.run_dir
    manifest, status = (run / "manifest.json").read_bytes(), (run / "status.json").read_bytes()
    def forbidden(*args, **kwargs):
        pytest.fail("Missing-checkpoint resume must reject before training")
    monkeypatch.setattr(runner, "_train", forbidden)
    with pytest.raises(ValueError, match="no completed-epoch checkpoint"):
        run_experiment(path, cfg, tmp_path / "runs", resume=run)
    assert (run / "manifest.json").read_bytes() == manifest
    assert (run / "status.json").read_bytes() == status
    assert not (run / "checkpoint.pt").exists()
    assert not (run / "report.json").exists()


def test_service_final_boundary_stop_has_no_completed_request_artifacts(tmp_path):
    request = load_request(SCHEMA_PATH.parent / "examples" / "synthetic-smoke.v1.json")
    request["model"]["epochs"] = 1
    with pytest.raises(RunStopped) as stopped:
        execute_synthetic_request(request, tmp_path / "runs", should_stop=stop_after(1))
    run = stopped.value.run_dir
    assert stopped.value.epoch == 1
    assert (run / "checkpoint.pt").exists()
    assert read_json(run / "status.json")["reason"] == "stop_requested"
    for name in ("report.json", "model.pt", "request.json", "request.sha256"):
        assert not (run / name).exists()
    assert not list((tmp_path / "runs").glob(".synthetic-input-*"))
