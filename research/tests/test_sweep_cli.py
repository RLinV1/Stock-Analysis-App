"""Offline JSON contract and output protection regression source."""

import json

import pytest

from portfolio_lab.sweep_cli import main, summarize_document, write_summary


def document():
    return {
        "schema_version": 1,
        "settings": {"seeds": [7], "costs_bps": [0], "max_runs": 1},
        "records": [{"seed": 7, "cost_bps": 0, "status": "failed", "reason": "training failed"}],
    }


def test_explicit_document_retains_failure_without_claiming_success():
    summary = summarize_document(document())
    assert summary["schema_version"] == 1
    assert summary["coverage_complete"] is True
    assert summary["all_successful"] is False
    assert summary["records"][0]["reason"] == "training failed"
    assert summary["context"] is None


@pytest.mark.parametrize("mutate", [
    lambda payload: payload.pop("schema_version"),
    lambda payload: payload.update(schema_version=True),
    lambda payload: payload.update(schema_version=1.0),
    lambda payload: payload.update(schema_version=2),
    lambda payload: payload.update(unknown="typo"),
    lambda payload: payload["settings"].pop("max_runs"),
    lambda payload: payload["settings"].update(seed=7),
    lambda payload: payload["settings"].update(seeds="7"),
    lambda payload: payload["settings"].update(costs_bps=0),
    lambda payload: payload.update(records={}),
])
def test_document_rejects_missing_unknown_and_mistyped_fields(mutate):
    payload = document()
    mutate(payload)
    with pytest.raises(ValueError):
        summarize_document(payload)


def test_summary_is_written_only_after_complete_validation(tmp_path):
    source, output = tmp_path / "input.json", tmp_path / "summary.json"
    payload = document()
    payload["records"] = []
    source.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="incomplete"):
        write_summary(source, output)
    assert not output.exists()


def test_existing_evidence_is_not_overwritten(tmp_path):
    source, output = tmp_path / "input.json", tmp_path / "summary.json"
    source.write_text(json.dumps(document()), encoding="utf-8")
    output.write_bytes(b"existing evidence\n")
    with pytest.raises(FileExistsError):
        write_summary(source, output)
    assert output.read_bytes() == b"existing evidence\n"


def test_input_path_cannot_be_overwritten(tmp_path):
    source = tmp_path / "input.json"
    original = json.dumps(document()).encode("utf-8")
    source.write_bytes(original)
    with pytest.raises(FileExistsError):
        write_summary(source, source)
    assert source.read_bytes() == original


@pytest.mark.parametrize("raw", [
    '{"schema_version": 1, "schema_version": 1, "settings": {}, "records": []}',
    '{"schema_version": 1, "settings": {"max_runs": 1, "max_runs": 2}, "records": []}',
    '{"schema_version": 1, "settings": {}, "records": [NaN]}',
    '{"schema_version": 1, "settings": {}, "records": [Infinity]}',
    '{"schema_version": 1, "settings": {}, "records": [-Infinity]}',
    '{"schema_version": 1,',
])
def test_ambiguous_or_nonstandard_json_creates_no_output(tmp_path, raw):
    source, output = tmp_path / "input.json", tmp_path / "summary.json"
    source.write_text(raw, encoding="utf-8")
    with pytest.raises(ValueError):
        write_summary(source, output)
    assert not output.exists()


def test_standalone_entry_point_writes_strict_json(tmp_path, capsys):
    source, output = tmp_path / "input.json", tmp_path / "summary.json"
    source.write_text(json.dumps(document()), encoding="utf-8")
    assert main(["--input", str(source), "--output", str(output)]) == 0
    assert capsys.readouterr().out.strip() == str(output)
    summary = json.loads(output.read_text(encoding="utf-8"))
    assert summary["failed"] == 1
    assert summary["all_successful"] is False
    assert output.read_bytes().endswith(b"\n")


def test_cli_reports_invalid_input_without_creating_output(tmp_path, capsys):
    source, output = tmp_path / "input.json", tmp_path / "summary.json"
    source.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit) as stopped:
        main(["--input", str(source), "--output", str(output)])
    assert stopped.value.code == 2
    assert "input requires exactly" in capsys.readouterr().err
    assert not output.exists()
