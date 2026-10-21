"""Local CLI sharing the research runner with the planned Python job worker."""

import argparse
import json
from pathlib import Path

from .data import load_dataset, synthetic_dataset
from .json_io import load_json, load_json_object
from .runner import RunConfig, run_experiment
from .repeat import repeat_experiment
from .service_contract import execute_synthetic_request, load_request
from .walk_forward import WalkForwardConfig, run_walk_forward


def _run_config(settings: object) -> RunConfig:
    """Reject malformed local settings before dispatching any experiment."""
    if not isinstance(settings, dict):
        raise ValueError("Run config must be a JSON object")
    try:
        config = RunConfig(**settings)
    except TypeError as error:
        raise ValueError("Run config must contain required split dates and only declared RunConfig fields") from error
    config.validate()
    return config


def main() -> None:
    parser = argparse.ArgumentParser(description="Paper-inspired portfolio research")
    commands = parser.add_subparsers(dest="command", required=True)
    synthetic = commands.add_parser("synthetic", help="Generate a clearly labeled synthetic fixture")
    synthetic.add_argument("output", type=Path)
    synthetic.add_argument("--observations", type=int, default=420)
    run = commands.add_parser("run", help="Train and evaluate one immutable experiment")
    run.add_argument("dataset", type=Path, help="Dataset manifest JSON")
    run.add_argument("--config", type=Path, help="RunConfig JSON, or use bounded CLI defaults")
    run.add_argument("--output", type=Path, default=Path("runs"))
    run.add_argument("--epochs", type=int, default=3)
    run.add_argument("--seed", type=int, default=7)
    run.add_argument("--cost-bps", type=float, default=1.0)
    run.add_argument("--resume", type=Path)
    run.add_argument("--stop-after-epochs", type=int)
    repeat = commands.add_parser("repeat", help="Repeat a completed local A0 run and compare its outputs")
    repeat.add_argument("reference", type=Path, help="Completed run directory, including its copied dataset")
    repeat.add_argument("--output", type=Path, default=Path("runs"))
    service_run = commands.add_parser("synthetic-run", help="Execute a bounded versioned synthetic request locally")
    service_run.add_argument("request", type=Path, help="Synthetic request v1 JSON")
    service_run.add_argument("--output", type=Path, default=Path("runs"))
    walk = commands.add_parser("walk-forward", help="Execute explicit frozen-fold research locally")
    walk.add_argument("dataset", type=Path, help="Validated dataset manifest JSON")
    walk.add_argument("--config", type=Path, required=True,
                      help="Complete WalkForwardConfig JSON; no new numerical defaults are adopted")
    walk.add_argument("--output", type=Path, default=Path("runs"))
    args = parser.parse_args()
    try:
        if args.command == "synthetic":
            print(synthetic_dataset(args.output, args.observations))
        elif args.command == "repeat":
            comparison_path = repeat_experiment(args.reference, args.output)
            print(comparison_path)
            outcome = json.loads(comparison_path.read_text(encoding="utf-8"))["outcome"]
            if outcome != "matched":
                parser.exit(1, f"Repeat outcome: {outcome}; see saved comparison report.\n")
        elif args.command == "synthetic-run":
            print(execute_synthetic_request(load_request(args.request), args.output))
        elif args.command == "walk-forward":
            settings = load_json(args.config)
            if not isinstance(settings, dict):
                raise ValueError("Walk-forward config must be a complete JSON object")
            try:
                config = WalkForwardConfig(**settings)
            except TypeError as error:
                raise ValueError("Walk-forward config must contain exactly the declared fields") from error
            print(run_walk_forward(args.dataset, config, args.output))
        else:
            if args.config:
                config = _run_config(load_json_object(args.config))
            elif args.resume:
                manifest = load_json_object(args.resume / "manifest.json")
                config = _run_config(manifest.get("config"))
            else:
                dataset = load_dataset(args.dataset)
                pretest = int(len(dataset.dates) * 0.7)
                train_end = int(pretest * 0.9)
                config = RunConfig(str(dataset.dates[train_end - 1]), str(dataset.dates[pretest - 1]),
                                   epochs=args.epochs, seed=args.seed, cost_bps=args.cost_bps)
                config.validate()
            print(run_experiment(args.dataset, config, args.output, resume=args.resume,
                                 stop_after_epochs=args.stop_after_epochs))
    except (ValueError, FileExistsError, FileNotFoundError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
