"""Descriptive Git provenance; numerical identity remains content-based."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess


SOURCE_SCOPE = (
    "research/src/portfolio_lab/**/*.py",
    "research/pyproject.toml",
    "research/requirements*.txt",
)
REVISION_NOTE = (
    "Scope covers research Python source and package declarations, not the entire tree. "
    "Dirty or untracked source cannot be recovered from the commit alone; "
    "this metadata does not include a source snapshot or dependency lock."
)


def source_revision(project_root: Path | None = None) -> dict:
    """Inspect Git without changing it; absent/failed Git is explicit, never clean."""
    root = project_root if project_root is not None else Path(__file__).resolve().parents[3]
    result = {"state": "git_unavailable", "commit": None, "source_dirty": None,
              "source_changes": None, "scope": list(SOURCE_SCOPE), "note": REVISION_NOTE}
    executable = shutil.which("git")
    if executable is None:
        return result
    environment = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"}

    def git(*arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [executable, "-c", "core.fsmonitor=false", "-C", str(root), *arguments],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=5, env=environment, check=False,
        )

    try:
        repository = git("rev-parse", "--show-toplevel")
        if repository.returncode:
            result["state"] = ("no_repository" if "not a git repository" in repository.stderr
                               else "git_error")
            return result
        # Derive pathspecs relative to this project's root, even in a larger repository.
        repository_root = Path(repository.stdout.strip()).resolve()
        prefix = Path(root).resolve().relative_to(repository_root).as_posix()
        prefix = "" if prefix == "." else prefix + "/"
        pathspecs = [f":(top,glob){prefix}{path}" for path in SOURCE_SCOPE]
        revision = git("rev-parse", "--verify", "HEAD")
        if revision.returncode == 0:
            result["commit"] = revision.stdout.strip()
        status = git("status", "--porcelain=v1", "-z", "--untracked-files=all",
                     "--ignored=traditional", "--", *pathspecs)
        if status.returncode:
            result["state"] = "git_error"
            return result
        changes = {"staged": False, "unstaged": False, "untracked": False,
                   "ignored_source": False}
        entries = iter(status.stdout.split("\0"))
        for entry in entries:
            if not entry:
                continue
            code = entry[:2]
            if code == "??":
                changes["untracked"] = True
            elif code == "!!":
                # Ignoring consumed source does not make that source recoverable from Git.
                changes["untracked"] = True
                changes["ignored_source"] = True
            else:
                changes["staged"] |= code[0] != " "
                changes["unstaged"] |= code[1] != " "
                if "R" in code or "C" in code:
                    next(entries, None)  # -z emits a second path for a rename/copy.
        result.update(state="available" if result["commit"] else "no_commit",
                      source_dirty=any(changes.values()), source_changes=changes)
    except (OSError, subprocess.SubprocessError, ValueError):
        result["state"] = "git_error"
    return result
