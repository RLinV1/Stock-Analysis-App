"""Local frozen-fold orchestration; no service routing or external replay claim."""

from __future__ import annotations

import csv
import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from filelock import FileLock

from .data import Dataset, file_hash, load_dataset, save_json
from .json_io import load_json_object, parse_json_object
from .metrics import CONVENTIONS, baseline_weights, evaluate
from .model import OBJECTIVE_CONVENTIONS
from .protocol import Fold, plan_walk_forward
from .provenance import source_revision
from .runner import RunConfig, run_experiment, runtime_versions, source_fingerprint, validate_fold_settings
from .snapshots import snapshot_csv_path, snapshot_dataset


@dataclass(frozen=True)
class WalkForwardConfig:
    # All settings are explicit: this does not adopt proposed project defaults.
    test_start: str
    test_end: str
    lookback: int
    hidden_size: int
    epochs: int
    batch_size: int
    learning_rate: float
    seed: int
    cost_bps: float
    device: str

    def for_fold(self, fold: Fold) -> RunConfig:
        validate_fold_settings(self)
        values = asdict(self)
        values.pop("test_start")
        values.pop("test_end")
        result = RunConfig(fold.train_end, fold.validation_end, **values,
                           normalization="train-only", objective_window="minibatch")
        result.validate()
        return result


def _allocations(directory: Path, symbols: list[str], dates: list[str], strategies: list[str]) -> dict:
    """Read only the just-produced fold output, preserving asset/date identity."""
    positions = {date: index for index, date in enumerate(dates)}
    values = {name: np.zeros((len(dates), len(symbols)), dtype=np.float64) for name in strategies}
    seen = set()
    with (directory / "allocations.csv").open(newline="", encoding="utf-8") as handle:
        rows = csv.reader(handle)
        if next(rows, None) != ["return_date", "strategy", *symbols]:
            raise ValueError("Fold allocation asset header differs from the snapshot")
        for row in rows:
            if len(row) != len(symbols) + 2:
                raise ValueError("Fold allocation dimensions differ from the snapshot")
            date, strategy = row[:2]
            identity = (strategy, date)
            if date not in positions or strategy not in values or identity in seen:
                raise ValueError("Fold allocation dates/strategies are missing, extra or duplicated")
            weights = np.asarray([float(value) for value in row[2:]], dtype=np.float64)
            if (not np.isfinite(weights).all() or np.any(weights < 0)
                    or not np.isclose(weights.sum(), 1, atol=1e-6, rtol=0)):
                raise ValueError("Fold allocations must be finite normalized long-only weights")
            values[strategy][positions[date]] = weights
            seen.add(identity)
    if len(seen) != len(dates) * len(strategies):
        raise ValueError("Fold allocations omit an evaluation target")
    return values


def _evaluation_returns(dataset: Dataset, fold: Fold) -> np.ndarray:
    """Recover planned targets without reconstructing training feature windows.

    Dataset/fold validation belongs to the owned snapshot and planner. Match
    make_samples' price arithmetic and float32 target conversion exactly.
    """
    indices = np.asarray(fold.test_indices, dtype=np.intp)
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            values = (dataset.prices[indices] / dataset.prices[indices - 1] - 1).astype(np.float32)
    except (OverflowError, FloatingPointError) as exc:
        raise ValueError("Evaluation return conversion overflowed") from exc
    if not np.isfinite(values).all():
        raise ValueError("Evaluation return conversion overflowed")
    return values


def continuous_results(weights: dict[str, np.ndarray], returns: np.ndarray,
                       cost_bps: float) -> dict:
    """Charge one initial position and actual adjacent targets across all folds."""
    if not weights:
        raise ValueError("Require at least one recorded strategy")
    return {name: evaluate(values, returns, cost_bps, allow_single_observation=True)
            for name, values in weights.items()}


def run_walk_forward(dataset_path: Path, config: WalkForwardConfig, output_root: Path) -> Path:
    """Train sequential frozen folds from a validated local dataset snapshot.

    Every group is new. Partial groups are retained; no group resume or A0 repeat
    is implied. Child fold reports have local-entry accounting; this group's
    report recomputes the continuous account from the recorded target weights.
    """
    dataset = load_dataset(dataset_path)
    plan = plan_walk_forward(dataset.dates, config.test_start, config.test_end,
                             lookback=config.lookback)
    for fold in plan.folds:
        config.for_fold(fold)
    snapshot_csv_path(dataset.manifest["csv"])
    output_root.mkdir(parents=True, exist_ok=True)
    directory = output_root / ("walk-forward-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
                               + "-" + uuid.uuid4().hex[:12])
    directory.mkdir(exist_ok=False)
    records = []
    active_fold = None
    with FileLock(str(directory / ".run.lock"), timeout=0):
        try:
            snapshot = directory / "dataset"
            dataset = snapshot_dataset(dataset, snapshot)
            # Plan from the validated copy, not a mutable original input directory.
            plan = plan_walk_forward(dataset.dates, config.test_start, config.test_end,
                                     lookback=config.lookback)
            identity = {"config": asdict(config), "dataset": dataset.manifest,
                        "dataset_manifest_sha256": file_hash(snapshot / "manifest.json"),
                        "source_sha256": source_fingerprint(), "versions": runtime_versions(),
                        "objective": OBJECTIVE_CONVENTIONS,
                        "evaluation_protocol": {"kind": "expanding-walk-forward", "plan": asdict(plan)}}
            method = "synthetic-walk-forward" if dataset.manifest["kind"] == "synthetic" else "paper-inspired-walk-forward"
            save_json(directory / "manifest.json", {
                "schema_version": 1, "run_id": directory.name, **identity,
                "identity_sha256": hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest(),
                "source_revision": source_revision(), "method_label": method,
                "conventions": CONVENTIONS,
                "deviations": [*dataset.manifest["deviations"],
                               "Current daily equal-weight/60-40 baseline subset; not the full paper suite",
                               "Local group execution; no group resume or external v2 replay verifier",
                               "Transaction costs apply to evaluation only, not training/validation loss",
                               "Per-fold modelling/execution limitations remain in referenced child manifests",
                               "Explicit caller seed/settings reused independently for each fold"]})
            all_dates, all_returns, all_weights = [], [], {}
            strategies = None
            baseline_omissions = None
            for fold in plan.folds:
                active_fold = fold.number
                save_json(directory / "status.json", {"state": "running", "active_fold": fold.number,
                                                       "completed_folds": len(records), "fold_budget": len(plan.folds)})
                fold_config = config.for_fold(fold)
                fold_root = directory / "folds" / f"fold-{fold.number:04d}"
                child = Path(run_experiment(snapshot / "manifest.json", fold_config,
                                            fold_root, fold=fold)).resolve(strict=True)
                if (not fold_root.resolve().is_relative_to(directory.resolve())
                        or not child.is_dir() or not child.is_relative_to(fold_root.resolve())):
                    raise ValueError("Fold returned a directory outside its owned output root")
                report_bytes = (child / "report.json").read_bytes()
                manifest_bytes = (child / "manifest.json").read_bytes()
                report = parse_json_object(report_bytes)
                child_manifest = parse_json_object(manifest_bytes)
                if load_json_object(child / "status.json").get("state") != "completed":
                    raise ValueError("Fold did not complete")
                expected_protocol = {"kind": "expanding-walk-forward-fold",
                                     "fold": json.loads(json.dumps(asdict(fold)))}
                fold_method = "synthetic-smoke" if dataset.manifest["kind"] == "synthetic" else "paper-inspired"
                expected_child = {"evaluation_protocol": expected_protocol, "config": asdict(fold_config),
                                  "method_label": fold_method, "conventions": CONVENTIONS,
                                  "objective": OBJECTIVE_CONVENTIONS,
                                  **{key: identity[key] for key in (
                                      "dataset_manifest_sha256", "source_sha256", "versions")}}
                actual_child = {key: child_manifest.get(key) for key in expected_child}
                if (json.dumps(actual_child, sort_keys=True, allow_nan=False)
                        != json.dumps(expected_child, sort_keys=True, allow_nan=False)):
                    raise ValueError("Fold provenance differs from its group snapshot, protocol or settings")
                dates = dataset.dates[list(fold.test_indices)].tolist()
                expected_strategies = ["lstm", *baseline_weights(dataset.manifest["assets"], 0)]
                if not isinstance(report.get("strategies"), dict) or list(report["strategies"]) != expected_strategies:
                    raise ValueError("Fold report differs from the learned/baseline strategy contract")
                expected_omissions = ([] if "stock_bond_60_40" in expected_strategies
                                      else ["60/40 unavailable: missing stock/bond roles"])
                if report.get("baseline_omissions") != expected_omissions:
                    raise ValueError("Fold baseline omissions differ from dataset roles")
                current_strategies = list(report["strategies"])
                if (report["test_dates"] != dates or type(report.get("cost_bps")) not in (int, float)
                        or report["cost_bps"] != config.cost_bps
                        or report.get("method_label") != fold_method
                        or json.dumps(report.get("conventions"), sort_keys=True, allow_nan=False)
                        != json.dumps(CONVENTIONS, sort_keys=True, allow_nan=False)
                        or json.dumps(report.get("objective"), sort_keys=True, allow_nan=False)
                        != json.dumps(OBJECTIVE_CONVENTIONS, sort_keys=True, allow_nan=False)
                        or (strategies is not None and current_strategies != strategies)
                        or (baseline_omissions is not None
                            and report["baseline_omissions"] != baseline_omissions)):
                    raise ValueError("Fold report differs from planned dates, cost or strategy order")
                strategies = current_strategies
                baseline_omissions = report["baseline_omissions"]
                allocations = _allocations(child, dataset.symbols, dates, strategies)
                returns = _evaluation_returns(dataset, fold)
                local_results = continuous_results(allocations, returns, config.cost_bps)
                if (json.dumps(report["strategies"], sort_keys=True, allow_nan=False)
                        != json.dumps(local_results, sort_keys=True, allow_nan=False)):
                    raise ValueError("Fold reported accounting differs from its recorded allocations and owned returns")
                all_dates.extend(dates)
                all_returns.append(returns)
                for name, weights in allocations.items():
                    all_weights.setdefault(name, []).append(weights)
                records.append({"number": fold.number, "run_directory": child.relative_to(directory.resolve()).as_posix(),
                                "train_end": fold.train_end, "validation_end": fold.validation_end,
                                "test_start": fold.test_start, "test_end": fold.test_end,
                                "model_and_scaler_sha256": file_hash(child / "model.pt"),
                                "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                                "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
                                "deviations": child_manifest["deviations"]})
                save_json(directory / "folds.json", {"completed_folds": records})
            expected = [str(dataset.dates[index]) for fold in plan.folds for index in fold.test_indices]
            if all_dates != expected or len(set(all_dates)) != len(all_dates):
                raise ValueError("Group evaluation does not cover planned targets exactly once")
            combined = {name: np.concatenate(parts) for name, parts in all_weights.items()}
            results = continuous_results(combined, np.concatenate(all_returns), config.cost_bps)
            with (directory / "allocations.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["return_date", "strategy", *dataset.symbols])
                for name, values in combined.items():
                    writer.writerows([date, name, *weights.tolist()] for date, weights in zip(all_dates, values))
            save_json(directory / "report.json", {
                "run_id": directory.name, "method_label": method, "test_dates": all_dates,
                "cost_bps": config.cost_bps, "strategies": results, "folds": records,
                "baseline_omissions": baseline_omissions,
                "requested_start": plan.requested_start, "requested_end": plan.requested_end,
                "effective_start": plan.effective_start, "effective_end": plan.effective_end,
                "exclusions": list(plan.exclusions), "conventions": CONVENTIONS,
                "objective": OBJECTIVE_CONVENTIONS,
                "accounting": "One initial cash entry; continuous target turnover across fold boundaries"})
            save_json(directory / "status.json", {"state": "completed", "completed_folds": len(records),
                                                   "fold_budget": len(plan.folds)})
        except BaseException as error:
            save_json(directory / "status.json", {
                "state": "interrupted" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "failed",
                "completed_folds": len(records), "completed_runs": records,
                "active_fold": active_fold, "error_type": type(error).__name__,
                "limitation": "Partial group retained; group resume is not implemented"})
            raise
    return directory
