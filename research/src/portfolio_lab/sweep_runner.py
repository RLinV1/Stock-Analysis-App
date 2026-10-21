"""Sequential local sweep source. No work runs merely by importing this module."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

from .data import file_hash, load_dataset, save_json
from .json_io import parse_json_object
from .metrics import CONVENTIONS, baseline_weights
from .model import OBJECTIVE_CONVENTIONS
from .protocol import plan_walk_forward
from .runner import runtime_versions, source_fingerprint
from .snapshots import snapshot_csv_path, snapshot_dataset
from .sweep import Candidate, SweepSettings, plan_candidates, summarize_candidates
from .walk_forward import WalkForwardConfig, run_walk_forward


@dataclass(frozen=True)
class SweepModelConfig:
    """Common settings, deliberately excluding varying seed and transaction cost."""

    test_start: str
    test_end: str
    lookback: int
    hidden_size: int
    epochs: int
    batch_size: int
    learning_rate: float
    device: str

    def for_candidate(self, candidate: Candidate) -> WalkForwardConfig:
        return WalkForwardConfig(**asdict(self), seed=candidate.seed, cost_bps=candidate.cost_bps)


def _json_value(value):
    return json.loads(json.dumps(value, sort_keys=True, allow_nan=False))


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _read(directory: Path, filename: str) -> tuple[dict, str]:
    raw = (directory / filename).read_bytes()
    value = parse_json_object(raw)
    return value, hashlib.sha256(raw).hexdigest()


def _candidate_record(directory: Path, candidate_root: Path, group: Path,
                      candidate: Candidate, config: WalkForwardConfig,
                      identity: dict, dates: list[str], method: str,
                      settings_hash: str, expected_strategies: list[str]) -> tuple[dict, list[str]]:
    resolved = directory.resolve(strict=True)
    owned_root = candidate_root.resolve()
    if (not owned_root.is_relative_to(group.resolve()) or not resolved.is_dir()
            or not resolved.is_relative_to(owned_root)):
        raise ValueError("Returned candidate directory is outside its owned output root")
    (status, status_hash), (manifest, manifest_hash), (report, report_hash) = (
        _read(resolved, name) for name in ("status.json", "manifest.json", "report.json"))
    if status.get("state") != "completed":
        raise ValueError("Candidate group did not complete")
    folds = len(identity["evaluation_protocol"]["plan"]["folds"])
    if any(type(status.get(key)) is not int or status[key] != folds
           for key in ("completed_folds", "fold_budget")):
        raise ValueError("Candidate status fold counts differ from its plan")
    if _digest(manifest.get("config")) != _digest(asdict(config)):
        raise ValueError("Candidate configuration differs from requested settings")
    if any(_digest(manifest.get(key)) != _digest(identity[key]) for key in (
            "dataset_manifest_sha256", "source_sha256", "versions", "evaluation_protocol", "objective")):
        raise ValueError("Candidate dataset/source/runtime/protocol identity differs")
    if manifest.get("method_label") != method or _digest(manifest.get("conventions")) != _digest(CONVENTIONS):
        raise ValueError("Candidate method or accounting conventions differ")
    if (report.get("test_dates") != dates or type(report.get("cost_bps")) not in (int, float)
            or report["cost_bps"] != candidate.cost_bps):
        raise ValueError("Candidate report dates or costs differ")
    if report.get("method_label") != method or _digest(report.get("conventions")) != _digest(CONVENTIONS):
        raise ValueError("Candidate report method or accounting conventions differ")
    if _digest(report.get("objective")) != _digest(OBJECTIVE_CONVENTIONS):
        raise ValueError("Candidate report objective differs from the common method")
    omissions = report.get("baseline_omissions")
    expected_omissions = ([] if "stock_bond_60_40" in expected_strategies
                          else ["60/40 unavailable: missing stock/bond roles"])
    if omissions != expected_omissions:
        raise ValueError("Candidate baseline omissions differ from dataset roles")
    results = report.get("strategies")
    if not isinstance(results, dict) or set(results) != set(expected_strategies):
        raise ValueError("Candidate strategies differ from the learned/dataset baseline contract")
    metrics = {}
    for name, result in results.items():
        if not isinstance(result, dict) or not isinstance(result.get("metrics"), dict):
            raise ValueError("Candidate strategies require nested evaluator metrics")
        metrics[name] = result["metrics"]
    record = {
        "seed": candidate.seed, "cost_bps": candidate.cost_bps, "status": "completed",
        "run_directory": resolved.relative_to(group.resolve()).as_posix(),
        "manifest_sha256": manifest_hash, "report_sha256": report_hash,
        "status_sha256": status_hash,
        "strategies": metrics,
        "context": {"dataset_sha256": identity["dataset_manifest_sha256"],
                    "settings_sha256": settings_hash, "test_dates": dates, "method_label": method},
    }
    # Validate the report's metric schema before accepting this terminal result.
    summarize_candidates(SweepSettings((candidate.seed,), (candidate.cost_bps,), 1), [record])
    return record, omissions


def run_sweep(dataset_path: Path, config: SweepModelConfig, settings: SweepSettings,
              output_root: Path) -> Path:
    """Run all declared candidates in order with retained partial/failure state.

    This is unverified integration source. It provides no resume or external
    artifact verifier. Each candidate trains its own frozen walk-forward folds.
    """
    candidates = plan_candidates(settings)
    dataset = load_dataset(dataset_path)
    plan = plan_walk_forward(dataset.dates, config.test_start, config.test_end, lookback=config.lookback)
    snapshot_csv_path(dataset.manifest["csv"])
    for candidate in candidates:
        for fold in plan.folds:
            config.for_candidate(candidate).for_fold(fold)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    group = output_root / ("sweep-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
                           + "-" + uuid.uuid4().hex[:12])
    group.mkdir(exist_ok=False)
    inventory = [{"seed": item.seed, "cost_bps": item.cost_bps, "status": "pending"}
                 for item in candidates]
    active = None

    def progress(state: str, **extra) -> None:
        save_json(group / "candidates.json", inventory)
        save_json(group / "status.json", {
            "state": state, "active_candidate": active, "requested": len(candidates),
            "terminal_candidates": sum(row["status"] in ("completed", "failed", "invalid") for row in inventory),
            "folds_per_candidate": len(plan.folds), "planned_fold_runs": len(candidates) * len(plan.folds),
            "resume_supported": False, **extra,
        })

    with FileLock(str(group / ".run.lock"), timeout=0):
        try:
            progress("preparing")
            dataset = snapshot_dataset(dataset, group / "dataset")
            # Replan from the owned validated copy, then validate every fold again.
            plan = plan_walk_forward(dataset.dates, config.test_start, config.test_end, lookback=config.lookback)
            for candidate in candidates:
                for fold in plan.folds:
                    config.for_candidate(candidate).for_fold(fold)
            dates = [dataset.dates[index].item() if hasattr(dataset.dates[index], "item")
                     else dataset.dates[index] for fold in plan.folds for index in fold.test_indices]
            identity = {
                "config": asdict(config), "dataset_manifest_sha256": file_hash(group / "dataset/manifest.json"),
                "source_sha256": source_fingerprint(), "versions": runtime_versions(),
                "evaluation_protocol": _json_value({"kind": "expanding-walk-forward", "plan": asdict(plan)}),
                "conventions": CONVENTIONS, "objective": OBJECTIVE_CONVENTIONS,
            }
            settings_hash = _digest(identity)
            method = ("synthetic-walk-forward" if dataset.manifest["kind"] == "synthetic"
                      else "paper-inspired-walk-forward")
            save_json(group / "manifest.json", {
                "schema_version": 1, "run_id": group.name, **identity,
                "settings_sha256": settings_hash, "sweep": asdict(settings),
                "method_label": method, "dataset": dataset.manifest,
                "deviations": [*dataset.manifest["deviations"],
                               "Explicit caller grid; no favorable seed selection",
                               "Every grid cell is trained independently; costs affect evaluation only",
                               "Local sequential execution; no sweep resume or external replay verifier",
                               "Per-candidate model/baseline limitations remain in child artifacts"],
            })
            common_context = common_omissions = None
            expected_strategies = ["lstm", *baseline_weights(dataset.manifest["assets"], 0)]
            for index, candidate in enumerate(candidates):
                active = index
                root = group / "candidates" / f"candidate-{index:04d}"
                root.mkdir(parents=True)
                base = {"seed": candidate.seed, "cost_bps": candidate.cost_bps,
                        "run_directory": root.relative_to(group).as_posix()}
                inventory[index] = {**base, "status": "running"}
                progress("running")
                try:
                    # Validate immutable input identity immediately before each candidate.
                    if file_hash(group / "dataset/manifest.json") != identity["dataset_manifest_sha256"]:
                        raise ValueError("Sweep snapshot manifest changed")
                    load_dataset(group / "dataset/manifest.json")
                    child = run_walk_forward(group / "dataset/manifest.json", config.for_candidate(candidate), root)
                except Exception as exc:
                    inventory[index] = {**base, "status": "failed",
                                        "reason": "Candidate execution failed", "error_type": type(exc).__name__}
                else:
                    try:
                        record, omissions = _candidate_record(Path(child), root, group, candidate,
                                                              config.for_candidate(candidate), identity,
                                                              dates, method, settings_hash, expected_strategies)
                        checked = summarize_candidates(SweepSettings((candidate.seed,), (candidate.cost_bps,), 1), [record])
                        if common_context is not None and checked["context"] != common_context:
                            raise ValueError("Candidate strategy/context differs from earlier completed results")
                        if common_context is not None and omissions != common_omissions:
                            raise ValueError("Candidate baseline omissions differ")
                        common_context, common_omissions = checked["context"], omissions
                        inventory[index] = record
                    except Exception as exc:
                        inventory[index] = {**base, "status": "invalid",
                                            "reason": "Returned candidate artifacts failed validation",
                                            "error_type": type(exc).__name__}
                progress("running")
            active = None
            summary = summarize_candidates(settings, inventory)
            # The inventory retains hashes and error types as well as summary records.
            save_json(group / "report.json", {
                "schema_version": 1, **summary, "baseline_omissions": common_omissions,
                "candidate_inventory": "candidates.json", "settings_sha256": settings_hash,
                "objective": OBJECTIVE_CONVENTIONS,
            })
            progress("completed" if summary["all_successful"] else "completed_with_failures",
                     all_successful=summary["all_successful"], coverage_complete=True)
            return group
        except BaseException as exc:
            interrupted = isinstance(exc, (KeyboardInterrupt, SystemExit))
            if active is not None and inventory[active]["status"] == "running":
                inventory[active] = {**inventory[active], "status": "interrupted" if interrupted else "failed",
                                     "reason": "Sweep did not finish this candidate"}
            progress("interrupted" if interrupted else "failed", error_type=type(exc).__name__, coverage_complete=False)
            raise
