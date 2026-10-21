"""Pure, explicit seed/cost planning and descriptive summaries.

This module starts no experiments. Caller-supplied records are validated for
comparability, not authenticated against artifacts on disk.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from statistics import mean, pstdev
from typing import Sequence


METRICS = (
    "cumulative_return", "annualized_volatility", "sharpe", "max_drawdown",
    "total_turnover", "total_cost_return_units",
)


@dataclass(frozen=True)
class Candidate:
    seed: int
    cost_bps: float


@dataclass(frozen=True)
class SweepSettings:
    seeds: tuple[int, ...]
    costs_bps: tuple[float, ...]
    max_runs: int

    def __post_init__(self) -> None:
        if type(self.max_runs) is not int or self.max_runs < 1:
            raise ValueError("max_runs must be an explicit positive integer")
        if not isinstance(self.seeds, (list, tuple)) or not isinstance(self.costs_bps, (list, tuple)):
            raise ValueError("seeds and costs_bps must be explicit ordered lists or tuples")
        if len(self.seeds) * len(self.costs_bps) > self.max_runs:
            raise ValueError("requested candidates exceed max_runs")
        object.__setattr__(self, "seeds", tuple(self.seeds))
        object.__setattr__(self, "costs_bps", tuple(self.costs_bps))


def _number(value: object) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def plan_candidates(settings: SweepSettings) -> tuple[Candidate, ...]:
    """Validate the entire budget before returning candidates in caller order."""
    if type(settings.max_runs) is not int or settings.max_runs < 1:
        raise ValueError("max_runs must be an explicit positive integer")
    if not settings.seeds or not settings.costs_bps:
        raise ValueError("seeds and costs_bps must both be nonempty")
    if any(type(seed) is not int or not 0 <= seed <= 2**32 - 1 for seed in settings.seeds):
        raise ValueError("seeds must be unsigned 32-bit integers")
    if any(not _number(cost) or not 0 <= cost <= 100 for cost in settings.costs_bps):
        raise ValueError("costs_bps must be finite numbers from 0 through 100")
    if len(set(settings.seeds)) != len(settings.seeds):
        raise ValueError("duplicate seeds are not permitted")
    if len(set(settings.costs_bps)) != len(settings.costs_bps):
        raise ValueError("duplicate costs are not permitted")
    if len(settings.seeds) * len(settings.costs_bps) > settings.max_runs:
        raise ValueError("requested candidates exceed max_runs")
    return tuple(Candidate(seed, float(cost)) for seed in settings.seeds for cost in settings.costs_bps)


def _context(record: dict, strategies: tuple[str, ...]) -> dict:
    context = record.get("context")
    if not isinstance(context, dict):
        raise ValueError("completed candidates require context")
    for key in ("dataset_sha256", "settings_sha256"):
        value = context.get(key)
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise ValueError(f"context requires a lowercase SHA-256 {key}")
    dates = context.get("test_dates")
    if not isinstance(dates, list) or not dates or any(not isinstance(day, str) for day in dates):
        raise ValueError("context requires nonempty test_dates")
    try:
        canonical = all(date.fromisoformat(day).isoformat() == day for day in dates)
    except ValueError as exc:
        raise ValueError("test_dates must be canonical ISO dates") from exc
    if not canonical or dates != sorted(set(dates)):
        raise ValueError("test_dates must be canonical, unique, and increasing")
    method = context.get("method_label")
    if not isinstance(method, str) or not method.strip():
        raise ValueError("context requires method_label")
    return {
        "dataset_sha256": context["dataset_sha256"],
        "settings_sha256": context["settings_sha256"],
        "test_dates": list(dates), "method_label": method,
        "strategies": list(strategies),
    }


def _completed(record: dict) -> tuple[dict, dict]:
    strategies = record.get("strategies")
    if not isinstance(strategies, dict) or "lstm" not in strategies:
        raise ValueError("completed candidates require lstm strategy metrics")
    if any(not isinstance(name, str) or not name.strip() for name in strategies):
        raise ValueError("strategy names must be nonempty strings")
    context = _context(record, tuple(sorted(strategies)))
    checked = {}
    for name, metrics in strategies.items():
        if not isinstance(metrics, dict) or any(key not in metrics for key in METRICS):
            raise ValueError("completed strategies require all supported metrics")
        observations = metrics.get("observations")
        if type(observations) is not int or observations != len(context["test_dates"]):
            raise ValueError("observations must match test_dates")
        values = {"observations": observations}
        for key in METRICS:
            value = metrics[key]
            if key == "sharpe" and value is None:
                note = metrics.get("sharpe_note")
                if not isinstance(note, str) or not note.strip():
                    raise ValueError("null Sharpe requires an explanation")
                values[key], values["sharpe_note"] = None, note
            elif not _number(value):
                raise ValueError(f"{key} must be finite; only Sharpe may be null")
            else:
                values[key] = float(value)
                if key == "sharpe":
                    if metrics.get("sharpe_note") is not None:
                        raise ValueError("numeric Sharpe must not have a null explanation")
                    values["sharpe_note"] = None
        if values["cumulative_return"] < -1:
            raise ValueError("cumulative_return must be at least -1")
        if not 0 <= values["max_drawdown"] <= 1:
            raise ValueError("max_drawdown must be between 0 and 1")
        for key in ("annualized_volatility", "total_turnover", "total_cost_return_units"):
            if values[key] < 0:
                raise ValueError(f"{key} must be nonnegative")
        checked[name] = values
    return checked, context


def _distribution(values: list[float], reasons: list[str]) -> dict:
    # statistics.mean avoids an overflowing intermediate sum of finite values.
    result = {
        "numeric_count": len(values), "null_count": len(reasons),
        "null_reasons": dict(sorted(Counter(reasons).items())),
        "mean": float(mean(values)) if values else None,
        "population_std": pstdev(values) if values else None,
        "min": min(values) if values else None, "max": max(values) if values else None,
    }
    if any(value is not None and not math.isfinite(value)
           for value in (result["mean"], result["population_std"], result["min"], result["max"])):
        raise ValueError("derived statistics must be finite")
    return result


def summarize_candidates(settings: SweepSettings, records: Sequence[dict]) -> dict:
    """Require every requested terminal result, including failed/invalid cells.

    settings_sha256 identifies all common experiment settings EXCEPT seed and
    cost. Caller context is not authenticated here; local execution checks are separate.
    """
    candidates = plan_candidates(settings)
    expected = {(item.seed, item.cost_bps) for item in candidates}
    indexed: dict[tuple[int, float], dict] = {}
    common = None
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("candidate records must be objects")
        seed, cost = record.get("seed"), record.get("cost_bps")
        if type(seed) is not int or not _number(cost):
            raise ValueError("candidate identity requires integer seed and finite cost")
        key = (seed, float(cost))
        if key not in expected or key in indexed:
            raise ValueError("candidate is unrequested or duplicated")
        status = record.get("status")
        row = {"seed": seed, "cost_bps": float(cost), "status": status}
        if status == "completed":
            strategies, context = _completed(record)
            if common is not None and common != context:
                raise ValueError("completed candidates must share a comparable context")
            common = context
            row["strategies"] = strategies
        elif status in ("failed", "invalid"):
            reason = record.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("failed and invalid candidates require a reason")
            row["reason"] = reason
        else:
            raise ValueError("every candidate must have a terminal status")
        if "run_directory" in record:
            directory = record["run_directory"]
            if not isinstance(directory, str) or not directory.strip():
                raise ValueError("run_directory must be a nonempty string")
            row["run_directory"] = directory
        indexed[key] = row
    if set(indexed) != expected:
        raise ValueError("candidate coverage is incomplete")

    ordered = [indexed[(item.seed, item.cost_bps)] for item in candidates]
    names = common["strategies"] if common else []
    by_cost = []
    for cost in settings.costs_bps:
        rows = [indexed[(seed, float(cost))] for seed in settings.seeds]
        completed = [row for row in rows if row["status"] == "completed"]
        counts = Counter(row["status"] for row in rows)
        strategies = {}
        for name in names:
            distributions = {}
            for metric in METRICS:
                values = [row["strategies"][name][metric] for row in completed
                          if row["strategies"][name][metric] is not None]
                reasons = [row["strategies"][name]["sharpe_note"] for row in completed
                           if row["strategies"][name][metric] is None]
                distributions[metric] = _distribution(values, reasons)
            strategies[name] = distributions
        by_cost.append({
            "cost_bps": float(cost), "requested": len(rows),
            **{status: counts[status] for status in ("completed", "failed", "invalid")},
            "strategies": strategies,
        })

    intervals = []
    costs = sorted(float(cost) for cost in settings.costs_bps)
    for seed in settings.seeds:
        for baseline in (name for name in names if name != "lstm"):
            for low, high in zip(costs, costs[1:]):
                rows = [indexed[(seed, low)], indexed[(seed, high)]]
                interval = {"seed": seed, "baseline": baseline, "low_cost_bps": low, "high_cost_bps": high}
                if any(row["status"] != "completed" for row in rows):
                    interval["outcome"] = "unavailable"
                else:
                    differences = [row["strategies"]["lstm"]["cumulative_return"]
                                   - row["strategies"][baseline]["cumulative_return"] for row in rows]
                    if not all(math.isfinite(value) for value in differences):
                        raise ValueError("derived return differences must be finite")
                    interval["return_differences"] = differences
                    interval["outcome"] = (
                        "tie_at_tested_cost" if 0 in differences else
                        "sign_change" if (differences[0] < 0) != (differences[1] < 0) else
                        "no_sign_change"
                    )
                intervals.append(interval)
    counts = Counter(row["status"] for row in ordered)
    return {
        "scope": "local-explicit-seed-cost-summary", "coverage_complete": True,
        "all_successful": counts["completed"] == len(candidates),
        "requested": len(candidates),
        **{status: counts[status] for status in ("completed", "failed", "invalid")},
        "records": ordered, "by_cost": by_cost, "tested_cost_intervals": intervals,
        "context": common,
        "limitations": [
            "Descriptive statistics only; no significance or confidence claim.",
            "All requested candidates are retained; no favorable seed selection.",
            "Only adjacent tested cost intervals are reported; no interpolated threshold.",
            "Caller-supplied context is not artifact authentication or historical evidence.",
            "This summary does not establish group replay support or additional baseline implementations.",
        ],
    }
