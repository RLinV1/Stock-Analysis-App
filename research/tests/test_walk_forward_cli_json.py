"""Unrun configuration parse failures must not dispatch any model work."""

import json
import sys

import pytest

from portfolio_lab import cli


@pytest.mark.parametrize("kind", ["duplicate", "nonfinite", "overflow"])
def test_ambiguous_or_nonfinite_walk_config_never_dispatches(tmp_path, monkeypatch, kind):
    settings = {"test_start": "2024-01-01", "test_end": "2024-01-03", "lookback": 10,
                "hidden_size": 4, "epochs": 1, "batch_size": 64, "learning_rate": 0.001,
                "seed": 7, "cost_bps": 0, "device": "cpu"}
    raw = json.dumps(settings)
    if kind == "duplicate":
        raw = raw[:-1] + ', "epochs": 1}'
    elif kind == "nonfinite":
        raw = raw.replace('0.001', 'NaN')
    else:
        raw = raw.replace('0.001', '1e9999')
    config = tmp_path / "config.json"
    config.write_text(raw, encoding="utf-8")
    def forbidden(*args, **kwargs):
        pytest.fail("Malformed JSON must fail before group/model dispatch")
    monkeypatch.setattr(cli, "run_walk_forward", forbidden)
    monkeypatch.setattr(sys, "argv", ["portfolio-lab", "walk-forward", str(tmp_path / "manifest.json"),
                                      "--config", str(config), "--output", str(tmp_path / "runs")])
    with pytest.raises(SystemExit) as stopped:
        cli.main()
    assert stopped.value.code == 2
    assert not (tmp_path / "runs").exists()
