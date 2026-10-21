"""Explicit local sweep training entry point; unverified integration source."""

from __future__ import annotations

import argparse
from dataclasses import fields
from pathlib import Path
from typing import Sequence

from .sweep import SweepSettings, plan_candidates
from .sweep_cli import load_document
from .sweep_runner import SweepModelConfig, run_sweep


def parse_config(document: object) -> tuple[SweepModelConfig, SweepSettings]:
    if not isinstance(document, dict) or set(document) != {"schema_version", "model", "sweep"}:
        raise ValueError("training config requires exactly schema_version, model, and sweep")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise ValueError("only integer schema_version 1 is supported")
    model, sweep = document["model"], document["sweep"]
    if not isinstance(model, dict) or set(model) != {field.name for field in fields(SweepModelConfig)}:
        raise ValueError("model must contain every declared common setting and no extra fields")
    if not isinstance(sweep, dict) or set(sweep) != {"seeds", "costs_bps", "max_runs"}:
        raise ValueError("sweep requires exactly seeds, costs_bps, and max_runs")
    if not isinstance(sweep["seeds"], list) or not isinstance(sweep["costs_bps"], list):
        raise ValueError("seeds and costs_bps must be JSON arrays")
    settings = SweepSettings(**sweep)
    plan_candidates(settings)
    return SweepModelConfig(**model), settings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an explicit local seed/cost walk-forward sweep.")
    parser.add_argument("--dataset", type=Path, required=True, help="validated dataset manifest")
    parser.add_argument("--config", type=Path, required=True, help="complete version 1 model/sweep JSON")
    parser.add_argument("--output", type=Path, required=True, help="root for a new owned sweep group")
    arguments = parser.parse_args(argv)
    try:
        model, settings = parse_config(load_document(arguments.config))
        group = run_sweep(arguments.dataset, model, settings, arguments.output)
        status = load_document(group / "status.json")
        if not isinstance(status, dict) or status.get("coverage_complete") is not True:
            raise ValueError("executor did not return complete coverage")
        if status.get("state") == "completed" and status.get("all_successful") is True:
            exit_status = 0
        elif status.get("state") == "completed_with_failures" and status.get("all_successful") is False:
            exit_status = 1
        else:
            raise ValueError("executor returned inconsistent completion status")
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    print(group)
    return exit_status


if __name__ == "__main__":
    raise SystemExit(main())
