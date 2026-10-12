import json
import os
import shutil
import subprocess

import pytest

from portfolio_lab import provenance, runner
from portfolio_lab.data import load_dataset, synthetic_dataset


def git(root, *arguments):
    executable = shutil.which("git")
    if executable is None:
        pytest.skip("Git unavailable for isolated repository fixture")
    return subprocess.run(
        [executable, "-c", "user.name=Portfolio Lab Test", "-c",
         "user.email=portfolio-test@example.invalid", "-c", "core.autocrlf=false",
         "-c", "commit.gpgsign=false", "-C", str(root), *arguments],
        check=True, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull},
    ).stdout.strip()


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repo"
    package = root / "research" / "src" / "portfolio_lab"
    package.mkdir(parents=True)
    (package / "model.py").write_text("VALUE = 1\n")
    (root / "research" / "pyproject.toml").write_text("[project]\nname = 'fixture'\n")
    (root / "research" / "requirements-cpu.txt").write_text("numpy==2.2.6\n")
    (root / "README.md").write_text("Fixture\n")
    git(root, "init")
    git(root, "add", ".")
    git(root, "commit", "-m", "Create isolated provenance fixture")
    return root


def test_clean_source_and_documentation_changes(repository):
    before = provenance.source_revision(repository)
    assert before["state"] == "available"
    assert before["commit"] == git(repository, "rev-parse", "HEAD")
    assert before["source_dirty"] is False
    (repository / "README.md").write_text("Documentation edit\n")
    (repository / "notes.md").write_text("Untracked notes\n")
    assert provenance.source_revision(repository) == before
    git(repository, "add", "README.md", "notes.md")
    assert provenance.source_revision(repository) == before
    git(repository, "commit", "-m", "Documentation-only fixture commit")
    after = provenance.source_revision(repository)
    assert after["commit"] != before["commit"]
    assert after["source_dirty"] is False


@pytest.mark.parametrize("path", ["research/src/portfolio_lab/model.py",
                                  "research/pyproject.toml", "research/requirements-cpu.txt"])
def test_unstaged_and_staged_source_changes(repository, path):
    with (repository / path).open("a") as handle:
        handle.write("# change\n")
    unstaged = provenance.source_revision(repository)
    assert unstaged["source_dirty"] is True
    assert unstaged["source_changes"] == {
        "staged": False, "unstaged": True, "untracked": False, "ignored_source": False}
    git(repository, "add", path)
    staged = provenance.source_revision(repository)
    assert staged["commit"] == unstaged["commit"]
    assert staged["source_changes"] == {
        "staged": True, "unstaged": False, "untracked": False, "ignored_source": False}


def test_untracked_and_ignored_source_are_dirty(repository):
    package = repository / "research" / "src" / "portfolio_lab"
    (package / "extra.py").write_text("EXTRA = True\n")
    revision = provenance.source_revision(repository)
    assert revision["source_dirty"] is True
    assert revision["source_changes"]["untracked"] is True
    (repository / ".gitignore").write_text("extra.py\n")
    ignored = provenance.source_revision(repository)
    assert ignored["source_dirty"] is True
    assert ignored["source_changes"]["ignored_source"] is True


def test_ignored_bytecode_does_not_count_as_source(repository):
    (repository / ".gitignore").write_text("__pycache__/\nignored/\n")
    package = repository / "research" / "src" / "portfolio_lab"
    cache = package / "__pycache__"
    cache.mkdir()
    (cache / "model.cpython-312.pyc").write_bytes(b"fixture bytecode")
    assert provenance.source_revision(repository)["source_dirty"] is False
    ignored = package / "ignored"
    ignored.mkdir()
    (ignored / "extra.py").write_text("EXTRA = True\n")
    revision = provenance.source_revision(repository)
    assert revision["source_dirty"] is True
    assert revision["source_changes"]["ignored_source"] is True


def test_missing_git_is_explicit(monkeypatch, tmp_path):
    monkeypatch.setattr(provenance.shutil, "which", lambda name: None)
    revision = provenance.source_revision(tmp_path)
    assert revision["state"] == "git_unavailable"
    assert revision["commit"] is None
    assert revision["source_dirty"] is None


def test_missing_repository_and_uncommitted_repository(tmp_path, monkeypatch):
    # A workspace-local pytest temp root must not discover the enclosing project.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    if shutil.which("git") is None:
        pytest.skip("Git unavailable")
    absent = provenance.source_revision(tmp_path)
    assert absent["state"] == "no_repository"
    assert absent["commit"] is None
    assert absent["source_dirty"] is None
    git(tmp_path, "init")
    empty = provenance.source_revision(tmp_path)
    assert empty["state"] == "no_commit"
    assert empty["commit"] is None


def test_git_failure_never_implies_clean(monkeypatch, tmp_path):
    monkeypatch.setattr(provenance.shutil, "which", lambda name: "git")

    def fail(*args, **kwargs):
        raise subprocess.TimeoutExpired("git", 5)

    monkeypatch.setattr(provenance.subprocess, "run", fail)
    revision = provenance.source_revision(tmp_path)
    assert revision["state"] == "git_error"
    assert revision["source_dirty"] is None


def test_run_retains_revision_outside_numerical_identity(repository, tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "source_revision", lambda: provenance.source_revision(repository))
    # Isolate this identity test from concurrent developer edits to the real source tree.
    fingerprint = runner.source_fingerprint()
    monkeypatch.setattr(runner, "source_fingerprint", lambda: fingerprint)
    dataset_path = synthetic_dataset(tmp_path / "data", 120)
    dataset = load_dataset(dataset_path)
    config = runner.RunConfig(str(dataset.dates[70]), str(dataset.dates[90]),
                              lookback=10, hidden_size=4, epochs=2)
    partial = runner.run_experiment(dataset_path, config, tmp_path / "runs", stop_after_epochs=1)
    before_bytes = (partial / "manifest.json").read_bytes()
    before = json.loads(before_bytes)
    assert before["source_revision"]["commit"] == git(repository, "rev-parse", "HEAD")
    assert before["source_revision"]["source_dirty"] is False
    (repository / "README.md").write_text("A new documentation revision\n")
    git(repository, "add", "README.md")
    git(repository, "commit", "-m", "Update fixture documentation")
    runner.run_experiment(dataset_path, config, tmp_path / "runs", resume=partial)
    assert (partial / "manifest.json").read_bytes() == before_bytes
    repeated = runner.run_experiment(dataset_path, config, tmp_path / "runs")
    after = json.loads((repeated / "manifest.json").read_text())
    assert after["source_revision"]["commit"] != before["source_revision"]["commit"]
    assert after["identity_sha256"] == before["identity_sha256"]
    assert after["source_sha256"] == before["source_sha256"]
