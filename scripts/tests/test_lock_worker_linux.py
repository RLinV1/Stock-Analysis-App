"""Trust-boundary regressions for the container dependency lock generator."""

import copy
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "lock_worker_linux", Path(__file__).resolve().parents[1] / "lock_worker_linux.py")
lock = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lock)
ROOTS = {"torch": ("torch", "2.8.0+cpu"), "psycopg": ("psycopg[binary]", "3.3.6")}


def test_resolution_inputs_remove_legacy_index_and_preserve_exact_direct_extras(monkeypatch):
    monkeypatch.setattr(lock, "direct_requirements", lambda: ROOTS)
    source = lock.resolution_input()
    assert source.splitlines() == ["psycopg[binary]==3.3.6", "torch @ " + lock.TORCH_URL]
    assert "--extra-index-url" not in source


def report():
    def item(name, version, url, direct=False):
        return {"metadata": {"name": name, "version": version}, "is_direct": direct,
                "download_info": {"url": url, "archive_info": {"hashes": {"sha256": "a" * 64}}}}
    return {"version": "1", "environment": {"sys_platform": "linux", "platform_machine": "x86_64",
            "python_version": "3.12", "implementation_name": "cpython"}, "install": [
                item("torch", "2.8.0+cpu", lock.TORCH_URL, True),
                item("psycopg", "3.3.6", "https://files.pythonhosted.org/psycopg.whl"),
                item("psycopg-binary", "3.3.6", "https://files.pythonhosted.org/psycopg_binary.whl")]}


def test_preserves_direct_extras_and_locks_transitive_wheels_deterministically():
    source = report()
    text = lock.generate(source, ROOTS)
    source["install"].reverse()
    assert lock.generate(source, ROOTS) == text
    assert "psycopg[binary]==3.3.6 --hash=sha256:" in text
    assert "psycopg-binary==3.3.6 --hash=sha256:" in text
    assert text.count("--hash=sha256:") == 3
    assert "--extra-index-url" not in text


@pytest.mark.parametrize("field,value", [("sys_platform", "win32"), ("platform_machine", "aarch64"),
                                        ("python_version", "3.13"), ("implementation_name", "pypy")])
def test_rejects_other_execution_targets(field, value):
    source = report()
    source["environment"][field] = value
    with pytest.raises(ValueError):
        lock.generate(source, ROOTS)


@pytest.mark.parametrize("url", ["https://attacker.invalid/p.whl", "http://files.pythonhosted.org/p.whl",
                                 "https://files.pythonhosted.org/p.tar.gz",
                                 "https://user:password@files.pythonhosted.org/p.whl",
                                 "https://files.pythonhosted.org/p.whl?mutable=1"])
def test_rejects_untrusted_or_mutable_artifacts(url):
    source = report()
    source["install"][1]["download_info"]["url"] = url
    with pytest.raises(ValueError):
        lock.generate(source, ROOTS)


def test_rejects_missing_hash_omitted_root_duplicate_and_pin_drift():
    base = report()
    variants = []
    missing_hash = copy.deepcopy(base)
    missing_hash["install"][1]["download_info"]["archive_info"]["hashes"].clear()
    variants.append(missing_hash)
    omitted = copy.deepcopy(base)
    omitted["install"].pop(1)
    variants.append(omitted)
    duplicate = copy.deepcopy(base)
    duplicate["install"].append(duplicate["install"][1])
    variants.append(duplicate)
    drift = copy.deepcopy(base)
    drift["install"][1]["metadata"]["version"] = "3.3.7"
    variants.append(drift)
    wrong_torch = copy.deepcopy(base)
    wrong_torch["install"][0]["download_info"]["url"] = lock.TORCH_URL.replace("download.pytorch.org", "files.pythonhosted.org")
    variants.append(wrong_torch)
    for source in variants:
        with pytest.raises(ValueError):
            lock.generate(source, ROOTS)
