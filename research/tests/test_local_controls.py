"""Local config boundary regressions; source only, execution remains unrun."""

import json
import sys
from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest

from portfolio_lab import cli, runner
from portfolio_lab.runner import RunConfig


BASE = {"train_end": "2020-01-01", "validation_end": "2020-02-01"}


def forbidden(*args, **kwargs):
    pytest.fail("Invalid local controls must reject before dispatch/runtime access")


def invoke(tmp_path, monkeypatch, raw, source):
    output = tmp_path / "runs"
    arguments = ["portfolio-lab", "run", str(tmp_path / "missing-dataset.json"), "--output", str(output)]
    if source == "explicit":
        config_path = tmp_path / "config.json"
        config_path.write_bytes(raw if isinstance(raw, bytes) else raw.encode("utf-8"))
        arguments += ["--config", str(config_path)]
        retained = {config_path: config_path.read_bytes()}
    else:
        resume = tmp_path / "saved-run"
        resume.mkdir()
        manifest = resume / "manifest.json"
        manifest.write_bytes(raw if isinstance(raw, bytes) else raw.encode("utf-8"))
        checkpoint = resume / "checkpoint.pt"
        checkpoint.write_bytes(b"existing evidence; must not be loaded")
        arguments += ["--resume", str(resume)]
        retained = {manifest: manifest.read_bytes(), checkpoint: checkpoint.read_bytes()}
    monkeypatch.setattr(sys, "argv", arguments)
    return output, retained


@pytest.mark.parametrize("source", ["explicit", "resume"])
@pytest.mark.parametrize("kind", ["duplicate", "nonfinite", "overflow", "array", "null", "missing", "unknown", "utf8"])
def test_invalid_json_or_mapping_is_usage_error_without_dispatch(tmp_path, monkeypatch, capsys, source, kind):
    settings = json.dumps(BASE)
    if kind == "duplicate":
        settings = settings[:-1] + ', "train_end": "2020-01-01"}'
    elif kind == "nonfinite":
        settings = settings[:-1] + ', "learning_rate": NaN}'
    elif kind == "overflow":
        settings = settings[:-1] + ', "learning_rate": 1e9999}'
    elif kind == "array":
        settings = "[]"
    elif kind == "null":
        settings = "null"
    elif kind == "missing":
        settings = "{}"
    elif kind == "unknown":
        settings = settings[:-1] + ', "unknown_option": true}'
    raw = settings if source == "explicit" else '{"config": ' + settings + '}'
    if kind == "utf8":
        raw = b"\xff"
    output, retained = invoke(tmp_path, monkeypatch, raw, source)
    monkeypatch.setattr(cli, "run_experiment", forbidden)
    monkeypatch.setattr(cli, "load_dataset", forbidden)
    monkeypatch.setattr(runner.torch.cuda, "is_available", forbidden)
    with pytest.raises(SystemExit) as stopped:
        cli.main()
    assert stopped.value.code == 2
    assert "Error:" in capsys.readouterr().err
    assert not output.exists()
    assert {file: file.read_bytes() for file in retained} == retained


@pytest.mark.parametrize("raw", ['{}', '{"config": null}', '{"config": []}',
                                  '{"config": {}, "config": {}}',
                                  '{"config": {}, "unused": {"x": 1, "x": 1}}'])
def test_resume_requires_unambiguous_config_object(tmp_path, monkeypatch, raw):
    output, retained = invoke(tmp_path, monkeypatch, raw, "resume")
    monkeypatch.setattr(cli, "run_experiment", forbidden)
    with pytest.raises(SystemExit) as stopped:
        cli.main()
    assert stopped.value.code == 2
    assert not output.exists()
    assert {file: file.read_bytes() for file in retained} == retained


@pytest.mark.parametrize("source", ["explicit", "resume"])
@pytest.mark.parametrize("field,value", [
    ("epochs", True), ("epochs", 1.5), ("batch_size", 64.0), ("lookback", False),
    ("hidden_size", "4"), ("seed", 7.0), ("cost_bps", True),
    ("learning_rate", 10**400), ("device", []), ("train_end", []),
    ("validation_end", 20200201), ("normalization", {}), ("objective_window", []),
])
def test_bad_control_types_never_dispatch_from_cli(tmp_path, monkeypatch, source, field, value):
    settings = {**BASE, "device": "cuda", field: value}
    raw = json.dumps(settings if source == "explicit" else {"config": settings})
    output, retained = invoke(tmp_path, monkeypatch, raw, source)
    monkeypatch.setattr(cli, "run_experiment", forbidden)
    monkeypatch.setattr(cli, "load_dataset", forbidden)
    monkeypatch.setattr(runner.torch.cuda, "is_available", forbidden)
    with pytest.raises(SystemExit) as stopped:
        cli.main()
    assert stopped.value.code == 2
    assert not output.exists()
    assert {file: file.read_bytes() for file in retained} == retained


@pytest.mark.parametrize("field,value", [
    ("epochs", True), ("epochs", 2.0), ("batch_size", "64"), ("hidden_size", []),
    ("lookback", 10.5), ("seed", False), ("learning_rate", True),
    ("learning_rate", float("nan")), ("learning_rate", 10**400),
    ("cost_bps", True), ("cost_bps", float("inf")), ("device", {}),
    ("train_end", None), ("validation_end", []),
])
def test_default_direct_run_bad_types_reject_before_runtime_and_preserve_evidence(tmp_path, monkeypatch, field, value):
    resume = tmp_path / "saved-run"
    resume.mkdir()
    for name in ("manifest.json", "status.json", "checkpoint.pt"):
        (resume / name).write_bytes(b"existing evidence")
    before = {file: file.read_bytes() for file in resume.iterdir()}
    monkeypatch.setattr(runner, "load_dataset", forbidden)
    monkeypatch.setattr(runner, "runtime_versions", forbidden)
    monkeypatch.setattr(runner, "_train", forbidden)
    monkeypatch.setattr(runner.torch.cuda, "is_available", forbidden)
    config = replace(RunConfig(**BASE, device="cuda"), **{field: value})
    with pytest.raises(ValueError, match=field):
        runner.run_experiment(tmp_path / "missing.json", config, tmp_path / "runs", resume=resume)
    assert {file: file.read_bytes() for file in resume.iterdir()} == before
    assert not (tmp_path / "runs").exists()


@pytest.mark.parametrize("source", ["explicit", "resume"])
@pytest.mark.parametrize("controls", [{}, {"normalization": "raw", "objective_window": "full-training"},
                                       {"learning_rate": 1, "cost_bps": 0}])
def test_valid_local_config_is_forwarded_with_existing_defaults(tmp_path, monkeypatch, source, controls):
    settings = {**BASE, **controls}
    raw = json.dumps(settings if source == "explicit" else {"config": settings})
    output, retained = invoke(tmp_path, monkeypatch, raw, source)
    captured = []
    def capture(dataset, config, target, **kwargs):
        captured.append((dataset, config, target, kwargs))
        return target / "stub-no-training"
    monkeypatch.setattr(cli, "run_experiment", capture)
    monkeypatch.setattr(cli, "load_dataset", forbidden)
    monkeypatch.setattr(runner.torch.cuda, "is_available", forbidden)
    cli.main()
    assert len(captured) == 1
    assert asdict(captured[0][1]) == asdict(RunConfig(**settings))
    assert captured[0][2] == output
    assert captured[0][3]["resume"] == (tmp_path / "saved-run" if source == "resume" else None)
    assert {file: file.read_bytes() for file in retained} == retained


def test_bounded_cli_defaults_are_preserved_without_training(tmp_path, monkeypatch):
    dates = [f"date-{index}" for index in range(100)]
    monkeypatch.setattr(cli, "load_dataset", lambda _: SimpleNamespace(dates=dates))
    captured = []
    monkeypatch.setattr(cli, "run_experiment", lambda dataset, config, output, **kwargs: captured.append(config))
    monkeypatch.setattr(sys, "argv", ["portfolio-lab", "run", str(tmp_path / "manifest.json")])
    cli.main()
    assert captured == [RunConfig("date-62", "date-69", epochs=3, seed=7, cost_bps=1.0)]
