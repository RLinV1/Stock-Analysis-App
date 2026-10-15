"""Cleanup must never remove unrelated Docker resources or hide daemon failure."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

SPEC = importlib.util.spec_from_file_location(
    "smoke_images", Path(__file__).resolve().parents[1] / "smoke_images.py")
smoke_images = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke_images)


def test_cleanup_checks_owner_before_every_removal():
    smoke = smoke_images.ImageSmoke("api", "worker")
    smoke.containers = ["unrelated-container", "owned-container"]
    removed = []

    def docker(*args, **kwargs):
        if args[1] == "inspect":
            owner = "someone-else" if args[2] == "unrelated-container" else smoke.owner
            return SimpleNamespace(returncode=0, stdout=json.dumps({smoke_images.LABEL: owner}))
        removed.append(args[-1])
        return SimpleNamespace(returncode=0, stdout="")

    smoke.docker = docker
    assert smoke.cleanup() == ["unrelated-container"]
    assert "unrelated-container" not in removed
    assert set(removed) == {"owned-container", smoke.volume, smoke.network}


def test_cleanup_does_not_call_an_unreachable_daemon_success():
    smoke = smoke_images.ImageSmoke("api", "worker")
    smoke.containers = ["owned-container"]
    calls = []

    def docker(*args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=1, stderr="Cannot connect to the Docker daemon")

    smoke.docker = docker
    assert len(smoke.cleanup()) == 3
    assert all(args[1] == "inspect" for args in calls)


def test_cleanup_accepts_resources_already_absent():
    smoke = smoke_images.ImageSmoke("api", "worker")
    smoke.docker = lambda *args, **kwargs: SimpleNamespace(
        returncode=1, stderr="Error response from daemon: No such resource")
    assert smoke.cleanup() == []
