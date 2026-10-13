#!/usr/bin/env python3
"""Dependency-free secret scanner for this repository.

Run before any publication, or as an optional pre-commit hook:

    python scripts/check_secrets.py [--staged | --all] [paths...]

--staged (default) scans the staged blob of every added, copied, modified
or renamed file, so it checks exactly what will be committed. --all scans
every tracked file in the working tree. Explicit paths (files or
directories) scan working-tree content.

Exit status: 0 no findings, 1 findings, 2 usage or git error.

This is a regular-expression scanner. It is a cheap first gate, not a
substitute for gitleaks or trufflehog before the repository goes public.
Matched values are never printed; output shows only a redacted prefix.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple

MAX_BYTES = 2 * 1024 * 1024
BINARY_SNIFF_BYTES = 8 * 1024
ALLOW_MARKER = "secret-scan: allow"

# Directory names skipped wherever they appear in a path.
# Dependency, cache and build trees: never committed sources and very large to walk.
SKIP_ANY_COMPONENT = frozenset({"node_modules", ".venv", ".maven-repo", ".maven-tmp", ".git",
                                ".jest-cache", ".expo", "target", "__pycache__", ".pytest_cache"})
# Directory names skipped only at the repository (or scan) root.
SKIP_TOP_LEVEL = frozenset({"runs", "data"})


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    redacted: str = ""

    def format(self) -> str:
        suffix = f" [{self.redacted}]" if self.redacted else ""
        return f"{self.path}:{self.line}: {self.rule}{suffix}"


# --------------------------------------------------------------------------
# Rules. Each specific rule has a name and a compiled pattern; group 0 is the
# matched secret value used for allowlisting and redaction.
# --------------------------------------------------------------------------

_SPECIFIC_RULES: Tuple[Tuple[str, "re.Pattern[str]"], ...] = (
    ("private-key", re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----")),
    ("aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("github-token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    # LocalStack auth tokens: "ls-" followed by a long alphanumeric body or a
    # UUID-shaped body. A digit and a letter are both required (checked in
    # _localstack_ok) so words such as "ls-files" or "ls-remote" never match.
    (
        "localstack-auth-token",
        re.compile(
            r"(?<![A-Za-z0-9_-])ls-(?:[A-Za-z0-9]{20,}"
            r"|[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12})"
            r"(?![A-Za-z0-9_-])"
        ),
    ),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
)

_KEY_WORDS = r"(?:password|passwd|secret|token|api[_-]?key|auth[_-]?token)"
_GENERIC = re.compile(
    r"(?i)(?P<key>[A-Za-z0-9_.-]*" + _KEY_WORDS + r"[A-Za-z0-9_.-]*)"
    r"[\"']?\s*(?:=>|:=|[:=])\s*"
    r"(?:\"(?P<dq>[^\"]*)\"|'(?P<sq>[^']*)'|(?P<bare>[A-Za-z0-9_\-+/=.~!@$%^&*]+))"
)
_GENERIC_MIN_LEN = 16
_AUTH_SCHEME = re.compile(r"^(?:Bearer|Basic|Token)\s+", re.IGNORECASE)

_ALLOW_SUBSTRINGS = ("validation-only", "unit-test-secret", "example", "changeme")
_PLACEHOLDER = re.compile(r"<[^<>\s][^<>]*>")


def is_allowlisted_value(value: str) -> bool:
    """True when a matched value is a known placeholder or test value."""
    v = value.strip()
    if not v:
        return True
    lowered = v.lower()
    if lowered == "test":
        return True
    if "${" in v:
        return True
    if any(s in lowered for s in _ALLOW_SUBSTRINGS):
        return True
    if _PLACEHOLDER.search(v):
        return True
    return False


def _mixed_classes(value: str) -> bool:
    has_alpha = any(c.isalpha() for c in value)
    has_digit = any(c.isdigit() for c in value)
    return has_alpha and has_digit


def _localstack_ok(value: str) -> bool:
    body = value[3:]
    return any(c.isdigit() for c in body) and any(c.isalpha() for c in body)


def redact(value: str) -> str:
    """Return a redacted form that never contains the full value."""
    if len(value) >= 12:
        return value[:4] + "…"
    return "…"


def check_filename(path: str) -> Optional[Finding]:
    """Flag files whose name alone indicates secret material."""
    name = path.replace("\\", "/").rsplit("/", 1)[-1]
    lowered = name.lower()
    if lowered == ".env" or (lowered.startswith(".env.") and lowered != ".env.example"):
        return Finding(path, 0, "sensitive-filename")
    if lowered.endswith((".pem", ".key", ".p12")):
        return Finding(path, 0, "sensitive-filename")
    if lowered in {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}:
        return Finding(path, 0, "sensitive-filename")
    return None


def is_skipped_path(path: str) -> bool:
    parts = [p for p in path.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts:
        return False
    if parts[0] in SKIP_TOP_LEVEL and len(parts) > 1:
        return True
    return any(p in SKIP_ANY_COMPONENT for p in parts[:-1])


def _scan_line(path: str, lineno: int, line: str) -> List[Finding]:
    if ALLOW_MARKER in line:
        return []
    findings: List[Finding] = []
    spans: List[Tuple[int, int]] = []
    for rule, pattern in _SPECIFIC_RULES:
        for m in pattern.finditer(line):
            value = m.group(0)
            if rule == "localstack-auth-token" and not _localstack_ok(value):
                continue
            if rule != "private-key" and is_allowlisted_value(value):
                continue
            spans.append(m.span())
            findings.append(Finding(path, lineno, rule, redact(value)))
    for m in _GENERIC.finditer(line):
        group = next(g for g in ("dq", "sq", "bare") if m.group(g) is not None)
        value = m.group(group)
        start, end = m.span(group)
        if any(start < e and s < end for s, e in spans):
            continue
        if group == "bare" and end < len(line) and line[end] in "([":
            continue  # a call or index expression, not a literal
        value = _AUTH_SCHEME.sub("", value)
        if any(c.isspace() for c in value):
            continue
        if len(value) < _GENERIC_MIN_LEN or not _mixed_classes(value):
            continue
        if is_allowlisted_value(value):
            continue
        findings.append(Finding(path, lineno, "generic-secret-assignment", redact(value)))
    return findings


def scan_text(path: str, text: str) -> List[Finding]:
    """Scan decoded text content. Does not apply filename or skip rules."""
    findings: List[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        findings.extend(_scan_line(path, lineno, line))
    return findings


def is_binary(data: bytes) -> bool:
    return b"\x00" in data[:BINARY_SNIFF_BYTES]


def scan_bytes(path: str, data: bytes) -> List[Finding]:
    """Scan one file's content plus its name. Skips excluded, large or binary files."""
    if is_skipped_path(path):
        return []
    findings: List[Finding] = []
    name_finding = check_filename(path)
    if name_finding is not None:
        findings.append(name_finding)
    if len(data) > MAX_BYTES or is_binary(data):
        return findings
    findings.extend(scan_text(path, data.decode("utf-8", errors="replace")))
    return findings


# --------------------------------------------------------------------------
# File sources
# --------------------------------------------------------------------------


class GitError(Exception):
    pass


def _git(args: Sequence[str], cwd: Optional[str] = None) -> bytes:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        )
    except OSError as exc:
        raise GitError(f"cannot run git: {exc}") from exc
    if proc.returncode != 0:
        msg = proc.stderr.decode("utf-8", errors="replace").strip()
        raise GitError(f"git {' '.join(args[:2])} failed: {msg}")
    return proc.stdout


def _repo_root() -> str:
    return _git(["rev-parse", "--show-toplevel"]).decode("utf-8").strip()


def _split_z(raw: bytes) -> List[str]:
    return [p.decode("utf-8", errors="surrogateescape") for p in raw.split(b"\x00") if p]


def iter_staged() -> Iterator[Tuple[str, bytes]]:
    root = _repo_root()
    names = _split_z(
        _git(["diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"], cwd=root)
    )
    for name in names:
        if is_skipped_path(name):
            continue
        yield name, _git(["show", f":{name}"], cwd=root)


def _read_file(path: str) -> Optional[bytes]:
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            # Read only enough to know the file is over the limit.
            return fh.read(MAX_BYTES + 1) if size > MAX_BYTES else fh.read()
    except OSError:
        return None


def iter_tracked() -> Iterator[Tuple[str, bytes]]:
    root = _repo_root()
    for name in _split_z(_git(["ls-files", "-z"], cwd=root)):
        if is_skipped_path(name):
            continue
        data = _read_file(os.path.join(root, name))
        if data is not None:  # tracked but deleted in the working tree
            yield name, data


def iter_paths(paths: Iterable[str]) -> Iterator[Tuple[str, bytes]]:
    for given in paths:
        if os.path.isdir(given):
            for dirpath, dirnames, filenames in os.walk(given):
                rel_dir = os.path.relpath(dirpath, given)
                dirnames[:] = [
                    d
                    for d in dirnames
                    if d not in SKIP_ANY_COMPONENT
                    and not (rel_dir == "." and d in SKIP_TOP_LEVEL)
                    and d != ".git"
                ]
                for fn in filenames:
                    full = os.path.join(dirpath, fn)
                    data = _read_file(full)
                    if data is not None:
                        yield full.replace("\\", "/"), data
        elif os.path.isfile(given):
            data = _read_file(given)
            if data is None:
                raise FileNotFoundError(given)
            yield given.replace("\\", "/"), data
        else:
            raise FileNotFoundError(given)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regex secret scanner. Exit 0 clean, 1 findings, 2 usage/git error."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true", help="scan staged content (default)")
    mode.add_argument("--all", action="store_true", help="scan all tracked files")
    parser.add_argument("paths", nargs="*", help="working-tree files or directories to scan")
    args = parser.parse_args(argv)  # exits 2 on usage errors

    if args.paths and (args.staged or args.all):
        parser.error("paths cannot be combined with --staged or --all")

    try:
        sys.stdout.reconfigure(errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass

    if args.paths:
        source = iter_paths(args.paths)
    elif args.all:
        source = iter_tracked()
    else:
        source = iter_staged()

    findings: List[Finding] = []
    try:
        for path, data in source:
            findings.extend(scan_bytes(path, data))
    except GitError as exc:
        print(f"check_secrets: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"check_secrets: cannot read {exc}", file=sys.stderr)
        return 2

    for finding in findings:
        print(finding.format())
    if findings:
        print(
            f"check_secrets: {len(findings)} finding(s). Remove the secret, or mark a "
            f"reviewed false positive with an inline '{ALLOW_MARKER}' comment.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
