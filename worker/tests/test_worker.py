import hashlib
import io
import json
import re
import time
import uuid
from pathlib import Path

import pytest

import portfolio_worker
from portfolio_worker import Claimed, JobStore, run_one, upload_artifacts


class FakeS3:
    def __init__(self):
        self.objects = {}
        self.corrupt = False

    def put_object(self, *, Bucket, Key, Body):
        self.objects[(Bucket, Key)] = Body

    def get_object(self, *, Bucket, Key):
        content = self.objects[(Bucket, Key)]
        if self.corrupt:
            content += b"tampered"
        return {"Body": io.BytesIO(content)}


def job():
    return Claimed(uuid.UUID(int=1), uuid.UUID(int=2), uuid.UUID(int=3), {})


def test_attempt_scoped_artifacts_and_index_are_verified(tmp_path):
    (tmp_path / "report.json").write_text('{"state":"completed"}', encoding="utf-8")
    (tmp_path / "request.json").write_text('{"contract_version":1}', encoding="utf-8")
    (tmp_path / ".run.lock").write_text("machine-local", encoding="utf-8")
    s3 = FakeS3()
    key, digest = upload_artifacts(s3, "lab-artifacts", job(), tmp_path)
    assert key == f"runs/{job().run_id}/attempts/{job().attempt_id}/artifact-index.json"
    content = s3.objects[("lab-artifacts", key)]
    assert hashlib.sha256(content).hexdigest() == digest
    index = json.loads(content)
    assert [item["path"] for item in index["files"]] == ["report.json", "request.json"]
    assert all(item["key"].startswith(f"runs/{job().run_id}/attempts/{job().attempt_id}/")
               for item in index["files"])
    assert not any(".run.lock" in object_key for _, object_key in s3.objects)


def test_readback_mismatch_prevents_index_publication(tmp_path):
    (tmp_path / "report.json").write_text("{}", encoding="utf-8")
    s3 = FakeS3()
    s3.corrupt = True
    with pytest.raises(ValueError, match="readback hash mismatch"):
        upload_artifacts(s3, "lab-artifacts", job(), tmp_path)
    assert not any(key.endswith("artifact-index.json") for _, key in s3.objects)


def test_missing_report_is_not_publishable(tmp_path):
    (tmp_path / "request.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="missing its report"):
        upload_artifacts(FakeS3(), "lab-artifacts", job(), tmp_path)


class FakeCursor:
    def __init__(self, row):
        self.row = row
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.statements.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def transaction(self):
        return self

    def cursor(self):
        return self._cursor


def test_invalid_stored_request_fails_terminally_instead_of_blocking_queue(monkeypatch):
    run_id = uuid.UUID(int=9)
    cursor = FakeCursor((run_id, {"contract_version": 2}, 0))
    store = JobStore("dbname=unused", "worker-test")
    monkeypatch.setattr(store, "_connect", lambda: FakeConnection(cursor))
    assert store.claim() is None
    sql, params = cursor.statements[-1]
    assert "state='FAILED'" in sql and "error_code='invalid_request'" in sql
    assert params == (run_id,)
    assert not any("INSERT INTO run_attempt" in statement for statement, _ in cursor.statements)


class RecordingStore:
    """Fake JobStore recording which ownership transition run_one chose."""

    def __init__(self, *, heartbeat=True, publish=True):
        self.heartbeat_result = heartbeat
        self.publish_result = publish
        self.calls = []

    def heartbeat(self, job):
        self.calls.append("heartbeat")
        return self.heartbeat_result

    def publish(self, job, key, digest):
        self.calls.append("publish")
        return self.publish_result

    def cancel_owned(self, job):
        self.calls.append("cancel_owned")
        return True

    def fail_owned(self, job):
        self.calls.append("fail_owned")


def fake_execute(request, root):
    run_dir = root / "run"
    run_dir.mkdir()
    (run_dir / "report.json").write_text("{}", encoding="utf-8")
    return run_dir


def test_run_one_publishes_completed_attempt(monkeypatch):
    monkeypatch.setattr(portfolio_worker, "execute_synthetic_request", fake_execute)
    store, s3 = RecordingStore(), FakeS3()
    run_one(store, s3, "lab-artifacts", job())
    assert store.calls == ["publish"]
    assert any(key.endswith("artifact-index.json") for _, key in s3.objects)


def test_run_one_does_not_upload_after_losing_lease(monkeypatch):
    def slow_execute(request, root):
        # Let the heartbeat thread observe a lost lease before execution returns.
        deadline = time.monotonic() + 5
        while "heartbeat" not in store.calls and time.monotonic() < deadline:
            time.sleep(0.01)
        return fake_execute(request, root)

    monkeypatch.setattr(portfolio_worker, "HEARTBEAT_SECONDS", 0.01)
    monkeypatch.setattr(portfolio_worker, "execute_synthetic_request", slow_execute)
    store, s3 = RecordingStore(heartbeat=False), FakeS3()
    run_one(store, s3, "lab-artifacts", job())
    assert store.calls == ["heartbeat", "cancel_owned"]
    assert s3.objects == {}


def test_run_one_cancels_when_conditional_publish_loses(monkeypatch):
    monkeypatch.setattr(portfolio_worker, "execute_synthetic_request", fake_execute)
    store = RecordingStore(publish=False)
    run_one(store, FakeS3(), "lab-artifacts", job())
    assert store.calls == ["publish", "cancel_owned"]


def test_run_one_records_failure_and_reraises(monkeypatch):
    def broken(request, root):
        raise RuntimeError("training failed")

    monkeypatch.setattr(portfolio_worker, "execute_synthetic_request", broken)
    store = RecordingStore()
    with pytest.raises(RuntimeError, match="training failed"):
        run_one(store, FakeS3(), "lab-artifacts", job())
    assert store.calls == ["fail_owned"]


ARTIFACT_INDEX_SCHEMA = (Path(__file__).resolve().parents[2]
                         / "contracts" / "artifact-index.v1.schema.json")


def publish_nested_run(tmp_path):
    (tmp_path / "report.json").write_text('{"state":"completed"}', encoding="utf-8")
    (tmp_path / "dataset").mkdir()
    (tmp_path / "dataset" / "prices.csv").write_text("day,price\n0,1.0\n", encoding="utf-8")
    s3 = FakeS3()
    key, _ = upload_artifacts(s3, "lab-artifacts", job(), tmp_path)
    return s3.objects[("lab-artifacts", key)]


def test_artifact_index_matches_published_contract(tmp_path):
    # Explicit checks for the constraints the v1 schema declares; not a general
    # JSON Schema engine, so new schema keywords need matching assertions here.
    schema = json.loads(ARTIFACT_INDEX_SCHEMA.read_text(encoding="utf-8"))
    index = json.loads(publish_nested_run(tmp_path))

    assert schema["additionalProperties"] is False
    assert set(index) == set(schema["required"]) == set(schema["properties"])
    assert index["kind"] == schema["properties"]["kind"]["const"]
    assert str(uuid.UUID(index["run_id"])) == index["run_id"] == str(job().run_id)
    assert str(uuid.UUID(index["attempt_id"])) == index["attempt_id"] == str(job().attempt_id)

    files_schema = schema["properties"]["files"]
    item_schema = files_schema["items"]
    required_path = files_schema["contains"]["properties"]["path"]["const"]
    assert isinstance(index["files"], list)
    assert len(index["files"]) >= files_schema["minItems"]
    assert any(item["path"] == required_path for item in index["files"])
    assert item_schema["additionalProperties"] is False
    assert set(item_schema["required"]) == set(item_schema["properties"])

    prefix = f"runs/{job().run_id}/attempts/{job().attempt_id}/"
    pattern = item_schema["properties"]["sha256"]["pattern"]
    for item in index["files"]:
        assert set(item) == set(item_schema["required"])
        assert isinstance(item["path"], str) and item["path"]
        assert isinstance(item["key"], str) and item["key"]
        assert re.fullmatch(pattern, item["sha256"])
        assert type(item["bytes"]) is int and item["bytes"] >= 0
        assert "\\" not in item["path"]
        assert item["key"] == prefix + item["path"]
        content = (tmp_path / item["path"]).read_bytes()
        assert item["sha256"] == hashlib.sha256(content).hexdigest()
        assert item["bytes"] == len(content)
    assert [item["path"] for item in index["files"]] == ["dataset/prices.csv", "report.json"]


def test_artifact_index_bytes_are_canonical(tmp_path):
    content = publish_nested_run(tmp_path)
    canonical = json.dumps(json.loads(content), sort_keys=True,
                           separators=(",", ":")).encode()
    assert content == canonical
