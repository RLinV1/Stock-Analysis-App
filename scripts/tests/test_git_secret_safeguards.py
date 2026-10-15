"""Real temporary Git repositories; fixture values assembled at runtime."""

from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_secrets as cs

SCANNER = Path(cs.__file__).resolve()
HOOK = SCANNER.parents[1] / ".githooks" / "pre-commit"
SECRET = "gh" + "p_" + "a1B2" * 10


def git(repo, *args, check=True):
    result = subprocess.run(
        ["git", "-C", str(repo), *args], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if check and result.returncode:
        pytest.fail("temporary Git operation failed (diagnostics suppressed)")
    return result


@pytest.fixture
def repo(tmp_path, monkeypatch):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Secret scan test")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "core.autocrlf", "false")
    git(tmp_path, "config", "commit.gpgsign", "false")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def commit_file(repo, path="config.txt", content="clean\n"):
    file = repo / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")
    git(repo, "add", "-f", "--", path)
    git(repo, "commit", "-qm", "test fixture")
    return git(repo, "rev-parse", "HEAD").stdout.strip().decode()


def test_history_finds_removed_secret(repo, capsys):
    commit_file(repo, content=SECRET)
    commit_file(repo)
    assert cs.main(["--all"]) == 0
    assert cs.main(["--history"]) == 1
    captured = capsys.readouterr()
    assert "github-token" in captured.out and "git:" in captured.out
    assert SECRET not in captured.out + captured.err
    assert SECRET[:4] not in captured.out + captured.err
    assert "config.txt" not in captured.out


def test_history_finds_other_branch_and_tag(repo):
    base = commit_file(repo)
    git(repo, "checkout", "-qb", "other")
    commit_file(repo, content=SECRET)
    git(repo, "tag", "retained")
    git(repo, "checkout", "--detach", base)
    git(repo, "branch", "-D", "other")
    assert any(f.rule == "github-token" for f in cs.scan_history())


def test_history_finds_reflog_only_content(repo):
    base = commit_file(repo)
    commit_file(repo, content=SECRET)
    git(repo, "reset", "--hard", base)
    assert cs.main(["--history"]) == 1


def test_history_finds_detached_head_without_reflog(repo):
    base = commit_file(repo)
    git(repo, "checkout", "--detach", base)
    commit_file(repo, content=SECRET)
    git(repo, "reflog", "expire", "--expire=now", "--all")
    assert cs.main(["--history"]) == 1


@pytest.mark.parametrize("kind", ["commit", "tag"])
def test_history_scans_messages(repo, kind):
    commit_file(repo)
    if kind == "commit":
        git(repo, "commit", "--allow-empty", "-qm", SECRET)
    else:
        git(repo, "tag", "-a", "message", "-m", SECRET)
    assert any(f.rule == "github-token" for f in cs.scan_history())


@pytest.mark.parametrize("path", [".env", "runs/forced.txt", "node_modules/forced.txt"])
def test_history_scans_force_added_skipped_paths(repo, path):
    commit_file(repo, path=path, content=SECRET)
    findings = list(cs.scan_history())
    assert any(f.rule == "github-token" for f in findings)
    if path == ".env":
        assert any(f.rule == "sensitive-filename" for f in findings)


def test_history_deduplicates_blobs_and_never_prints_secret_filename(repo, capsys):
    commit_file(repo, path=SECRET + ".key", content=SECRET)
    commit_file(repo, path="second.txt", content=SECRET)
    assert cs.main(["--history"]) == 1
    captured = capsys.readouterr()
    assert captured.out.count("github-token") == 1
    assert SECRET[:4] not in captured.out + captured.err


def test_history_disables_replacement_objects(repo):
    original = commit_file(repo, content=SECRET)
    clean = commit_file(repo)
    git(repo, "replace", original, clean)
    assert any(f.rule == "github-token" for f in cs.scan_history())


def test_history_clean_and_unborn(repo):
    assert cs.main(["--history"]) == 0
    commit_file(repo)
    assert cs.main(["--history"]) == 0


def test_history_rejects_shallow_repository(repo, capsys):
    head = commit_file(repo)
    # A real Git shallow boundary, without transport/network configuration.
    (repo / ".git/shallow").write_text(head + "\n", encoding="ascii")
    assert cs.main(["--history"]) == 2
    assert "shallow" in capsys.readouterr().err


def test_history_paths_and_modes_are_exclusive(repo):
    for args in (["--history", "config.txt"], ["--history", "--all"]):
        with pytest.raises(SystemExit) as exc:
            cs.main(args)
        assert exc.value.code == 2


def test_git_error_diagnostics_do_not_leak(monkeypatch, capsys):
    def fail(*args, **kwargs):
        return subprocess.CompletedProcess(args, 1, b"", SECRET.encode())
    monkeypatch.setattr(subprocess, "run", fail)
    assert cs.main(["--history"]) == 2
    captured = capsys.readouterr()
    assert SECRET[:4] not in captured.out + captured.err


def test_history_preserves_binary_size_allowlist_limits(repo):
    commit_file(repo, content="unit-test-secret-1234567890")
    commit_file(repo, path="large.txt", content=SECRET + "a" * cs.MAX_BYTES)
    binary = repo / "binary.bin"
    binary.write_bytes(b"\x00" + SECRET.encode())
    git(repo, "add", "binary.bin")
    git(repo, "commit", "-qm", "binary")
    assert cs.main(["--history"]) == 0


def test_reviewed_history_exclusion_is_exact_and_auditable(repo, monkeypatch, capsys):
    commit_file(repo, content=SECRET)
    blob = git(repo, "rev-parse", "HEAD:config.txt").stdout.strip().decode()
    monkeypatch.setattr(cs, "load_history_allowlist", lambda: {("git:" + blob, 1, "github-token")})
    assert cs.main(["--history"]) == 0
    assert "1 reviewed history fixture" in capsys.readouterr().err
    assert cs.main(["--history", "--no-history-allowlist"]) == 1
    assert "github-token" in capsys.readouterr().out
    commit_file(repo, content=SECRET + "\nchanged blob\n")
    assert cs.main(["--history"]) == 1


@pytest.mark.parametrize("line,rule", [(2, "github-token"), (1, "generic-secret-assignment")])
def test_reviewed_exclusion_does_not_cover_other_line_or_rule(repo, monkeypatch, line, rule):
    commit_file(repo, content=SECRET)
    blob = git(repo, "rev-parse", "HEAD:config.txt").stdout.strip().decode()
    monkeypatch.setattr(cs, "load_history_allowlist", lambda: {("git:" + blob, line, rule)})
    assert cs.main(["--history"]) == 1


def test_history_allowlist_requires_exact_identity_and_rationale(tmp_path):
    path = tmp_path / "allowlist.json"
    assert cs.load_history_allowlist(path) == set()
    entry = {"object": "a" * 40, "line": 1, "rule": "github-token", "rationale": "reviewed fixture"}
    path.write_text(json.dumps({"version": 1, "findings": [entry]}))
    assert cs.load_history_allowlist(path) == {("git:" + "a" * 40, 1, "github-token")}
    for field, value in [("object", "wildcard*"), ("line", -1), ("rule", "*"), ("rationale", "")]:
        path.write_text(json.dumps({"version": 1, "findings": [{**entry, field: value}]}))
        with pytest.raises(cs.GitError, match="details suppressed"):
            cs.load_history_allowlist(path)


def test_unfiltered_flag_requires_history():
    with pytest.raises(SystemExit) as exc:
        cs.main(["--no-history-allowlist"])
    assert exc.value.code == 2


@pytest.fixture
def hooked_repo(repo):
    (repo / "scripts").mkdir()
    shutil.copyfile(SCANNER, repo / "scripts/check_secrets.py")
    (repo / ".githooks").mkdir()
    target = repo / ".githooks/pre-commit"
    shutil.copyfile(HOOK, target)
    target.chmod(0o755)
    interpreter = repo / ".venv/bin/python"
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text("#!/bin/sh\nexec '" + sys.executable.replace("\\", "/") + "' \"$@\"\n", encoding="utf-8")
    interpreter.chmod(0o755)
    git(repo, "config", "core.hooksPath", ".githooks")
    return repo


def test_real_hook_blocks_staged_secret_despite_clean_worktree(hooked_repo):
    repo = hooked_repo
    (repo / "config.txt").write_text(SECRET, encoding="utf-8")
    git(repo, "add", "config.txt")
    (repo / "config.txt").write_text("clean", encoding="utf-8")
    result = git(repo, "commit", "-qm", "must reject", check=False)
    assert result.returncode != 0
    assert b"github-token" in result.stdout + result.stderr
    assert SECRET.encode() not in result.stdout + result.stderr


def test_real_hook_allows_clean_stage_despite_unstaged_secret(hooked_repo):
    repo = hooked_repo
    (repo / "config.txt").write_text("clean", encoding="utf-8")
    git(repo, "add", "config.txt")
    (repo / "config.txt").write_text(SECRET, encoding="utf-8")
    assert git(repo, "commit", "-qm", "clean stage", check=False).returncode == 0


def test_real_hook_preserves_scanner_failure(hooked_repo):
    repo = hooked_repo
    (repo / "scripts/check_secrets.py").write_text("raise SystemExit(2)\n", encoding="utf-8")
    (repo / "config.txt").write_text("clean", encoding="utf-8")
    git(repo, "add", "config.txt")
    assert git(repo, "commit", "-qm", "must reject", check=False).returncode != 0


def test_hook_missing_python_fails_closed(repo):
    shell = shutil.which("sh")
    if shell is None:
        exec_path = Path(git(repo, "--exec-path").stdout.decode().strip())
        shell = str(exec_path.parents[2] / "bin/sh.exe")
    assert Path(shell).is_file()
    bin_dir = repo / "bin"
    bin_dir.mkdir()
    # Shell builtin fixture supplies the root without spawning a DLL-dependent
    # Git child after PATH is emptied. Other tests invoke actual Git hooks.
    result = subprocess.run(
        [shell, "-c", 'TEST_HOOK_ROOT="$3"; git() { printf "%s\\n" "$TEST_HOOK_ROOT"; }; PATH="$1"; export PATH; . "$2"', "hook-check",
         str(bin_dir).replace("\\", "/"), str(HOOK).replace("\\", "/"), repo.as_posix()],
        cwd=repo, capture_output=True,
    )
    assert result.returncode == 2
    assert b"Python interpreter unavailable" in result.stderr
