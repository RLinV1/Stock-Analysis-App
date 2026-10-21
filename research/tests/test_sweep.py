"""Fixed-answer source cases for explicit sweep summaries; no training needed."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json

import pytest

from portfolio_lab.sweep import Candidate, SweepSettings, plan_candidates, summarize_candidates


def completed(seed=7, cost=0, *, model_return=0.1, baseline_return=0.05, sharpe=1.0):
    def metrics(total, ratio):
        return {
            "observations": 2, "cumulative_return": total,
            "annualized_volatility": 0.2, "sharpe": ratio,
            "sharpe_note": "zero return volatility" if ratio is None else None,
            "max_drawdown": 0.05, "total_turnover": 1.5,
            "total_cost_return_units": 0.001,
        }
    return {
        "seed": seed, "cost_bps": cost, "status": "completed",
        "context": {
            "dataset_sha256": "a" * 64, "settings_sha256": "b" * 64,
            "test_dates": ["2024-01-02", "2024-01-03"],
            "method_label": "synthetic-walk-forward",
        },
        "strategies": {"lstm": metrics(model_return, sharpe), "equal_weight": metrics(baseline_return, 0.5)},
        "run_directory": f"runs/seed-{seed}-cost-{cost}",
    }


def test_plan_retains_caller_order_and_copies_mutable_settings():
    seeds, costs = [19, 3], [5, 0, 2]
    settings = SweepSettings(seeds, costs, 6)
    seeds.append(11)
    costs.reverse()
    assert plan_candidates(settings) == (
        Candidate(19, 5.0), Candidate(19, 0.0), Candidate(19, 2.0),
        Candidate(3, 5.0), Candidate(3, 0.0), Candidate(3, 2.0),
    )
    with pytest.raises(FrozenInstanceError):
        settings.max_runs = 10


@pytest.mark.parametrize("seeds,costs,budget", [
    ([], [0], 1), ([1], [], 1), ([1, 1], [0], 2), ([1], [0, 0.0], 2),
    ([True], [0], 1), ([1.0], [0], 1), ([-1], [0], 1), ([2**32], [0], 1),
    ([1], [True], 1), ([1], [float("nan")], 1), ([1], [float("inf")], 1),
    ([1], [-0.1], 1), ([1], [100.1], 1), ([1], [10**400], 1),
    ([1], [0], True), ([1], [0], 1.5), ([1], [0], 0), ([1, 2], [0, 1], 3),
])
def test_invalid_plan_is_rejected_without_partial_candidates(seeds, costs, budget):
    with pytest.raises(ValueError):
        plan_candidates(SweepSettings(seeds, costs, budget))


@pytest.mark.parametrize("axis", ["seeds", "costs_bps"])
@pytest.mark.parametrize("kind", ["set", "mapping", "generator", "range", "text", "none"])
def test_unordered_or_lazy_axes_are_rejected_without_iteration(axis, kind):
    def forbidden_generator():
        pytest.fail("Settings must reject lazy axes without consuming them")
        yield 7
    values = {"set": {7}, "mapping": {7: "ignored"}, "generator": forbidden_generator(),
              "range": range(1), "text": "7", "none": None}
    arguments = {"seeds": [7], "costs_bps": [0], "max_runs": 1}
    arguments[axis] = values[kind]
    with pytest.raises(ValueError, match="ordered lists or tuples"):
        SweepSettings(**arguments)


def test_over_budget_axes_are_rejected_before_copying():
    class NoIteration(list):
        def __iter__(self):
            pytest.fail("An excess candidate grid must reject before axis copying")
    with pytest.raises(ValueError, match="max_runs"):
        SweepSettings(NoIteration([7, 19]), NoIteration([0, 1]), 3)


def test_invalid_budget_is_rejected_before_copying_axes():
    class NoIteration(list):
        def __iter__(self):
            pytest.fail("An invalid budget must reject before axis copying")
    with pytest.raises(ValueError, match="positive integer"):
        SweepSettings(NoIteration([7]), NoIteration([0]), True)


def test_maximum_seed_and_cost_are_explicit_valid_boundaries():
    assert plan_candidates(SweepSettings((2**32 - 1,), (100,), 1)) == (Candidate(2**32 - 1, 100.0),)


@pytest.mark.parametrize("records", [
    [], [completed(7), completed(7)], [completed(8)],
    [{**completed(), "status": "running"}],
    [{**completed(), "seed": True}], [{**completed(), "cost_bps": True}],
    [{"seed": 7, "cost_bps": 0, "status": "failed"}],
    [{"seed": 7, "cost_bps": 0, "status": "invalid", "reason": " "}],
])
def test_summary_requires_exact_terminal_coverage(records):
    with pytest.raises(ValueError):
        summarize_candidates(SweepSettings((7,), (0,), 1), records)


def test_null_sharpe_is_counted_separately_and_never_becomes_zero():
    settings = SweepSettings((3, 7, 19), (0,), 3)
    records = [completed(19, model_return=0.5, sharpe=4), completed(3, sharpe=None),
               completed(7, model_return=0.3, sharpe=2)]
    before = deepcopy(records)
    report = summarize_candidates(settings, records)
    assert records == before
    assert [row["seed"] for row in report["records"]] == [3, 7, 19]
    assert report["all_successful"] is True
    ratios = report["by_cost"][0]["strategies"]["lstm"]["sharpe"]
    assert ratios == {
        "numeric_count": 2, "null_count": 1,
        "null_reasons": {"zero return volatility": 1},
        "mean": 3.0, "population_std": 1.0, "min": 2.0, "max": 4.0,
    }
    returns = report["by_cost"][0]["strategies"]["lstm"]["cumulative_return"]
    assert returns["mean"] == pytest.approx(0.3)
    assert returns["population_std"] == pytest.approx((0.08 / 3) ** 0.5)
    json.dumps(report, allow_nan=False)


def test_all_null_sharpe_has_no_numeric_mean_or_deviation():
    report = summarize_candidates(SweepSettings((7,), (0,), 1), [completed(sharpe=None)])
    ratios = report["by_cost"][0]["strategies"]["lstm"]["sharpe"]
    assert ratios["numeric_count"] == 0
    assert ratios["null_count"] == 1
    assert all(ratios[key] is None for key in ("mean", "population_std", "min", "max"))


def test_failed_and_invalid_cells_are_retained_in_declared_order():
    records = [completed(7, 5),
               {"seed": 3, "cost_bps": 5, "status": "invalid", "reason": "nonfinite model output"},
               {"seed": 7, "cost_bps": 0, "status": "failed", "reason": "training failed"},
               completed(3, 0)]
    report = summarize_candidates(SweepSettings((7, 3), (5, 0), 4), records)
    assert report["coverage_complete"] is True
    assert report["all_successful"] is False
    assert (report["requested"], report["completed"], report["failed"], report["invalid"]) == (4, 2, 1, 1)
    assert [row["status"] for row in report["records"]] == ["completed", "failed", "invalid", "completed"]
    assert [row["cost_bps"] for row in report["by_cost"]] == [5.0, 0.0]
    assert report["records"][1]["reason"] == "training failed"
    assert report["by_cost"][0]["invalid"] == 1
    assert report["by_cost"][1]["failed"] == 1
    assert all(row["outcome"] == "unavailable" for row in report["tested_cost_intervals"])


def test_all_failed_grid_reports_no_invented_metrics_or_context():
    report = summarize_candidates(SweepSettings((7,), (0,), 1), [
        {"seed": 7, "cost_bps": 0, "status": "failed", "reason": "training failed"},
    ])
    assert report["completed"] == 0
    assert report["context"] is None
    assert report["by_cost"][0]["strategies"] == {}
    assert report["tested_cost_intervals"] == []
    assert report["records"][0]["reason"] == "training failed"


def test_tested_intervals_are_sorted_adjacent_and_do_not_interpolate():
    settings = SweepSettings((7,), (10, 0, 5, 20), 4)
    report = summarize_candidates(settings, [
        completed(7, 0, model_return=0.2, baseline_return=0.1),
        completed(7, 5, model_return=0.05, baseline_return=0.1),
        completed(7, 10, model_return=0.1, baseline_return=0.1),
        completed(7, 20, model_return=0.3, baseline_return=0.1),
    ])
    intervals = report["tested_cost_intervals"]
    assert [(row["low_cost_bps"], row["high_cost_bps"]) for row in intervals] == [(0, 5), (5, 10), (10, 20)]
    assert [row["outcome"] for row in intervals] == ["sign_change", "tie_at_tested_cost", "tie_at_tested_cost"]
    assert intervals[0]["return_differences"] == pytest.approx([0.1, -0.05])
    assert not any("threshold" in key for row in intervals for key in row)


def test_failed_middle_cost_is_not_skipped_to_find_a_favorable_interval():
    report = summarize_candidates(SweepSettings((7,), (0, 5, 10), 3), [
        completed(7, 0, model_return=0.2),
        {"seed": 7, "cost_bps": 5, "status": "failed", "reason": "training failed"},
        completed(7, 10, model_return=-0.2),
    ])
    intervals = report["tested_cost_intervals"]
    assert len(intervals) == 2
    assert [row["outcome"] for row in intervals] == ["unavailable", "unavailable"]
    assert all("return_differences" not in row for row in intervals)


@pytest.mark.parametrize("key,value", [
    ("dataset_sha256", "c" * 64), ("settings_sha256", "d" * 64),
    ("test_dates", ["2024-01-03", "2024-01-04"]),
    ("method_label", "paper-inspired-walk-forward"),
])
def test_completed_context_drift_is_rejected(key, value):
    other = completed(3)
    other["context"][key] = value
    with pytest.raises(ValueError, match="comparable context"):
        summarize_candidates(SweepSettings((7, 3), (0,), 2), [completed(), other])


@pytest.mark.parametrize("mutate", [
    lambda row: row["context"].update(dataset_sha256="A" * 64),
    lambda row: row["context"].update(test_dates=["2024-01-02", "2024-01-02"]),
    lambda row: row["context"].update(test_dates=["2024-01-03", "2024-01-02"]),
    lambda row: row["context"].update(test_dates=["2024-02-30", "2024-03-01"]),
    lambda row: row["context"].update(test_dates=["20240102", "20240103"]),
    lambda row: row["strategies"]["lstm"].update(observations=True),
    lambda row: row["strategies"]["lstm"].update(observations=3),
    lambda row: row["strategies"]["lstm"].update(sharpe=None, sharpe_note=" "),
    lambda row: row["strategies"]["lstm"].update(sharpe=1, sharpe_note="not null"),
    lambda row: row["strategies"]["lstm"].update(cumulative_return=float("nan")),
    lambda row: row["strategies"]["lstm"].update(total_turnover=float("inf")),
    lambda row: row["strategies"]["lstm"].update(max_drawdown=True),
    lambda row: row["strategies"]["lstm"].pop("total_cost_return_units"),
    lambda row: row.update(run_directory=" "),
])
def test_invalid_completed_record_is_rejected(mutate):
    row = completed()
    mutate(row)
    with pytest.raises(ValueError):
        summarize_candidates(SweepSettings((7,), (0,), 1), [row])


def test_strategy_set_drift_is_rejected():
    other = completed(3)
    other["strategies"]["cash"] = deepcopy(other["strategies"]["equal_weight"])
    with pytest.raises(ValueError, match="comparable context"):
        summarize_candidates(SweepSettings((7, 3), (0,), 2), [completed(), other])


def test_finite_large_values_do_not_overflow_mean():
    rows = [completed(7, model_return=1e308, baseline_return=1e308),
            completed(3, model_return=1e308, baseline_return=1e308)]
    report = summarize_candidates(SweepSettings((7, 3), (0,), 2), rows)
    result = report["by_cost"][0]["strategies"]["lstm"]["cumulative_return"]
    assert result["mean"] == 1e308
    assert result["population_std"] == 0.0
    json.dumps(report, allow_nan=False)


def test_impossible_loss_is_rejected_before_comparison():
    rows = [completed(7, cost, model_return=1e308, baseline_return=-1e308) for cost in (0, 5)]
    with pytest.raises(ValueError, match="cumulative_return must be at least -1"):
        summarize_candidates(SweepSettings((7,), (0, 5), 2), rows)


@pytest.mark.parametrize("metric,value", [
    ("cumulative_return", -1.000001), ("max_drawdown", -0.01), ("max_drawdown", 1.000001),
    ("annualized_volatility", -0.1), ("total_turnover", -1), ("total_cost_return_units", -0.01),
])
def test_impossible_metric_domain_is_rejected(metric, value):
    row = completed()
    row["strategies"]["lstm"][metric] = value
    with pytest.raises(ValueError, match=metric):
        summarize_candidates(SweepSettings((7,), (0,), 1), [row])


def test_metric_domain_boundaries_and_negative_sharpe_are_retained():
    row = completed(model_return=-1, sharpe=-3)
    row["strategies"]["lstm"].update(
        max_drawdown=1, total_turnover=0, total_cost_return_units=0,
    )
    report = summarize_candidates(SweepSettings((7,), (0,), 1), [row])
    values = report["records"][0]["strategies"]["lstm"]
    assert values["cumulative_return"] == -1
    assert values["max_drawdown"] == 1
    assert values["sharpe"] == -3
    assert report["by_cost"][0]["strategies"]["lstm"]["sharpe"]["mean"] == -3
    row["strategies"]["lstm"].update(
        annualized_volatility=0, sharpe=None, sharpe_note="zero return volatility",
    )
    zero_volatility = summarize_candidates(SweepSettings((7,), (0,), 1), [row])
    assert zero_volatility["records"][0]["strategies"]["lstm"]["annualized_volatility"] == 0
    assert zero_volatility["by_cost"][0]["strategies"]["lstm"]["sharpe"]["null_count"] == 1
