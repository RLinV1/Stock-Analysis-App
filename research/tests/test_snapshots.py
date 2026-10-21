"""Snapshot ownership and preflight identity regression source; unrun."""

import hashlib
import json
from types import SimpleNamespace

import pytest

from portfolio_lab import snapshots


def prepared(tmp_path, csv="prices.csv"):
    source = tmp_path / "source"
    source.mkdir()
    manifest = {"csv": csv, "sha256": hashlib.sha256(b"sample prices\n").hexdigest(), "marker": True}
    raw = (json.dumps(manifest, indent=4) + "\n").encode()
    manifest_path = source / "manifest.json"
    manifest_path.write_bytes(raw)
    if csv == "prices.csv" or csv == "nested/prices.csv":
        data = source / csv
        data.parent.mkdir(parents=True, exist_ok=True)
        data.write_bytes(b"sample prices\n")
    return SimpleNamespace(manifest=manifest, manifest_path=manifest_path), raw


def fake_validator(manifest_path):
    """Isolate copy invariants; public dataset integration remains a separate gate."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = hashlib.sha256((manifest_path.parent / manifest["csv"]).read_bytes()).hexdigest()
    if actual != manifest["sha256"]:
        raise ValueError("copied CSV checksum mismatch")
    return SimpleNamespace(manifest=manifest, manifest_path=manifest_path)


def test_snapshot_preserves_manifest_bytes_and_only_declared_csv(tmp_path, monkeypatch):
    dataset, raw = prepared(tmp_path)
    (dataset.manifest_path.parent / "unrelated.key").write_text("not dataset input")
    monkeypatch.setattr(snapshots, "load_dataset", fake_validator)
    destination = tmp_path / "snapshot"
    copied = snapshots.snapshot_dataset(dataset, destination)
    assert copied.manifest_path == destination / "manifest.json"
    assert copied.manifest_path.read_bytes() == raw
    assert (destination / "prices.csv").read_bytes() == b"sample prices\n"
    assert not (destination / "unrelated.key").exists()


def test_changed_source_manifest_is_rejected_before_output(tmp_path, monkeypatch):
    dataset, _ = prepared(tmp_path)
    changed = {**dataset.manifest, "marker": False}
    dataset.manifest_path.write_text(json.dumps(changed), encoding="utf-8")
    monkeypatch.setattr(snapshots, "load_dataset", lambda _: pytest.fail("validation must not be reached"))
    destination = tmp_path / "snapshot"
    with pytest.raises(ValueError, match="changed after preflight"):
        snapshots.snapshot_dataset(dataset, destination)
    assert not destination.exists()


def test_boolean_to_number_manifest_change_is_not_equal(tmp_path):
    dataset, _ = prepared(tmp_path)
    dataset.manifest_path.write_text(json.dumps({**dataset.manifest, "marker": 1}), encoding="utf-8")
    destination = tmp_path / "snapshot"
    with pytest.raises(ValueError, match="changed after preflight"):
        snapshots.snapshot_dataset(dataset, destination)
    assert not destination.exists()


def test_existing_destination_is_preserved(tmp_path, monkeypatch):
    dataset, _ = prepared(tmp_path)
    destination = tmp_path / "snapshot"
    destination.mkdir()
    evidence = destination / "manifest.json"
    evidence.write_bytes(b"prior evidence\n")
    monkeypatch.setattr(snapshots, "load_dataset", lambda _: pytest.fail("must not validate existing output"))
    with pytest.raises(FileExistsError):
        snapshots.snapshot_dataset(dataset, destination)
    assert evidence.read_bytes() == b"prior evidence\n"
    assert list(destination.iterdir()) == [evidence]


@pytest.mark.parametrize("csv", [
    "", " ", ".", "../prices.csv", "nested/../prices.csv", "/prices.csv",
    "C:/prices.csv", "C:prices.csv", "\\\\host\\share\\prices.csv", "..\\prices.csv",
    "manifest.json", "MANIFEST.JSON", "manifest.json/prices.csv", "manifest.json\\prices.csv",
    "manifest.json.", "manifest.json ", "manifest.json:prices.csv", "nested./prices.csv",
    "nested /prices.csv", "nested/prices.csv:stream",
    "nested/prices.csv", "nested\\prices.csv", "./prices.csv",
])
def test_invalid_csv_path_is_rejected_before_creation(tmp_path, csv):
    dataset, _ = prepared(tmp_path, csv)
    destination = tmp_path / "snapshot"
    with pytest.raises(ValueError):
        snapshots.snapshot_dataset(dataset, destination)
    assert not destination.exists()


def test_modified_csv_is_rejected_and_partial_snapshot_is_retained(tmp_path, monkeypatch):
    dataset, _ = prepared(tmp_path)
    (dataset.manifest_path.parent / "prices.csv").write_bytes(b"changed prices\n")
    monkeypatch.setattr(snapshots, "load_dataset", fake_validator)
    destination = tmp_path / "snapshot"
    with pytest.raises(ValueError, match="checksum mismatch"):
        snapshots.snapshot_dataset(dataset, destination)
    assert (destination / "manifest.json").exists()
    assert (destination / "prices.csv").read_bytes() == b"changed prices\n"


def test_copy_failure_does_not_claim_a_validated_snapshot(tmp_path, monkeypatch):
    dataset, _ = prepared(tmp_path)
    (dataset.manifest_path.parent / "prices.csv").unlink()
    monkeypatch.setattr(snapshots, "load_dataset", lambda _: pytest.fail("copy did not finish"))
    destination = tmp_path / "snapshot"
    with pytest.raises(FileNotFoundError):
        snapshots.snapshot_dataset(dataset, destination)
    assert (destination / "manifest.json").exists()


def test_snapshot_round_trip_with_public_dataset_loader(tmp_path):
    from portfolio_lab.data import load_dataset, synthetic_dataset

    manifest = synthetic_dataset(tmp_path / "real-data", observations=100)
    original = load_dataset(manifest)
    copied = snapshots.snapshot_dataset(original, tmp_path / "snapshot")
    assert copied.manifest_path == (tmp_path / "snapshot/manifest.json").resolve()
    assert copied.manifest == original.manifest
    assert copied.dates.tolist() == original.dates.tolist()
    assert copied.prices.tolist() == original.prices.tolist()
    assert copied.manifest_path.read_bytes() == manifest.read_bytes()


def test_public_loader_rejects_csv_changed_after_preflight(tmp_path):
    from portfolio_lab.data import load_dataset, synthetic_dataset

    manifest = synthetic_dataset(tmp_path / "real-data", observations=100)
    original = load_dataset(manifest)
    csv = manifest.parent / original.manifest["csv"]
    csv.write_bytes(csv.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="checksum mismatch"):
        snapshots.snapshot_dataset(original, tmp_path / "snapshot")


def test_validated_snapshot_is_independent_of_later_source_changes(tmp_path):
    from portfolio_lab.data import load_dataset, synthetic_dataset

    manifest = synthetic_dataset(tmp_path / "real-data", observations=100)
    original = load_dataset(manifest)
    copied = snapshots.snapshot_dataset(original, tmp_path / "snapshot")
    (manifest.parent / original.manifest["csv"]).write_bytes(b"original source changed\n")
    reloaded = load_dataset(copied.manifest_path)
    assert reloaded.prices.tolist() == original.prices.tolist()


def test_duplicate_snapshot_manifest_field_fails_before_directory_creation(tmp_path):
    dataset, _ = prepared(tmp_path)
    raw = json.dumps(dataset.manifest)
    dataset.manifest_path.write_text(raw[:-1] + ', "marker": true}', encoding="utf-8")
    destination = tmp_path / "snapshot"
    with pytest.raises(ValueError, match="duplicate JSON field"):
        snapshots.snapshot_dataset(dataset, destination)
    assert not destination.exists()
