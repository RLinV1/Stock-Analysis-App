"""Future CPU integration gate; written only, not executed during GPU workload."""

import json

import torch

from portfolio_lab.data import file_hash, load_dataset, synthetic_dataset
from portfolio_lab.sweep import SweepSettings
from portfolio_lab.sweep_runner import SweepModelConfig, run_sweep


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_sweep_consumes_nested_walk_forward_results(tmp_path):
    manifest = synthetic_dataset(tmp_path / "data", observations=420)
    dataset = load_dataset(manifest)
    config = SweepModelConfig(
        test_start=str(dataset.dates[330]), test_end=str(dataset.dates[334]),
        lookback=10, hidden_size=4, epochs=1, batch_size=64,
        learning_rate=0.001, device="cpu",
    )
    settings = SweepSettings(seeds=(7,), costs_bps=(0, 1), max_runs=2)
    group = run_sweep(manifest, config, settings, tmp_path / "runs")
    status = read(group / "status.json")
    assert status["state"] == "completed"
    assert status["coverage_complete"] is True
    assert status["all_successful"] is True
    assert status["planned_fold_runs"] == 2
    assert status["terminal_candidates"] == 2
    report, inventory = read(group / "report.json"), read(group / "candidates.json")
    expected_dates = dataset.dates[330:335].tolist()
    assert report["context"]["test_dates"] == expected_dates
    assert report["context"]["method_label"] == "synthetic-walk-forward"
    assert len(inventory) == 2
    assert report["objective"]["transaction_costs"] == "evaluation_only"
    saved_models, histories = [], []
    for row, cost_summary in zip(inventory, report["by_cost"]):
        child = group / row["run_directory"]
        child_report, child_status = read(child / "report.json"), read(child / "status.json")
        assert child_report["objective"] == report["objective"]
        fold, = child_report["folds"]
        fold_directory = child / fold["run_directory"]
        saved_models.append(torch.load(fold_directory / "model.pt", map_location="cpu", weights_only=True))
        histories.append(read(fold_directory / "report.json")["history"])
        assert child_status["completed_folds"] == child_status["fold_budget"] == 1
        assert child_report["test_dates"] == expected_dates
        assert row["report_sha256"] == file_hash(child / "report.json")
        assert row["manifest_sha256"] == file_hash(child / "manifest.json")
        for strategy, result in child_report["strategies"].items():
            assert row["strategies"][strategy] == result["metrics"]
            assert result["metrics"]["observations"] == 5
            assert len(result["wealth"]) == 5
            for name, distribution in cost_summary["strategies"][strategy].items():
                value = result["metrics"][name]
                if value is None:
                    assert distribution["mean"] is None
                    assert distribution["numeric_count"] == 0
                    assert distribution["null_count"] == 1
                else:
                    assert distribution["mean"] == value
                    assert distribution["population_std"] == 0.0
                    assert distribution["numeric_count"] == 1
                    assert distribution["null_count"] == 0
    # Costs currently alter accounting, not this method's fit or model selection.
    assert histories[0] == histories[1]
    for name, tensor in saved_models[0]["model"].items():
        torch.testing.assert_close(tensor, saved_models[1]["model"][name], rtol=0, atol=0)
    for name in ("mean", "scale"):
        torch.testing.assert_close(saved_models[0][name], saved_models[1][name], rtol=0, atol=0)
