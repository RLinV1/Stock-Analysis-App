"""Local CLI sharing the research runner with the planned Python job worker."""

import argparse
import json
from pathlib import Path

from .data import load_dataset, synthetic_dataset
from .runner import RunConfig, run_experiment


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
    args = parser.parse_args()
    try:
        if args.command == "synthetic":
            print(synthetic_dataset(args.output, args.observations))
        else:
            if args.config:
                config = RunConfig(**json.loads(args.config.read_text()))
            elif args.resume:
                config = RunConfig(**json.loads((args.resume / "manifest.json").read_text())["config"])
            else:
                dataset = load_dataset(args.dataset)
                pretest = int(len(dataset.dates) * 0.7)
                train_end = int(pretest * 0.9)
                config = RunConfig(str(dataset.dates[train_end - 1]), str(dataset.dates[pretest - 1]),
                                   epochs=args.epochs, seed=args.seed, cost_bps=args.cost_bps)
            print(run_experiment(args.dataset, config, args.output, resume=args.resume,
                                 stop_after_epochs=args.stop_after_epochs))
    except (ValueError, FileExistsError, FileNotFoundError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
