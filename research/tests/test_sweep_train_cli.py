"""Unrun training CLI dispatch source; executor is always stubbed."""

import json

import pytest

from portfolio_lab import sweep_train_cli as cli


def config():
    return {
        "schema_version": 1,
        "model": {"test_start": "2024-01-01", "test_end": "2024-01-03", "lookback": 10,
                  "hidden_size": 8, "epochs": 1, "batch_size": 32, "learning_rate": 0.001, "device": "cpu"},
        "sweep": {"seeds": [7, 3], "costs_bps": [5, 0], "max_runs": 4},
    }


def test_config_has_complete_common_settings_and_preserves_grid():
    model, settings = cli.parse_config(config())
    assert model.lookback == 10
    assert not hasattr(model, "seed")
    assert not hasattr(model, "cost_bps")
    assert settings.seeds == (7, 3)
    assert settings.costs_bps == (5, 0)
    assert settings.max_runs == 4


@pytest.mark.parametrize("mutate", [
    lambda payload: payload.pop("schema_version"),
    lambda payload: payload.update(schema_version=True),
    lambda payload: payload.update(schema_version=2),
    lambda payload: payload.update(unknown=1),
    lambda payload: payload["model"].pop("device"),
    lambda payload: payload["model"].update(seed=7),
    lambda payload: payload["model"].update(cost_bps=1),
    lambda payload: payload["sweep"].pop("max_runs"),
    lambda payload: payload["sweep"].update(seeds=[7, 7]),
    lambda payload: payload["sweep"].update(costs_bps=[True]),
    lambda payload: payload["sweep"].update(max_runs=3),
])
def test_malformed_or_incomplete_config_is_rejected(mutate):
    payload = config()
    mutate(payload)
    with pytest.raises(ValueError):
        cli.parse_config(payload)


@pytest.mark.parametrize("state,successful,exit_code", [
    ("completed", True, 0), ("completed_with_failures", False, 1),
])
def test_cli_dispatches_explicit_inputs_and_reports_completion(tmp_path, monkeypatch, capsys, state, successful, exit_code):
    request, dataset, output = tmp_path / "config.json", tmp_path / "manifest.json", tmp_path / "runs"
    request.write_text(json.dumps(config()), encoding="utf-8")
    captured = []
    def run(actual_dataset, model, settings, actual_output):
        captured.append((actual_dataset, model, settings, actual_output))
        group = actual_output / "sweep-stub"
        group.mkdir(parents=True)
        (group / "status.json").write_text(json.dumps({"state": state, "all_successful": successful,
                                                      "coverage_complete": True}), encoding="utf-8")
        return group
    monkeypatch.setattr(cli, "run_sweep", run)
    assert cli.main(["--dataset", str(dataset), "--config", str(request), "--output", str(output)]) == exit_code
    assert capsys.readouterr().out.strip() == str(output / "sweep-stub")
    assert captured[0][0] == dataset
    assert captured[0][3] == output
    assert captured[0][1].epochs == 1
    assert captured[0][2].seeds == (7, 3)


def test_invalid_json_never_dispatches_training(tmp_path, monkeypatch):
    request = tmp_path / "config.json"
    request.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
    monkeypatch.setattr(cli, "run_sweep", lambda *args: pytest.fail("must not dispatch"))
    with pytest.raises(SystemExit) as stopped:
        cli.main(["--dataset", str(tmp_path / "manifest.json"), "--config", str(request), "--output", str(tmp_path / "runs")])
    assert stopped.value.code == 2
    assert not (tmp_path / "runs").exists()


@pytest.mark.parametrize("status", [
    {"state": "running", "all_successful": False, "coverage_complete": False},
    {"state": "completed", "all_successful": False, "coverage_complete": True},
    {"state": "completed_with_failures", "all_successful": True, "coverage_complete": True},
])
def test_inconsistent_or_partial_result_is_never_cli_success(tmp_path, monkeypatch, status):
    request = tmp_path / "config.json"
    request.write_text(json.dumps(config()), encoding="utf-8")
    group = tmp_path / "group"
    group.mkdir()
    (group / "status.json").write_text(json.dumps(status), encoding="utf-8")
    monkeypatch.setattr(cli, "run_sweep", lambda *args: group)
    with pytest.raises(SystemExit) as stopped:
        cli.main(["--dataset", str(tmp_path / "manifest.json"), "--config", str(request), "--output", str(tmp_path / "runs")])
    assert stopped.value.code == 2


def test_duplicate_completion_status_cannot_be_cli_success(tmp_path, monkeypatch):
    request = tmp_path / "config.json"
    request.write_text(json.dumps(config()), encoding="utf-8")
    group = tmp_path / "group"
    group.mkdir()
    (group / "status.json").write_text(
        '{"state":"completed","coverage_complete":true,"all_successful":true,"all_successful":true}',
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "run_sweep", lambda *args: group)
    with pytest.raises(SystemExit) as stopped:
        cli.main(["--dataset", str(tmp_path / "manifest.json"), "--config", str(request), "--output", str(tmp_path / "runs")])
    assert stopped.value.code == 2
