"""Explicit data provenance and chronological, next-period samples."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path: Path, value: object) -> None:
    """Replace a complete JSON file atomically within its directory."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


@dataclass
class Dataset:
    dates: np.ndarray
    prices: np.ndarray
    manifest: dict
    manifest_path: Path

    @property
    def symbols(self) -> list[str]:
        return [asset["symbol"] for asset in self.manifest["assets"]]


def load_dataset(path: Path) -> Dataset:
    path = path.resolve()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "kind", "source", "license", "adjustment", "missing_data",
                "assets", "start", "end", "csv", "sha256", "deviations"}
    if not required <= manifest.keys() or manifest["schema_version"] != 1:
        raise ValueError("Dataset manifest is incomplete or uses an unsupported schema")
    if manifest["kind"] not in {"synthetic", "historical"}:
        raise ValueError("Dataset kind must be synthetic or historical")
    if any(not isinstance(manifest[k], str) or not manifest[k].strip()
           for k in ("source", "license", "adjustment")):
        raise ValueError("Data source, license/access notes, and adjustment convention are required")
    if manifest["missing_data"] != "reject":
        raise ValueError("Only the explicit reject missing-data policy is supported")
    if not isinstance(manifest["deviations"], list) or not manifest["deviations"]:
        raise ValueError("Declare the dataset's deviations from the paper")
    assets = manifest["assets"]
    if not isinstance(assets, list) or len(assets) < 2:
        raise ValueError("At least two assets are required")
    symbols = [a["symbol"] for a in assets]
    if len(set(symbols)) != len(symbols) or any(not s or s == "date" for s in symbols):
        raise ValueError("Asset symbols must be nonempty and unique")
    if any(a.get("role") not in {"stock", "bond", "other"} for a in assets):
        raise ValueError("Each asset needs a stock, bond, or other role")
    csv_path = path.parent / manifest["csv"]
    if Path(manifest["csv"]).name != manifest["csv"]:
        raise ValueError("CSV must be a filename alongside the manifest")
    if file_hash(csv_path) != manifest["sha256"]:
        raise ValueError("Dataset checksum mismatch")
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["date", *symbols]:
            raise ValueError("CSV columns must match the declared asset order")
        rows = list(reader)
    if len(rows) < 3:
        raise ValueError("Dataset is too short")
    dates = []
    for row in rows:
        parsed = date.fromisoformat(row["date"])
        if parsed.isoformat() != row["date"]:
            raise ValueError("Dates must use YYYY-MM-DD")
        dates.append(row["date"])
    if any(a >= b for a, b in zip(dates, dates[1:])):
        raise ValueError("Dates must be strictly increasing without duplicates")
    if (dates[0], dates[-1]) != (manifest["start"], manifest["end"]):
        raise ValueError("Manifest date range disagrees with CSV")
    try:
        prices = np.array([[float(row[s]) for s in symbols] for row in rows], dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError("Prices must be present and numeric") from exc
    if not np.isfinite(prices).all() or np.any(prices <= 0):
        raise ValueError("Prices must be finite and strictly positive")
    return Dataset(np.array(dates), prices, manifest, path)


def write_dataset(directory: Path, dates: list[str], prices: np.ndarray, assets: list[dict],
                  *, kind: str, source: str, license_note: str, adjustment: str,
                  deviations: list[str]) -> Path:
    directory.mkdir(parents=True, exist_ok=False)
    csv_path = directory / "prices.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", *(a["symbol"] for a in assets)])
        writer.writerows([d, *(format(float(v), ".12g") for v in p)] for d, p in zip(dates, prices))
    path = directory / "manifest.json"
    save_json(path, {"schema_version": 1, "kind": kind, "source": source,
                     "license": license_note, "adjustment": adjustment, "missing_data": "reject",
                     "assets": assets, "start": dates[0], "end": dates[-1], "csv": "prices.csv",
                     "sha256": file_hash(csv_path), "deviations": deviations})
    load_dataset(path)
    return path


def synthetic_dataset(directory: Path, observations: int = 420, seed: int = 2026) -> Path:
    if observations < 100:
        raise ValueError("Synthetic dataset needs at least 100 observations")
    rng = np.random.default_rng(seed)
    dates, day = [], date(2018, 1, 1)
    while len(dates) < observations:
        if day.weekday() < 5:
            dates.append(day.isoformat())
        day += timedelta(days=1)
    returns = rng.normal([0.00025, 0.00008, 0.00012], [0.01, 0.003, 0.012], (observations - 1, 3))
    prices = np.vstack([np.full(3, 100.0), 100 * np.cumprod(1 + returns, axis=0)])
    assets = [{"symbol": s, "role": r} for s, r in
              [("SYN_STOCK", "stock"), ("SYN_BOND", "bond"), ("SYN_OTHER", "other")]]
    return write_dataset(directory, dates, prices, assets, kind="synthetic",
                         source=f"Locally generated independent returns; numpy seed={seed}",
                         license_note="Project-generated test fixture; not market data",
                         adjustment="None; synthetic price paths",
                         deviations=["Synthetic three-asset universe; not paper data or performance evidence"])


@dataclass
class Samples:
    x: np.ndarray
    y: np.ndarray
    dates: np.ndarray
    train: np.ndarray
    validation: np.ndarray
    test: np.ndarray
    mean: np.ndarray
    scale: np.ndarray


def make_samples(dataset: Dataset, lookback: int, train_end: str, validation_end: str,
                 *, allow_single_test: bool = False) -> Samples:
    if not isinstance(allow_single_test, bool):
        raise ValueError("allow_single_test must be a boolean")
    if lookback < 2 or train_end >= validation_end:
        raise ValueError("Require lookback >= 2 and train_end < validation_end")
    if train_end not in dataset.dates or validation_end not in dataset.dates:
        raise ValueError("Split endpoints must exist in the dataset")
    prices = dataset.prices
    returns = np.zeros_like(prices)
    returns[1:] = prices[1:] / prices[:-1] - 1
    features = np.stack([prices, returns], axis=2).reshape(len(prices), -1)
    target_indices = np.arange(lookback, len(prices))
    dates = dataset.dates[target_indices]
    train = dates <= train_end
    validation = (dates > train_end) & (dates <= validation_end)
    test = dates > validation_end
    minimums = (2, 2, 1 if allow_single_test else 2)
    if any(np.count_nonzero(mask) < minimum for mask, minimum in zip((train, validation, test), minimums)):
        message = ("Training and validation need at least two target observations; test needs one"
                   if allow_single_test else "Every chronological split needs at least two target observations")
        raise ValueError(message)
    # Only rows used as inputs by training samples contribute to scaler fitting.
    last_training_target = target_indices[train][-1]
    fit = features[:last_training_target]
    mean = fit.mean(axis=0)
    scale = fit.std(axis=0)
    scale[scale < 1e-12] = 1.0
    normalized = (features - mean) / scale
    x = np.stack([normalized[i - lookback:i] for i in target_indices]).astype(np.float32)
    y = returns[target_indices].astype(np.float32)
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Feature/return conversion overflowed")
    return Samples(x, y, dates, train, validation, test, mean, scale)
