import json
from dataclasses import replace

import numpy as np
import pytest
import torch
from filelock import FileLock, Timeout

from portfolio_lab.data import load_dataset, synthetic_dataset, write_dataset
from portfolio_lab.runner import RunConfig, run_experiment


def fixture(tmp_path):
    path = synthetic_dataset(tmp_path / "data", 140)
    d = load_dataset(path)
    cfg = RunConfig(str(d.dates[90]), str(d.dates[110]), lookback=10, hidden_size=8, epochs=4, batch_size=32)
    return path, d, cfg


def read_json(path):
    return json.loads(path.read_text())


def test_epoch_resume_matches_uninterrupted_training(tmp_path):
    path, _, cfg = fixture(tmp_path)
    full = run_experiment(path, cfg, tmp_path / "runs")
    partial = run_experiment(path, cfg, tmp_path / "runs", stop_after_epochs=2)
    before = (partial / "manifest.json").read_bytes()
    assert read_json(partial / "status.json")["state"] == "paused"
    assert not (partial / "report.json").exists()
    run_experiment(path, cfg, tmp_path / "runs", resume=partial)
    assert (partial / "manifest.json").read_bytes() == before
    a, b = read_json(full / "report.json"), read_json(partial / "report.json")
    assert a["history"] == b["history"]
    assert a["strategies"] == b["strategies"]
    assert read_json(partial / "status.json")["state"] == "completed"
    saved = torch.load(partial / "model.pt", weights_only=True)
    assert saved["mean"].numel() == 6
    np.testing.assert_array_equal(load_dataset(partial / "dataset" / "manifest.json").prices,
                                  load_dataset(path).prices)
    with pytest.raises(ValueError, match="immutable"):
        run_experiment(path, cfg, tmp_path / "runs", resume=partial)


def test_checkpoint_mismatch_and_concurrent_access(tmp_path):
    path, _, cfg = fixture(tmp_path)
    run = run_experiment(path, cfg, tmp_path / "runs", stop_after_epochs=1)
    status_before = (run / "status.json").read_bytes()
    with pytest.raises(ValueError, match="mismatch"):
        run_experiment(path, replace(cfg, seed=9), tmp_path / "runs", resume=run)
    assert (run / "status.json").read_bytes() == status_before
    with FileLock(str(run / ".run.lock")):
        with pytest.raises(Timeout):
            run_experiment(path, cfg, tmp_path / "runs", resume=run)


def test_heldout_prices_cannot_change_trained_model(tmp_path):
    path, dataset, cfg = fixture(tmp_path)
    original = run_experiment(path, cfg, tmp_path / "runs")
    dataset.prices[111:] *= np.linspace(1, 3, len(dataset.prices) - 111)[:, None]
    manifest = dataset.manifest
    changed_path = write_dataset(tmp_path / "changed", dataset.dates.tolist(), dataset.prices,
                                 manifest["assets"], kind="synthetic", source="test perturbation",
                                 license_note="test fixture", adjustment="none",
                                 deviations=["held-out future mutation"])
    changed = run_experiment(changed_path, cfg, tmp_path / "runs")
    a = torch.load(original / "model.pt", weights_only=True)["model"]
    b = torch.load(changed / "model.pt", weights_only=True)["model"]
    for name in a:
        torch.testing.assert_close(a[name], b[name], rtol=0, atol=0)
    assert read_json(original / "report.json")["history"] == read_json(changed / "report.json")["history"]
    assert read_json(original / "report.json")["strategies"] != read_json(changed / "report.json")["strategies"]


def test_invalid_config_does_not_create_run(tmp_path):
    path, _, cfg = fixture(tmp_path)
    with pytest.raises(ValueError):
        run_experiment(path, replace(cfg, epochs=0), tmp_path / "runs")
    assert not (tmp_path / "runs").exists()
