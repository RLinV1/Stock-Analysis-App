"""Bounded, same-environment A0 repeat comparisons; not the v2 verifier."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import uuid
from dataclasses import fields
from pathlib import Path

from .data import file_hash, load_dataset, save_json
from .runner import RunConfig, run_experiment, runtime_versions, source_fingerprint


ABSOLUTE_TOLERANCE = 1e-7
IDENTITY_FIELDS = ("config", "dataset", "dataset_manifest_sha256", "source_sha256", "versions")
REPORT_FIELDS = {"run_id", "method_label", "test_dates", "cost_bps", "best_validation_epoch",
                 "strategies", "baseline_omissions", "conventions", "history", "runtime"}


class IncompatibleInput(ValueError):
    def __init__(self, differences: list[dict]):
        super().__init__("Recorded inputs do not match the available experiment inputs")
        self.differences = differences


def _reject_constant(value: str):
    raise ValueError(f"Nonfinite JSON value: {value}")


def _read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path.name}")
    def finite(item):
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError(f"Nonfinite JSON number in {path.name}")
        if isinstance(item, dict):
            for child in item.values():
                finite(child)
        elif isinstance(item, list):
            for child in item:
                finite(child)
    finite(value)
    return value


def _read_report(directory: Path) -> dict:
    report = _read_object(directory / "report.json")
    if not REPORT_FIELDS <= report.keys():
        raise ValueError("Reference report is incomplete")
    if (not isinstance(report["strategies"], dict) or not report["strategies"]
            or not isinstance(report["test_dates"], list) or not report["test_dates"]
            or not isinstance(report["history"], list) or not report["history"]):
        raise ValueError("Reference report has no strategies, dates or training history")
    required = {"metrics", "gross_returns", "net_returns", "costs", "turnover", "wealth"}
    metrics = {"cumulative_return", "annualized_volatility", "sharpe", "sharpe_note",
               "max_drawdown", "total_turnover", "total_cost_return_units", "observations"}
    for strategy in report["strategies"].values():
        if not isinstance(strategy, dict) or not required <= strategy.keys():
            raise ValueError("Reference strategy report is incomplete")
        if not isinstance(strategy["metrics"], dict) or not metrics <= strategy["metrics"].keys():
            raise ValueError("Reference strategy metrics are incomplete")
        for series in required - {"metrics"}:
            if not isinstance(strategy[series], list) or len(strategy[series]) != len(report["test_dates"]):
                raise ValueError("Reference series lengths disagree with the test dates")
    return report


def _read_allocations(directory: Path, manifest: dict) -> list:
    symbols = [asset["symbol"] for asset in manifest["dataset"]["assets"]]
    with (directory / "allocations.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if not rows or rows[0] != ["return_date", "strategy", *symbols] or len(rows) < 2:
        raise ValueError("Allocation header/order or rows are missing")
    result = []
    for row in rows[1:]:
        if len(row) != 2 + len(symbols):
            raise ValueError("Allocation row width disagrees with declared assets")
        weights = [float(value) for value in row[2:]]
        if any(not math.isfinite(value) for value in weights):
            raise ValueError("Allocation weights must be finite")
        result.append([row[0], row[1], *weights])
    return result


def _preflight(reference: Path) -> tuple[dict, Path, RunConfig]:
    manifest = _read_object(reference / "manifest.json")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise ValueError("Only local A0 schema_version=1 is supported")
    if _read_object(reference / "status.json").get("state") != "completed":
        raise ValueError("Only a completed reference run can be repeated")
    required = {*IDENTITY_FIELDS, "identity_sha256", "scaler", "split_counts", "split_targets",
                "conventions", "method_label", "deviations"}
    if not required <= manifest.keys():
        raise ValueError("Reference run manifest is incomplete")
    if not isinstance(manifest["config"], dict) or set(manifest["config"]) != {field.name for field in fields(RunConfig)}:
        raise ValueError("Reference must record every configuration field explicitly")
    config = RunConfig(**manifest["config"])
    config.validate()
    identity = {name: manifest[name] for name in IDENTITY_FIELDS}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    differences = []
    for name, actual in (("identity_sha256", digest), ("source_sha256", source_fingerprint()),
                         ("versions", runtime_versions())):
        if manifest[name] != actual:
            differences.append({"path": name, "expected": manifest[name], "actual": actual})
    dataset_path = reference / "dataset" / "manifest.json"
    actual_hash = file_hash(dataset_path)
    if actual_hash != manifest["dataset_manifest_sha256"]:
        differences.append({"path": "dataset_manifest_sha256",
                            "expected": manifest["dataset_manifest_sha256"], "actual": actual_hash})
    if differences:
        raise IncompatibleInput(differences)
    # Validate the saved CSV bytes, column order and declared data policy before training.
    try:
        dataset = load_dataset(dataset_path)
    except ValueError as exc:
        raise IncompatibleInput([{"path": "dataset", "reason": str(exc)}]) from exc
    if dataset.manifest != manifest["dataset"]:
        raise IncompatibleInput([{"path": "dataset", "reason": "Copied and recorded manifests differ"}])
    for name in ("model.pt", "checkpoint.pt"):
        if not (reference / name).is_file():
            raise ValueError(f"Completed reference is missing {name}")
    _read_report(reference)
    _read_allocations(reference, manifest)
    return manifest, dataset_path, config


def _compare(path: str, expected, actual, entries: list[dict]) -> None:
    """Compare shape/types/null reasons exactly and finite floats with a fixed bound."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(expected.keys() | actual.keys()):
            child = f"{path}.{key}"
            if key not in expected or key not in actual:
                entries.append({"path": child, "matches": False, "reason": "Missing or extra field"})
            else:
                _compare(child, expected[key], actual[key], entries)
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            entries.append({"path": path, "matches": False, "reason": "Different lengths",
                            "expected": len(expected), "actual": len(actual)})
        for index, (left, right) in enumerate(zip(expected, actual)):
            _compare(f"{path}[{index}]", left, right, entries)
    else:
        entry = {"path": path, "expected": expected, "actual": actual}
        if (isinstance(expected, (int, float)) and not isinstance(expected, bool)
                and isinstance(actual, (int, float)) and not isinstance(actual, bool)):
            if not math.isfinite(expected) or not math.isfinite(actual):
                raise ValueError(f"Nonfinite numeric result at {path}")
            difference = abs(expected - actual)
            # Integral values (counts/epochs) must agree exactly, including their type.
            integral = isinstance(expected, int) or isinstance(actual, int)
            entry["absolute_difference"] = difference
            entry["matches"] = (type(expected) is type(actual) and difference == 0) if integral else difference <= ABSOLUTE_TOLERANCE
        else:
            entry["matches"] = type(expected) is type(actual) and expected == actual
        entries.append(entry)


def compare_runs(reference: Path, repeated: Path) -> dict:
    """Compare completed local run outputs; does not certify artifact authenticity."""
    entries = []
    manifests = [_read_object(path / "manifest.json") for path in (reference, repeated)]
    for path in (reference, repeated):
        if _read_object(path / "status.json").get("state") != "completed":
            raise ValueError("Both compared runs must be completed")
    for name in ("config", "dataset", "dataset_manifest_sha256", "source_sha256", "versions"):
        if manifests[0][name] != manifests[1][name]:
            raise IncompatibleInput([{"path": name, "reason": "Compared run inputs differ"}])
    for name in ("scaler", "split_counts", "split_targets", "conventions", "method_label", "deviations"):
        _compare(f"manifest.{name}", manifests[0][name], manifests[1][name], entries)
    reports = [_read_report(path) for path in (reference, repeated)]
    for report in reports:
        # UUIDs and measurements are intentionally not numerical reproducibility claims.
        report.pop("run_id")
        report.pop("runtime")
    _compare("report", reports[0], reports[1], entries)
    _compare("allocations", _read_allocations(reference, manifests[0]),
             _read_allocations(repeated, manifests[1]), entries)
    mismatches = [entry for entry in entries if not entry["matches"]]
    return {"outcome": "different" if mismatches else "matched", "comparison_count": len(entries),
            "mismatch_count": len(mismatches),
            "max_absolute_difference": max((entry.get("absolute_difference", 0) for entry in entries), default=0),
            "comparisons": entries}


def repeat_experiment(reference_dir: Path, output_root: Path) -> Path:
    """Retain a separate report for every attempt, including rejected/failed repeats."""
    reference = reference_dir.resolve()
    output_root = output_root.resolve()
    if output_root.is_relative_to(reference):
        raise ValueError("Repeat output must be outside the immutable reference run")
    comparison_dir = output_root / ("repeat-" + uuid.uuid4().hex)
    comparison_dir.mkdir(parents=True, exist_ok=False)
    result = {"schema_version": 1, "scope": "a0-local-repeat", "reference_run": str(reference),
              "repeated_run": None, "absolute_tolerance": ABSOLUTE_TOLERANCE, "relative_tolerance": 0,
              "limitation": "Same-environment output comparison; no v2 source retrieval, full lock or artifact authenticity proof."}
    try:
        _, dataset_path, config = _preflight(reference)
    except IncompatibleInput as exc:
        result.update(outcome="incompatible", differences=exc.differences)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result.update(outcome="unavailable", reason=str(exc), error_type=type(exc).__name__)
    else:
        try:
            repeated = run_experiment(dataset_path, config, comparison_dir / "runs")
            result["repeated_run"] = str(repeated.resolve())
            result.update(compare_runs(reference, repeated))
        except IncompatibleInput as exc:
            result.update(outcome="incompatible", differences=exc.differences)
        except Exception as exc:
            # Retain the error and any failed run artifacts; never call failure a match.
            result.update(outcome="failed", reason=str(exc), error_type=type(exc).__name__)
    report_path = comparison_dir / "comparison.json"
    save_json(report_path, result)
    return report_path
