"""Single-process training with immutable run provenance and epoch checkpoints."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import random
import shutil
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import psutil
import torch
from filelock import FileLock

from .data import file_hash, load_dataset, make_samples, save_json
from .metrics import CONVENTIONS, baseline_weights, evaluate
from .model import Allocator, negative_sharpe
from .provenance import source_revision


class RunStopped(Exception):
    """A caller's stop request ended training at an epoch boundary.

    The run directory is left paused, like stop_after_epochs, with no report.
    """

    def __init__(self, run_dir: Path, epoch: int):
        super().__init__(f"Run stopped by request after epoch {epoch}")
        self.run_dir = run_dir
        self.epoch = epoch


@dataclass(frozen=True)
class RunConfig:
    train_end: str
    validation_end: str
    lookback: int = 50
    hidden_size: int = 64
    epochs: int = 100
    batch_size: int = 64
    learning_rate: float = 0.001
    seed: int = 7
    cost_bps: float = 1.0
    device: str = "cpu"

    def validate(self) -> None:
        if not 1 <= self.epochs <= 1000 or self.batch_size < 2:
            raise ValueError("Require 1..1000 epochs and batch_size >= 2")
        if not 1 <= self.hidden_size <= 1024 or not 2 <= self.lookback:
            raise ValueError("Invalid hidden size or lookback")
        if not math.isfinite(self.learning_rate) or not 0 < self.learning_rate <= 1:
            raise ValueError("Invalid learning rate")
        if not math.isfinite(self.cost_bps) or not 0 <= self.cost_bps <= 100:
            raise ValueError("Cost must be between 0 and 100 bps")
        if not 0 <= self.seed < 2**32:
            raise ValueError("Seed must fit an unsigned 32-bit integer")
        if self.device not in {"cpu", "cuda"}:
            raise ValueError("Device must be cpu or cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA requested but unavailable; use cpu")


def source_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def runtime_versions() -> dict:
    return {"python": platform.python_version(), "platform": platform.platform(),
            **{name: importlib.metadata.version(name)
               for name in ("torch", "numpy", "psutil", "filelock")}}


def checkpoint_save(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    torch.save(value, temporary)
    temporary.replace(path)


def _predict(model: Allocator, x: np.ndarray, device: str, batch_size: int) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        return np.concatenate([model(torch.from_numpy(x[i:i + batch_size]).to(device)).cpu().numpy()
                               for i in range(0, len(x), batch_size)])


def run_experiment(dataset_path: Path, config: RunConfig, output_root: Path,
                   *, resume: Path | None = None, stop_after_epochs: int | None = None,
                   should_stop: Callable[[], bool] | None = None) -> Path:
    """Train and evaluate one run.

    `should_stop` is polled before the first epoch and after each epoch's
    checkpoint is written; True pauses the run and raises RunStopped. It is
    not part of the run identity, so it never changes results or manifests.
    """
    config.validate()
    if stop_after_epochs is not None and stop_after_epochs < 1:
        raise ValueError("stop_after_epochs must be positive")
    dataset = load_dataset(dataset_path)
    samples = make_samples(dataset, config.lookback, config.train_end, config.validation_end)
    versions = runtime_versions()
    identity = {"config": asdict(config), "dataset": dataset.manifest,
                "dataset_manifest_sha256": file_hash(dataset_path),
                "source_sha256": source_fingerprint(), "versions": versions}
    identity_hash = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    if resume is None:
        output_root.mkdir(parents=True, exist_ok=True)
        run_dir = output_root / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:12])
        run_dir.mkdir(exist_ok=False)
    else:
        run_dir = resume.resolve()
        if not run_dir.is_dir():
            raise ValueError("Resume run directory does not exist")
    # A retry or second process cannot race the same run's checkpoint/report writes.
    with FileLock(str(run_dir / ".run.lock"), timeout=0):
        if resume is not None:
            manifest = json.loads((run_dir / "manifest.json").read_text())
            if manifest["identity_sha256"] != identity_hash:
                raise ValueError("Resume configuration, dataset, source, or environment mismatch")
            if json.loads((run_dir / "status.json").read_text())["state"] == "completed":
                raise ValueError("Completed runs are immutable; start a new run")
        else:
            manifest = {"schema_version": 1, "run_id": run_dir.name,
                        "created_at": datetime.now(timezone.utc).isoformat(), **identity,
                        "identity_sha256": identity_hash,
                        "source_revision": source_revision(),
                        "method_label": "synthetic-smoke" if dataset.manifest["kind"] == "synthetic" else "paper-inspired",
                        "conventions": CONVENTIONS,
                        "scaler": {"mean": samples.mean.tolist(), "scale": samples.scale.tolist()},
                        "split_counts": {name: int(getattr(samples, name).sum())
                                         for name in ("train", "validation", "test")},
                        "split_targets": {name: [str(samples.dates[getattr(samples, name)][0]),
                                                  str(samples.dates[getattr(samples, name)][-1])]
                                          for name in ("train", "validation", "test")},
                        "hardware": {"machine": platform.machine(), "processor": platform.processor(),
                                     "logical_cpus": psutil.cpu_count(), "ram_bytes": psutil.virtual_memory().total,
                                     "device": config.device,
                                     "gpu": torch.cuda.get_device_name(0) if config.device == "cuda" else None},
                        "determinism": "one thread; same code/data/environment/device; numerical tolerance 1e-7",
                        "deviations": [*dataset.manifest["deviations"],
                                       "Single fixed holdout; no two-year rolling retraining",
                                       "Daily equal-weight and 60/40 baselines; not full paper suite",
                                       "Train-only feature standardization; no volatility scaling",
                                       "Idealized close execution and L1 target turnover, including initial entry"]}
            save_json(run_dir / "manifest.json", manifest)
            (run_dir / "dataset").mkdir()
            shutil.copyfile(dataset.manifest_path, run_dir / "dataset" / "manifest.json")
            shutil.copyfile(dataset.manifest_path.parent / dataset.manifest["csv"],
                            run_dir / "dataset" / dataset.manifest["csv"])
        try:
            _train(run_dir, dataset, samples, config, identity_hash, resume is not None,
                   stop_after_epochs, should_stop)
        except RunStopped:
            # _train already recorded the paused, resumable state.
            raise
        except Exception as exc:
            save_json(run_dir / "status.json", {"state": "failed", "error_type": type(exc).__name__,
                                                "error": str(exc), "checkpoint_available": (run_dir / "checkpoint.pt").exists()})
            raise
    return run_dir


def _train(run_dir, dataset, samples, config, identity_hash, resuming, stop_after_epochs,
           should_stop=None):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    model = Allocator(len(dataset.symbols), config.hidden_size).to(config.device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    start_epoch, history, best_loss, best_state, best_epoch = 0, [], float("inf"), None, None
    accumulated_seconds, peak_rss = 0.0, psutil.Process().memory_info().rss
    if resuming:
        state = torch.load(run_dir / "checkpoint.pt", map_location="cpu", weights_only=True)
        if state["identity_sha256"] != identity_hash:
            raise ValueError("Checkpoint identity mismatch")
        model.load_state_dict(state["model"])
        optimizer.load_state_dict(state["optimizer"])
        torch.set_rng_state(state["torch_rng"])
        if config.device == "cuda":
            torch.cuda.set_rng_state_all(state["cuda_rng"])
        random.setstate(state["python_rng"])
        ns = state["numpy_rng"]
        np.random.set_state((ns[0], np.array(ns[1], dtype=np.uint32), ns[2], ns[3], ns[4]))
        start_epoch, history = state["epoch"], state["history"]
        best_loss, best_state, best_epoch = state["best_loss"], state["best_model"], state["best_epoch"]
        accumulated_seconds, peak_rss = state["elapsed_seconds"], state["peak_observed_rss_bytes"]
    start = time.perf_counter()
    train_x, train_y = samples.x[samples.train], samples.y[samples.train]
    validation_y = torch.from_numpy(samples.y[samples.validation])
    target_epoch = config.epochs if stop_after_epochs is None else min(config.epochs, start_epoch + stop_after_epochs)
    save_json(run_dir / "status.json", {"state": "running", "epoch": start_epoch, "epoch_budget": config.epochs})
    for epoch in range(start_epoch, target_epoch):
        # Epoch boundary: the previous epoch's checkpoint and status are durable.
        if should_stop is not None and should_stop():
            save_json(run_dir / "status.json", {"state": "paused", "epoch": epoch,
                                                "epoch_budget": config.epochs,
                                                "reason": "stop_requested"})
            raise RunStopped(run_dir, epoch)
        model.train()
        losses = []
        batch_start = 0
        while batch_start < len(train_x):
            end = min(batch_start + config.batch_size, len(train_x))
            if len(train_x) - end == 1:
                end += 1
            x = torch.from_numpy(train_x[batch_start:end]).to(config.device)
            y = torch.from_numpy(train_y[batch_start:end]).to(config.device)
            optimizer.zero_grad()
            loss = negative_sharpe(model(x), y)
            if not torch.isfinite(loss):
                raise ValueError("Training objective became nonfinite")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
            batch_start = end
        validation_weights = torch.from_numpy(_predict(model, samples.x[samples.validation], config.device, config.batch_size))
        val_loss = float(negative_sharpe(validation_weights, validation_y))
        if not math.isfinite(val_loss):
            raise ValueError("Validation objective became nonfinite")
        if val_loss < best_loss:
            best_loss, best_epoch = val_loss, epoch + 1
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        history.append({"epoch": epoch + 1, "train_loss_mean": float(np.mean(losses)), "validation_loss": val_loss})
        peak_rss = max(peak_rss, psutil.Process().memory_info().rss)
        ns = np.random.get_state()
        checkpoint_save(run_dir / "checkpoint.pt", {
            "identity_sha256": identity_hash, "epoch": epoch + 1, "model": model.state_dict(),
            "optimizer": optimizer.state_dict(), "best_model": best_state, "best_loss": best_loss,
            "best_epoch": best_epoch, "history": history, "torch_rng": torch.get_rng_state(),
            "cuda_rng": torch.cuda.get_rng_state_all() if config.device == "cuda" else [],
            "python_rng": random.getstate(), "numpy_rng": [ns[0], ns[1].tolist(), ns[2], ns[3], ns[4]],
            "elapsed_seconds": accumulated_seconds + time.perf_counter() - start,
            "peak_observed_rss_bytes": peak_rss})
        save_json(run_dir / "status.json", {"state": "running", "epoch": epoch + 1, "epoch_budget": config.epochs})
    if target_epoch < config.epochs:
        save_json(run_dir / "status.json", {"state": "paused", "epoch": target_epoch, "epoch_budget": config.epochs})
        return
    model.load_state_dict(best_state)
    weights = _predict(model, samples.x[samples.test], config.device, config.batch_size)
    portfolios = {"lstm": weights, **baseline_weights(dataset.manifest["assets"], len(weights))}
    results = {name: evaluate(w, samples.y[samples.test], config.cost_bps) for name, w in portfolios.items()}
    report = {"run_id": run_dir.name, "method_label": "synthetic-smoke" if dataset.manifest["kind"] == "synthetic" else "paper-inspired",
              "test_dates": samples.dates[samples.test].tolist(), "cost_bps": config.cost_bps,
              "best_validation_epoch": best_epoch, "strategies": results,
              "baseline_omissions": [] if "stock_bond_60_40" in portfolios else ["60/40 unavailable: missing stock/bond roles"],
              "conventions": CONVENTIONS, "history": history,
              "runtime": {"training_and_evaluation_seconds": accumulated_seconds + time.perf_counter() - start,
                          "peak_observed_rss_bytes": max(peak_rss, psutil.Process().memory_info().rss),
                          "memory_measurement": "RSS sampled at start, epoch boundaries, and completion; not a continuous peak"}}
    checkpoint_save(run_dir / "model.pt", {"model": best_state, "config": asdict(config),
                                           "mean": torch.tensor(samples.mean), "scale": torch.tensor(samples.scale),
                                           "symbols": dataset.symbols})
    with (run_dir / "allocations.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["return_date", "strategy", *dataset.symbols])
        for name, allocations in portfolios.items():
            writer.writerows([d, name, *w.tolist()] for d, w in zip(samples.dates[samples.test], allocations))
    save_json(run_dir / "report.json", report)
    save_json(run_dir / "status.json", {"state": "completed", "epoch": config.epochs, "best_validation_epoch": best_epoch})
