import hashlib
import json
from copy import deepcopy

import pytest

from portfolio_lab.service_contract import (
    SCHEMA_PATH, canonical_request, execute_synthetic_request, load_request,
    request_hash, validate_request,
)


EXAMPLE = SCHEMA_PATH.parent / "examples" / "synthetic-smoke.v1.json"


def example():
    return load_request(EXAMPLE)


def test_schema_is_closed_and_example_matches_it():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert set(schema["properties"]) == set(schema["required"])
    for section in (schema, schema["properties"]["dataset"],
                    schema["properties"]["model"], schema["properties"]["execution"]):
        assert section["type"] == "object"
        assert section["additionalProperties"] is False
        assert set(section["properties"]) == set(section["required"])
    assert validate_request(example()) == example()


@pytest.mark.parametrize("path,value", [
    (("contract_version",), 2),
    (("contract_version",), True),
    (("dataset", "kind"), "historical"),
    (("dataset", "observations"), 139),
    (("dataset", "observations"), 421),
    (("dataset", "seed"), -1),
    (("model", "epochs"), 0),
    (("model", "epochs"), 4),
    (("model", "lookback"), 9),
    (("execution", "cost_bps"), 1.5),
    (("execution", "seed"), True),
])
def test_invalid_requests_cannot_create_output(tmp_path, path, value):
    request = deepcopy(example())
    target = request
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValueError):
        execute_synthetic_request(request, tmp_path / "runs")
    assert not (tmp_path / "runs").exists()


def test_missing_extra_and_duplicate_fields_rejected(tmp_path):
    request = example()
    del request["model"]["epochs"]
    with pytest.raises(ValueError, match="missing"):
        validate_request(request)
    request = example()
    request["model"]["mystery"] = 1
    with pytest.raises(ValueError, match="unknown"):
        validate_request(request)
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(EXAMPLE.read_text(encoding="utf-8").replace(
        '"contract_version": 1,', '"contract_version": 1, "contract_version": 2,'),
        encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        load_request(duplicate)


def test_canonical_hash_ignores_key_order_and_matches_shared_fixture():
    request = example()
    reordered = {key: request[key] for key in reversed(request)}
    reordered["dataset"] = {key: request["dataset"][key]
                            for key in reversed(request["dataset"])}
    assert canonical_request(request) == canonical_request(reordered)
    assert request_hash(request) == request_hash(reordered)
    assert request_hash(request) == (EXAMPLE.parent / "synthetic-smoke.v1.sha256").read_text().strip()


def test_small_request_runs_and_retains_input_and_report(tmp_path):
    request = example()
    run_dir = execute_synthetic_request(request, tmp_path / "runs")
    assert json.loads((run_dir / "status.json").read_text())["state"] == "completed"
    assert (run_dir / "report.json").exists()
    assert (run_dir / "dataset" / "manifest.json").exists()
    assert json.loads((run_dir / "request.json").read_text()) == request
    assert hashlib.sha256((run_dir / "request.json").read_bytes()).hexdigest() == (
        run_dir / "request.sha256").read_text().strip()
    assert len(list((tmp_path / "runs").glob(".synthetic-input-*"))) == 0
