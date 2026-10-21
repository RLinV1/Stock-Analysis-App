"""Dataset copying for new, owned local research groups; no process launches."""

from __future__ import annotations

import json
import shutil
from pathlib import Path, PureWindowsPath

from .data import load_dataset
from .json_io import parse_json


def snapshot_csv_path(value: object) -> Path:
    """Reject escape and manifest collisions before creating output directories."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Snapshot CSV must be a nonempty relative path")
    relative, windows = Path(value), PureWindowsPath(value)
    if (relative.is_absolute() or relative.drive or windows.is_absolute() or windows.drive
            or not relative.parts or ".." in relative.parts or ".." in windows.parts):
        raise ValueError("Snapshot CSV paths must stay relative to the dataset directory")
    if any(part.endswith((".", " ")) or ":" in part for part in windows.parts):
        raise ValueError("Snapshot CSV paths must not use Windows aliases or alternate streams")
    if relative.name != value or windows.name != value:
        raise ValueError("Snapshot CSV must be a filename alongside the manifest")
    # Reject the manifest itself and a directory rooted at its reserved name.
    if (relative.parts[0].casefold() == "manifest.json"
            or windows.parts[0].casefold() == "manifest.json"):
        raise ValueError("Snapshot CSV must not collide with manifest.json")
    return relative


def _manifest_identity(manifest: dict) -> str:
    # JSON comparison preserves numeric/boolean distinctions that dict == loses.
    return json.dumps(manifest, sort_keys=True, allow_nan=False, separators=(",", ":"))


def snapshot_dataset(dataset, destination: Path):
    """Copy a preflight-validated dataset and return the validated owned copy.

    The destination must not exist. Failure may retain a partial new directory;
    callers own that evidence and must never treat it as a completed run.
    """
    csv_path = snapshot_csv_path(dataset.manifest["csv"])
    expected = _manifest_identity(dataset.manifest)
    source_manifest = Path(dataset.manifest_path)
    manifest_bytes = source_manifest.read_bytes()
    if _manifest_identity(parse_json(manifest_bytes)) != expected:
        raise ValueError("Dataset manifest changed after preflight")
    destination = Path(destination)
    destination.mkdir(exist_ok=False)
    (destination / "manifest.json").write_bytes(manifest_bytes)
    target_csv = destination / csv_path
    target_csv.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_manifest.parent / csv_path, target_csv)
    copied = load_dataset(destination / "manifest.json")
    if _manifest_identity(copied.manifest) != expected:
        raise ValueError("Copied dataset manifest differs from preflight")
    return copied
