"""Bounded local synthetic request adapter; not a general JSON Schema engine."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from .data import load_dataset, synthetic_dataset
from .runner import RunConfig, run_experiment


SCHEMA_PATH = Path(__file__).resolve().parents[3] / "contracts" / "synthetic-run-request.v1.schema.json"
MAX_REQUEST_BYTES = 8192


def _check(value: Any, schema: dict, field: str) -> None:
    """Check only the closed object/const/integer subset used by request v1."""
    kind = schema["type"]
    if kind == "object":
        if not isinstance(value, dict):
            raise ValueError(f"{field} must be an object")
        properties = schema["properties"]
        missing = set(schema["required"]) - value.keys()
        extra = value.keys() - properties.keys()
        if missing:
            raise ValueError(f"{field} missing: {', '.join(sorted(missing))}")
        if extra:
            raise ValueError(f"{field} unknown: {', '.join(sorted(extra))}")
        for name, child in properties.items():
            _check(value[name], child, f"{field}.{name}")
    elif kind == "integer":
        if type(value) is not int:
            raise ValueError(f"{field} must be an integer")
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError(f"{field} below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValueError(f"{field} above maximum {schema['maximum']}")
    elif kind == "string":
        if type(value) is not str:
            raise ValueError(f"{field} must be a string")
    else:
        raise ValueError(f"Unsupported schema type at {field}")
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{field} must be {schema['const']!r}")


def validate_request(request: Any) -> dict:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    _check(request, schema, "request")
    return request


def canonical_request(request: Any) -> bytes:
    validate_request(request)
    return json.dumps(request, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def request_hash(request: Any) -> str:
    return hashlib.sha256(canonical_request(request)).hexdigest()


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate request key: {key}")
        result[key] = value
    return result


def load_request(path: Path) -> dict:
    content = path.read_bytes()
    if len(content) > MAX_REQUEST_BYTES:
        raise ValueError("Synthetic request exceeds 8192 bytes")
    request = json.loads(content.decode("utf-8"), object_pairs_hook=_unique_pairs,
                         parse_constant=lambda value: (_ for _ in ()).throw(
                             ValueError(f"Non-finite request number: {value}")))
    return validate_request(request)


def execute_synthetic_request(request: dict, output_root: Path) -> Path:
    accepted = canonical_request(request)
    digest = hashlib.sha256(accepted).hexdigest()
    output_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".synthetic-input-", dir=output_root) as staging:
        dataset_path = synthetic_dataset(Path(staging) / "dataset",
                                         request["dataset"]["observations"],
                                         request["dataset"]["seed"])
        dates = load_dataset(dataset_path).dates
        pretest = int(len(dates) * 0.7)
        train_end = int(pretest * 0.9)
        config = RunConfig(
            train_end=str(dates[train_end - 1]),
            validation_end=str(dates[pretest - 1]),
            lookback=request["model"]["lookback"],
            hidden_size=request["model"]["hidden_size"],
            epochs=request["model"]["epochs"],
            batch_size=32,
            learning_rate=0.001,
            seed=request["execution"]["seed"],
            cost_bps=request["execution"]["cost_bps"],
            device="cpu",
        )
        run_dir = run_experiment(dataset_path, config, output_root)
    (run_dir / "request.json").write_bytes(accepted)
    (run_dir / "request.sha256").write_text(digest + "\n", encoding="ascii")
    return run_dir
