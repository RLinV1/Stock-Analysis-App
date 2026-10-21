"""Offline summary entry point; this module does not orchestrate training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .json_io import load_json
from .sweep import SweepSettings, summarize_candidates


def summarize_document(document: object) -> dict:
    """Interpret a complete, explicitly versioned input without implicit defaults."""
    if not isinstance(document, dict) or set(document) != {"schema_version", "settings", "records"}:
        raise ValueError("input requires exactly schema_version, settings, and records")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise ValueError("only integer schema_version 1 is supported")
    settings = document["settings"]
    if not isinstance(settings, dict) or set(settings) != {"seeds", "costs_bps", "max_runs"}:
        raise ValueError("settings require exactly seeds, costs_bps, and max_runs")
    if not isinstance(settings["seeds"], list) or not isinstance(settings["costs_bps"], list):
        raise ValueError("seeds and costs_bps must be JSON arrays")
    records = document["records"]
    if not isinstance(records, list):
        raise ValueError("records must be a JSON array")
    summary = summarize_candidates(SweepSettings(**settings), records)
    return {"schema_version": 1, **summary}


def load_document(input_path: Path):
    """Load strict JSON shared by offline summaries and training requests."""
    return load_json(input_path)


def write_summary(input_path: Path, output_path: Path) -> Path:
    """Validate and serialize fully before exclusively creating the output."""
    document = load_document(input_path)
    summary = summarize_document(document)
    serialized = json.dumps(summary, indent=2, allow_nan=False) + "\n"
    # Exclusive creation prevents accidental replacement of input or prior evidence.
    with Path(output_path).open("x", encoding="utf-8", newline="\n") as target:
        target.write(serialized)
    return Path(output_path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize explicit supplied research sweep results; no training.")
    parser.add_argument("--input", type=Path, required=True, help="version 1 input JSON document")
    parser.add_argument("--output", type=Path, required=True, help="new summary JSON file; parent must exist")
    arguments = parser.parse_args(argv)
    try:
        path = write_summary(arguments.input, arguments.output)
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
