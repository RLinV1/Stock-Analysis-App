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


@pytest.fixture(autouse=True)
def local_training_stand_in(monkeypatch):
    # Lifecycle tests control execution in process. Separate subprocess tests
    # exercise the real supervision boundary, including unresponsive children.
    monkeypatch.setattr(portfolio_worker, "execute_supervised",
                        lambda request, root, lost, **kwargs:
                        portfolio_worker.execute_synthetic_request(
                            request, root, should_stop=lost.is_set))


class FakeS3:
    def __init__(self):
        self.objects = {}
        self.corrupt = False

    def put_object(self, *, Bucket, Key, Body, **kwargs):
        if kwargs.get("IfNoneMatch") == "*":
            assert (Bucket, Key) not in self.objects, "immutable object overwritten"
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
    failed = [(sql, params) for sql, params in cursor.statements
              if "UPDATE experiment_run" in sql and "state='FAILED'" in sql
              and "error_code='invalid_request'" in sql]
    assert failed == [(failed[0][0], (run_id,))]
    # A recovered expired run's previous open attempt is closed in the same claim.
    sql, params = cursor.statements[-1]
    assert "UPDATE run_attempt" in sql and "failure_code='invalid_request'" in sql
    assert "finished_at IS NULL" in sql and params == (run_id,)
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


def fake_execute(request, root, **kwargs):
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
    def slow_execute(request, root, **kwargs):
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
    def broken(request, root, **kwargs):
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


class ReleasingStore(RecordingStore):
    def release_owned(self, job):
        self.calls.append("release_owned")
        return True


def test_run_one_releases_without_training_when_stop_already_requested(monkeypatch):
    def must_not_run(request, root, **kwargs):
        raise AssertionError("training started after stop was requested")

    monkeypatch.setattr(portfolio_worker, "execute_synthetic_request", must_not_run)
    store, s3, stop = ReleasingStore(), FakeS3(), portfolio_worker.threading.Event()
    stop.set()
    run_one(store, s3, "lab-artifacts", job(), stop=stop)
    assert store.calls == ["release_owned"]
    assert s3.objects == {}


def test_run_one_still_publishes_when_stop_arrives_during_training(monkeypatch):
    # Finished training is cheaper to publish than to rerun after a release.
    stop = portfolio_worker.threading.Event()

    def execute_then_stop(request, root, **kwargs):
        run_dir = fake_execute(request, root)
        stop.set()
        return run_dir

    monkeypatch.setattr(portfolio_worker, "execute_synthetic_request", execute_then_stop)
    store, s3 = ReleasingStore(), FakeS3()
    run_one(store, s3, "lab-artifacts", job(), stop=stop)
    assert store.calls == ["publish"]
    assert any(key.endswith("artifact-index.json") for _, key in s3.objects)


def test_run_one_with_unset_stop_publishes_as_before(monkeypatch):
    monkeypatch.setattr(portfolio_worker, "execute_synthetic_request", fake_execute)
    store, s3 = ReleasingStore(), FakeS3()
    run_one(store, s3, "lab-artifacts", job(), stop=portfolio_worker.threading.Event())
    assert store.calls == ["publish"]
    assert any(key.endswith("artifact-index.json") for _, key in s3.objects)


class RowcountCursor(FakeCursor):
    """FakeCursor whose UPDATEs report the queued rowcounts in order."""

    def __init__(self, rowcounts):
        super().__init__(None)
        self.rowcounts = list(rowcounts)
        self.rowcount = -1

    def execute(self, sql, params=None):
        super().execute(sql, params)
        self.rowcount = 1 if sql.lstrip().startswith("SELECT") else self.rowcounts.pop(0)


def test_release_owned_requeues_running_attempt_as_worker_shutdown(monkeypatch):
    cursor = RowcountCursor([1, 1])
    store = JobStore("dbname=unused", "worker-test")
    monkeypatch.setattr(store, "_connect", lambda: FakeConnection(cursor))
    claimed = job()
    assert store.release_owned(claimed) is True
    (run_sql, run_params), (attempt_sql, attempt_params) = cursor.statements[1:]
    assert run_sql.startswith("UPDATE experiment_run")
    assert "WHERE id=%s AND current_token=%s AND state='RUNNING'" in run_sql
    assert "ELSE 'QUEUED' END" in run_sql and "current_token=NULL" in run_sql
    assert run_params == (portfolio_worker.MAX_ATTEMPTS, portfolio_worker.MAX_ATTEMPTS,
                          claimed.run_id, claimed.token)
    assert "attempt_count=" not in run_sql
    assert attempt_sql.startswith("UPDATE run_attempt SET finished_at=CURRENT_TIMESTAMP")
    assert "WHERE id=%s AND fencing_token=%s" in attempt_sql
    assert attempt_params == ("worker_shutdown", claimed.attempt_id, claimed.token)


def test_release_owned_finishes_requested_cancel_as_cancelled(monkeypatch):
    cursor = RowcountCursor([0, 1, 1])
    store = JobStore("dbname=unused", "worker-test")
    monkeypatch.setattr(store, "_connect", lambda: FakeConnection(cursor))
    claimed = job()
    assert store.release_owned(claimed) is True
    cancel_sql, cancel_params = cursor.statements[2]
    assert "state='CANCELLED'" in cancel_sql
    assert "WHERE id=%s AND current_token=%s AND state='CANCEL_REQUESTED'" in cancel_sql
    assert cancel_params == (claimed.run_id, claimed.token)
    assert cursor.statements[3][1] == ("cancelled", claimed.attempt_id, claimed.token)


def test_release_owned_leaves_unowned_run_untouched(monkeypatch):
    cursor = RowcountCursor([0, 0])
    store = JobStore("dbname=unused", "worker-test")
    monkeypatch.setattr(store, "_connect", lambda: FakeConnection(cursor))
    assert store.release_owned(job()) is False
    assert not any("run_attempt" in sql for sql, _ in cursor.statements)


@pytest.mark.parametrize("method,rowcounts", [
    ("cancel_owned", [0]), ("fail_owned", [0]), ("release_owned", [0, 0]),
    ("heartbeat", [0]), ("publish", [0]),
])
def test_owned_end_transitions_require_unexpired_lease(monkeypatch, method, rowcounts):
    cursor = RowcountCursor(rowcounts)
    store = JobStore("dbname=unused", "worker-test")
    monkeypatch.setattr(store, "_connect", lambda: FakeConnection(cursor))
    arguments = (job(), "key", "a" * 64) if method == "publish" else (job(),)
    getattr(store, method)(*arguments)
    assert cursor.statements
    assert "FOR UPDATE" in cursor.statements[0][0]
    for sql, _ in cursor.statements:
        assert "current_token=%s" in sql
        if sql.startswith("UPDATE"):
            assert "lease_expires_at > clock_timestamp()" in sql
    assert not any("UPDATE run_attempt" in sql for sql, _ in cursor.statements)


@pytest.mark.parametrize("method", ["cancel_owned", "fail_owned", "release_owned",
                                    "heartbeat", "publish"])
def test_owned_end_transition_rejects_missing_attempt(monkeypatch, method):
    cursor = RowcountCursor([1, 0])
    store = JobStore("dbname=unused", "worker-test")
    monkeypatch.setattr(store, "_connect", lambda: FakeConnection(cursor))
    with pytest.raises(RuntimeError, match="Attempt ownership disappeared"):
        arguments = (job(), "key", "a" * 64) if method == "publish" else (job(),)
        getattr(store, method)(*arguments)


def stop_when_lost(request, root, *, should_stop):
    # Stand-in for the runner's epoch-boundary check: train until told to stop.
    deadline = time.monotonic() + 5
    while not should_stop() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert should_stop(), "heartbeat never reported the lost lease"
    raise portfolio_worker.RunStopped(root / "run", 1)


class DeclinedCancelStore(RecordingStore):
    def cancel_owned(self, job):
        self.calls.append("cancel_owned")
        return False


def test_run_one_stops_training_and_cancels_when_lease_is_lost(monkeypatch):
    monkeypatch.setattr(portfolio_worker, "HEARTBEAT_SECONDS", 0.01)
    monkeypatch.setattr(portfolio_worker, "execute_synthetic_request", stop_when_lost)
    store, s3 = RecordingStore(heartbeat=False), FakeS3()
    run_one(store, s3, "lab-artifacts", job())
    assert store.calls == ["heartbeat", "cancel_owned"]
    assert "fail_owned" not in store.calls
    assert s3.objects == {}


def test_run_one_stopped_run_owned_elsewhere_is_left_alone(monkeypatch):
    # cancel_owned is False when another worker holds the lease; nothing else runs.
    monkeypatch.setattr(portfolio_worker, "HEARTBEAT_SECONDS", 0.01)
    monkeypatch.setattr(portfolio_worker, "execute_synthetic_request", stop_when_lost)
    store, s3 = DeclinedCancelStore(heartbeat=False), FakeS3()
    run_one(store, s3, "lab-artifacts", job())
    assert store.calls == ["heartbeat", "cancel_owned"]
    assert s3.objects == {}


def test_run_one_stop_check_is_false_while_lease_is_held(monkeypatch):
    seen = []

    def record_stop_check(request, root, *, should_stop):
        seen.append(should_stop())
        return fake_execute(request, root)

    monkeypatch.setattr(portfolio_worker, "execute_synthetic_request", record_stop_check)
    store, s3 = RecordingStore(), FakeS3()
    run_one(store, s3, "lab-artifacts", job())
    assert seen == [False]
    assert store.calls == ["publish"]


def test_run_one_worker_stop_during_training_is_not_a_training_stop(monkeypatch):
    # A SIGTERM-style stop must not make the training stop check return True.
    stop = portfolio_worker.threading.Event()
    seen = []

    def stop_then_check(request, root, *, should_stop):
        stop.set()
        seen.append(should_stop())
        return fake_execute(request, root)

    monkeypatch.setattr(portfolio_worker, "execute_synthetic_request", stop_then_check)
    store, s3 = ReleasingStore(), FakeS3()
    run_one(store, s3, "lab-artifacts", job(), stop=stop)
    assert seen == [False]
    assert store.calls == ["publish"]


def test_lease_watchdog_stops_before_last_confirmed_lease(monkeypatch):
    monkeypatch.setattr(portfolio_worker.time, "monotonic", lambda: 100.0)
    signal = portfolio_worker.LeaseSignal(100.0)
    assert not signal.is_set()
    monkeypatch.setattr(portfolio_worker.time, "monotonic", lambda: 151.0)
    assert signal.is_set()


def test_late_heartbeat_reply_does_not_extend_lease_from_reply_time(monkeypatch):
    signal = portfolio_worker.LeaseSignal(100.0)
    signal.confirmed(110.0)
    monkeypatch.setattr(portfolio_worker.time, "monotonic", lambda: 161.0)
    assert signal.is_set()


def test_stopped_checkpoint_is_immutable_verified_and_registered(tmp_path):
    (tmp_path / "run").mkdir()
    (tmp_path / "run/checkpoint.pt").write_bytes(b"completed epoch checkpoint")
    calls = []

    class Store:
        def register_checkpoint(self, claimed, key, digest):
            calls.append((key, digest))
            return True

    s3 = FakeS3()
    assert portfolio_worker.retain_checkpoint(Store(), s3, "bucket", job(), tmp_path)
    [(key, digest)] = calls
    assert f"/attempts/{job().attempt_id}/checkpoints/" in key
    assert digest == hashlib.sha256(b"completed epoch checkpoint").hexdigest()
    assert key.endswith(f"/{digest}.pt")


def test_corrupt_checkpoint_is_not_registered(tmp_path):
    (tmp_path / "run").mkdir()
    (tmp_path / "run/checkpoint.pt").write_bytes(b"checkpoint")
    s3 = FakeS3()
    s3.corrupt = True
    with pytest.raises(ValueError, match="Checkpoint readback hash mismatch"):
        portfolio_worker.retain_checkpoint(object(), s3, "bucket", job(), tmp_path)


def test_register_checkpoint_checks_run_and_attempt_ownership(monkeypatch):
    cursor = RowcountCursor([0])
    store = JobStore("dbname=unused", "worker-test")
    monkeypatch.setattr(store, "_connect", lambda: FakeConnection(cursor))
    assert not store.register_checkpoint(job(), "key", "a" * 64)
    [(lock_sql, lock_params), (sql, params)] = cursor.statements
    assert "current_token=%s" in sql and "lease_expires_at > clock_timestamp()" in sql
    assert "FOR UPDATE" in lock_sql and lock_params == (job().run_id, job().token)
    assert "finished_at IS NULL" in sql
    assert params == ("key", "a" * 64, job().attempt_id, job().token,
                      job().run_id, job().run_id, job().token)


class CheckpointStore(RecordingStore):
    def register_checkpoint(self, claimed, key, digest):
        self.calls.append("register_checkpoint")
        return True


def checkpoint_execute(request, root, **kwargs):
    path = fake_execute(request, root)
    (path / "checkpoint.pt").write_bytes(b"completed checkpoint")
    return path


def test_cancel_during_publication_retains_checkpoint_before_cleanup(monkeypatch):
    monkeypatch.setattr(portfolio_worker, "execute_synthetic_request", checkpoint_execute)

    def stopped_upload(*args, **kwargs):
        raise portfolio_worker.TrainingStopped(None)

    monkeypatch.setattr(portfolio_worker, "upload_artifacts", stopped_upload)
    store, s3 = CheckpointStore(), FakeS3()
    run_one(store, s3, "bucket", job())
    assert store.calls == ["register_checkpoint", "cancel_owned"]
    assert len(s3.objects) == 1
    assert not any(key.endswith("artifact-index.json") for _, key in s3.objects)


def test_hard_deadline_retains_checkpoint_and_fails_without_publishing(monkeypatch):
    def deadline(request, root, lost, **kwargs):
        checkpoint_execute(request, root)
        raise portfolio_worker.TrainingDeadline()

    monkeypatch.setattr(portfolio_worker, "execute_supervised", deadline)
    store, s3 = CheckpointStore(), FakeS3()
    with pytest.raises(portfolio_worker.TrainingDeadline):
        run_one(store, s3, "bucket", job())
    assert store.calls == ["register_checkpoint", "fail_owned"]
    assert not any(key.endswith("artifact-index.json") for _, key in s3.objects)


def test_database_budgets_preserve_dsn_search_path(monkeypatch):
    import psycopg

    calls = []
    monkeypatch.setattr(psycopg, "connect", lambda *args, **kwargs: calls.append(kwargs))
    JobStore("dbname=unused options='-csearch_path=isolated_test'", "test")._connect()
    [arguments] = calls
    assert arguments["connect_timeout"] == 5
    assert "-csearch_path=isolated_test" in arguments["options"]
    assert "-cstatement_timeout=5000" in arguments["options"]
    assert "-clock_timeout=2000" in arguments["options"]
