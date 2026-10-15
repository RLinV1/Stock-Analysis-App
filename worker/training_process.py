"""Bounded child-process supervision; no database or S3 clients enter training."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


HARD_DEADLINE_SECONDS = 2 * 60 * 60
CANCEL_GRACE_SECONDS = 5
POLL_SECONDS = 0.1


class TrainingStopped(Exception):
    def __init__(self, run_dir: Path | None):
        super().__init__("Training stopped")
        self.run_dir = run_dir


class TrainingDeadline(Exception):
    pass


def reap(process: subprocess.Popen) -> None:
    """Terminate and reap even a child that ignores cooperative cancellation."""
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
    process.wait()


def supervise(process: subprocess.Popen, root: Path, lost, *,
              deadline: float, cancel_grace: float = CANCEL_GRACE_SECONDS) -> dict:
    """Monitor independently of training; all exit paths reap the owned child."""
    cancelled_at = None
    try:
        while process.poll() is None:
            now = time.monotonic()
            if now >= deadline:
                raise TrainingDeadline("Attempt compute deadline exceeded")
            if lost.is_set():
                if cancelled_at is None:
                    cancelled_at = now
                    (root / ".stop-training").touch()
                if now - cancelled_at >= cancel_grace:
                    raise TrainingStopped(None)
            time.sleep(POLL_SECONDS)
        if lost.is_set():
            raise TrainingStopped(_stopped_directory(root))
        if time.monotonic() >= deadline:
            raise TrainingDeadline("Attempt compute deadline exceeded")
        if process.returncode != 0:
            raise RuntimeError("Training child failed")
        result = json.loads((root / ".training-result.json").read_text(encoding="utf-8"))
        if result.get("state") == "stopped":
            raise TrainingStopped(_stopped_directory(root))
        if result.get("state") != "complete":
            raise RuntimeError("Training child failed")
        return result
    finally:
        reap(process)


def _stopped_directory(root: Path) -> Path | None:
    # The child only reports directories it created under the attempt temp root.
    try:
        result = json.loads((root / ".training-result.json").read_text(encoding="utf-8"))
        path = (root / result["run_directory"]).resolve()
        return path if path.is_relative_to(root.resolve()) and path != root.resolve() else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def execute_supervised(request: dict, root: Path, lost, *, deadline: float) -> Path:
    (root / ".training-request.json").write_text(json.dumps(request), encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), str(root)],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result = supervise(process, root, lost, deadline=deadline)
    path = (root / result["run_directory"]).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve() or not path.is_dir():
        raise RuntimeError("Training child returned invalid directory")
    return path


def child(root: Path) -> None:
    # Import happens in the child so even framework initialization has a deadline.
    from portfolio_lab.service_contract import RunStopped, execute_synthetic_request

    request = json.loads((root / ".training-request.json").read_text(encoding="utf-8"))
    try:
        path = execute_synthetic_request(request, root,
                                        should_stop=lambda: (root / ".stop-training").exists())
        result = {"state": "complete", "run_directory": path.relative_to(root).as_posix()}
    except RunStopped as exc:
        result = {"state": "stopped", "run_directory": exc.run_dir.relative_to(root).as_posix()}
    (root / ".training-result.json").write_text(json.dumps(result), encoding="utf-8")


if __name__ == "__main__":
    child(Path(sys.argv[1]).resolve())
