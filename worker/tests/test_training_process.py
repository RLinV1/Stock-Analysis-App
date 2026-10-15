"""Actual short-lived child tests; no app, service, DB or Docker starts."""

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from training_process import (TrainingDeadline, TrainingStopped, execute_supervised,
                              supervise)


def sleeping_child():
    return subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)


def test_unresponsive_child_is_terminated_on_cancellation(tmp_path):
    process, lost = sleeping_child(), threading.Event()
    lost.set()
    started = time.monotonic()
    with pytest.raises(TrainingStopped):
        supervise(process, tmp_path, lost, deadline=started + 20, cancel_grace=0.1)
    assert process.poll() is not None
    assert time.monotonic() - started < 5
    assert (tmp_path / ".stop-training").exists()


def test_unresponsive_child_is_terminated_at_hard_deadline(tmp_path):
    process = sleeping_child()
    started = time.monotonic()
    with pytest.raises(TrainingDeadline):
        supervise(process, tmp_path, threading.Event(), deadline=started + 0.1)
    assert process.poll() is not None
    assert time.monotonic() - started < 5


def test_failed_child_cannot_return_completed_result(tmp_path):
    process = subprocess.Popen([sys.executable, "-c", "raise SystemExit(7)"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with pytest.raises(RuntimeError, match="Training child failed"):
        supervise(process, tmp_path, threading.Event(), deadline=time.monotonic() + 20)
    assert process.poll() == 7


def test_cooperative_child_retains_stopped_run_directory(tmp_path):
    code = """
import json, sys, time
from pathlib import Path
root = Path(sys.argv[1])
(root / 'run').mkdir()
while not (root / '.stop-training').exists():
    time.sleep(0.01)
(root / '.training-result.json').write_text(json.dumps(
    {'state': 'stopped', 'run_directory': 'run'}))
"""
    process = subprocess.Popen([sys.executable, "-c", code, str(tmp_path)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    lost = threading.Event()
    lost.set()
    with pytest.raises(TrainingStopped) as stopped:
        supervise(process, tmp_path, lost, deadline=time.monotonic() + 20)
    assert stopped.value.run_dir == tmp_path / "run"
    assert process.poll() == 0


def test_real_training_child_returns_report(tmp_path):
    root = Path(__file__).resolve().parents[2]
    request = json.loads((root / "contracts/examples/synthetic-smoke.v1.json").read_text())
    run_dir = execute_supervised(request, tmp_path, threading.Event(),
                                 deadline=time.monotonic() + 60)
    report = json.loads((run_dir / "report.json").read_text())
    assert report["method_label"] == "synthetic-smoke"
    assert set(report["strategies"]) == {"lstm", "equal_weight", "stock_bond_60_40"}
    assert (run_dir / "checkpoint.pt").exists()
