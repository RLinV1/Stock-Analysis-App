"""JobStore SQL against a real PostgreSQL.

Skipped unless PORTFOLIO_TEST_DATABASE_URL names a disposable database (libpq
conninfo or URL). Each module run creates its own schema, applies the Liquibase
changelog SQL there, and drops the schema afterwards.
"""

import dataclasses
import json
import os
import threading
import uuid
from pathlib import Path

import pytest

DATABASE_URL = os.environ.get("PORTFOLIO_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="PORTFOLIO_TEST_DATABASE_URL is not set")

psycopg = pytest.importorskip("psycopg")
from psycopg.conninfo import make_conninfo  # noqa: E402
from psycopg.types.json import Jsonb  # noqa: E402

from portfolio_worker import MAX_ATTEMPTS, Claimed, JobStore  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = ROOT / "backend" / "src" / "main" / "resources" / "db" / "changelog"
CHANGESETS = ["001-synthetic-jobs.sql", "002-run-list-index.sql"]
SMOKE_REQUEST = json.loads(
    (ROOT / "contracts" / "examples" / "synthetic-smoke.v1.json").read_text(encoding="utf-8"))
MANIFEST_SHA256 = "a" * 64


def changelog_statements():
    """Changelog SQL without Liquibase directives or rollback comments."""
    statements = []
    for name in CHANGESETS:
        lines = (CHANGELOG / name).read_text(encoding="utf-8").splitlines()
        sql = "\n".join(line for line in lines if not line.lstrip().startswith("--"))
        statements.extend(part.strip() for part in sql.split(";") if part.strip())
    return statements


@pytest.fixture(scope="module")
def schema_dsn():
    schema = f"wtest_{uuid.uuid4().hex}"
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        conn.execute(f"CREATE SCHEMA {schema}")
    dsn = make_conninfo(DATABASE_URL, options=f"-csearch_path={schema}")
    try:
        with psycopg.connect(dsn, autocommit=True) as conn:
            for statement in changelog_statements():
                conn.execute(statement)
        yield dsn
    finally:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            conn.execute(f"DROP SCHEMA {schema} CASCADE")


@pytest.fixture
def db(schema_dsn):
    with psycopg.connect(schema_dsn, autocommit=True) as conn:
        conn.execute("TRUNCATE run_attempt, submission, experiment_run")
        yield conn


@pytest.fixture
def store(schema_dsn, db):
    return JobStore(schema_dsn, "worker-a")


def insert_run(db, *, request=None, created_at=None):
    run_id = uuid.uuid4()
    db.execute("""
        INSERT INTO experiment_run (id, operator_id, request_json, request_sha256, created_at)
        VALUES (%s, 'local', %s, %s, COALESCE(%s::timestamptz, CURRENT_TIMESTAMP))
    """, (run_id, Jsonb(SMOKE_REQUEST if request is None else request),
          uuid.uuid4().hex * 2, created_at))
    return run_id


def run_row(db, run_id):
    cur = db.execute("""
        SELECT state, attempt_count, current_token, lease_expires_at, manifest_key,
               manifest_sha256, error_code
        FROM experiment_run WHERE id=%s
    """, (run_id,))
    names = [column.name for column in cur.description]
    return dict(zip(names, cur.fetchone()))


def attempts(db, run_id):
    cur = db.execute("""
        SELECT id, attempt_no, fencing_token, worker_id, lease_expires_at, finished_at,
               failure_code
        FROM run_attempt WHERE run_id=%s ORDER BY attempt_no
    """, (run_id,))
    names = [column.name for column in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]


def expire_lease(db, run_id):
    db.execute("""
        UPDATE experiment_run SET lease_expires_at=CURRENT_TIMESTAMP - INTERVAL '1 second'
        WHERE id=%s
    """, (run_id,))


def request_cancel(db, run_id):
    db.execute("""
        UPDATE experiment_run SET state='CANCEL_REQUESTED',
            cancel_requested_at=CURRENT_TIMESTAMP WHERE id=%s
    """, (run_id,))


def test_claim_takes_oldest_queued_run_and_opens_attempt(db, store):
    newer = insert_run(db, created_at="2026-01-02T00:00:00Z")
    older = insert_run(db, created_at="2026-01-01T00:00:00Z")
    job = store.claim()
    assert job is not None
    assert job.run_id == older
    assert job.request == SMOKE_REQUEST
    row = run_row(db, older)
    assert row["state"] == "RUNNING"
    assert row["attempt_count"] == 1
    assert row["current_token"] == job.token
    assert row["lease_expires_at"] is not None
    [attempt] = attempts(db, older)
    assert attempt["id"] == job.attempt_id
    assert attempt["attempt_no"] == 1
    assert attempt["fencing_token"] == job.token
    assert attempt["worker_id"] == "worker-a"
    assert attempt["finished_at"] is None
    assert run_row(db, newer)["state"] == "QUEUED"


def test_claim_returns_none_when_queue_is_empty(db, store):
    assert store.claim() is None


def claim_concurrently(schema_dsn):
    stores = [JobStore(schema_dsn, "worker-a"), JobStore(schema_dsn, "worker-b")]
    barrier = threading.Barrier(len(stores))
    results, errors = [None] * len(stores), []

    def claim(index):
        try:
            barrier.wait(timeout=10)
            results[index] = stores[index].claim()
        except Exception as exc:  # surfaced by the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=claim, args=(index,)) for index in range(len(stores))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert errors == []
    return results


def test_concurrent_claims_take_distinct_runs(db, schema_dsn):
    runs = {insert_run(db), insert_run(db)}
    results = claim_concurrently(schema_dsn)
    assert all(result is not None for result in results)
    assert {result.run_id for result in results} == runs


def test_concurrent_claims_of_single_run_have_one_winner(db, schema_dsn):
    run_id = insert_run(db)
    results = claim_concurrently(schema_dsn)
    winners = [result for result in results if result is not None]
    assert len(winners) == 1
    assert winners[0].run_id == run_id
    assert len(attempts(db, run_id)) == 1


def test_heartbeat_extends_lease_only_for_current_token(db, store):
    run_id = insert_run(db)
    job = store.claim()
    db.execute("""
        UPDATE experiment_run SET lease_expires_at=CURRENT_TIMESTAMP + INTERVAL '5 seconds'
        WHERE id=%s
    """, (run_id,))
    shortened = run_row(db, run_id)["lease_expires_at"]

    stale = dataclasses.replace(job, token=uuid.uuid4())
    assert store.heartbeat(stale) is False
    assert run_row(db, run_id)["lease_expires_at"] == shortened

    assert store.heartbeat(job) is True
    extended = run_row(db, run_id)["lease_expires_at"]
    assert extended > shortened
    [attempt] = attempts(db, run_id)
    assert attempt["lease_expires_at"] == extended


def test_heartbeat_fails_after_lease_expired(db, store):
    run_id = insert_run(db)
    job = store.claim()
    expire_lease(db, run_id)
    assert store.heartbeat(job) is False


def test_publish_completes_run_and_finishes_attempt(db, store):
    run_id = insert_run(db)
    job = store.claim()
    key = f"runs/{run_id}/attempts/{job.attempt_id}/artifact-index.json"
    assert store.publish(job, key, MANIFEST_SHA256) is True
    row = run_row(db, run_id)
    assert row["state"] == "COMPLETE"
    assert row["manifest_key"] == key
    assert row["manifest_sha256"] == MANIFEST_SHA256
    assert row["current_token"] is None and row["lease_expires_at"] is None
    [attempt] = attempts(db, run_id)
    assert attempt["finished_at"] is not None
    assert attempt["failure_code"] is None


def test_publish_loses_after_cancel_request_and_cancel_owned_cancels(db, store):
    run_id = insert_run(db)
    job = store.claim()
    request_cancel(db, run_id)
    assert store.publish(job, "runs/key", MANIFEST_SHA256) is False
    row = run_row(db, run_id)
    assert row["state"] == "CANCEL_REQUESTED"
    assert row["manifest_key"] is None

    assert store.cancel_owned(job) is True
    row = run_row(db, run_id)
    assert row["state"] == "CANCELLED"
    assert row["current_token"] is None and row["lease_expires_at"] is None
    [attempt] = attempts(db, run_id)
    assert attempt["finished_at"] is not None
    assert attempt["failure_code"] == "cancelled"


def test_publish_loses_with_changed_token(db, store):
    run_id = insert_run(db)
    job = store.claim()
    stale = dataclasses.replace(job, token=uuid.uuid4())
    assert store.publish(stale, "runs/key", MANIFEST_SHA256) is False
    row = run_row(db, run_id)
    assert row["state"] == "RUNNING"
    assert row["current_token"] == job.token
    assert row["manifest_key"] is None


def test_cancel_owned_ignores_running_run(db, store):
    run_id = insert_run(db)
    job = store.claim()
    assert store.cancel_owned(job) is False
    assert run_row(db, run_id)["state"] == "RUNNING"


def test_expired_lease_is_reclaimed_as_next_attempt(db, store):
    run_id = insert_run(db)
    first = store.claim()
    expire_lease(db, run_id)
    second = JobStore(store.dsn, "worker-b").claim()
    assert second is not None
    assert second.run_id == run_id
    assert second.token != first.token
    row = run_row(db, run_id)
    assert row["state"] == "RUNNING"
    assert row["attempt_count"] == 2
    assert row["current_token"] == second.token
    old, new = attempts(db, run_id)
    assert old["id"] == first.attempt_id
    assert old["finished_at"] is not None
    assert old["failure_code"] == "lease_expired"
    assert new["id"] == second.attempt_id
    assert new["attempt_no"] == 2 and new["worker_id"] == "worker-b"
    assert new["finished_at"] is None
    # The fenced-out first owner can no longer publish or extend its lease.
    assert store.publish(first, "runs/key", MANIFEST_SHA256) is False
    assert store.heartbeat(first) is False


def test_expired_lease_on_last_attempt_fails_run(db, store):
    run_id = insert_run(db)
    for attempt_no in range(1, MAX_ATTEMPTS + 1):
        job = store.claim()
        assert job is not None and job.run_id == run_id
        assert run_row(db, run_id)["attempt_count"] == attempt_no
        expire_lease(db, run_id)
    assert store.claim() is None
    row = run_row(db, run_id)
    assert row["state"] == "FAILED"
    assert row["error_code"] == "attempts_exhausted"
    assert row["attempt_count"] == MAX_ATTEMPTS
    assert row["current_token"] is None and row["lease_expires_at"] is None
    history = attempts(db, run_id)
    assert len(history) == MAX_ATTEMPTS
    # The sweep closes the last attempt too; no attempt stays open on a terminal run.
    assert all(item["finished_at"] is not None for item in history)
    assert all(item["failure_code"] == "lease_expired" for item in history)


def test_expired_cancel_request_is_cancelled_and_attempt_closed(db, store):
    run_id = insert_run(db)
    job = store.claim()
    assert job is not None and job.run_id == run_id
    request_cancel(db, run_id)
    expire_lease(db, run_id)
    assert store.claim() is None
    row = run_row(db, run_id)
    assert row["state"] == "CANCELLED"
    assert row["current_token"] is None and row["lease_expires_at"] is None
    [attempt] = attempts(db, run_id)
    assert attempt["finished_at"] is not None
    assert attempt["failure_code"] == "cancelled"


def test_fail_owned_requeues_until_last_attempt_then_fails(db, store):
    run_id = insert_run(db)
    for attempt_no in range(1, MAX_ATTEMPTS):
        job = store.claim()
        store.fail_owned(job)
        row = run_row(db, run_id)
        assert row["state"] == "QUEUED"
        assert row["attempt_count"] == attempt_no
        assert row["error_code"] == "worker_failure"
        assert row["current_token"] is None and row["lease_expires_at"] is None
    job = store.claim()
    store.fail_owned(job)
    row = run_row(db, run_id)
    assert row["state"] == "FAILED"
    assert row["attempt_count"] == MAX_ATTEMPTS
    assert row["error_code"] == "worker_failure"
    recorded = attempts(db, run_id)
    assert [attempt["attempt_no"] for attempt in recorded] == [1, 2, 3]
    assert all(attempt["finished_at"] is not None for attempt in recorded)
    assert all(attempt["failure_code"] == "worker_failure" for attempt in recorded)
    assert store.claim() is None


def test_release_owned_requeues_until_last_attempt_then_fails(db, store):
    run_id = insert_run(db)
    for attempt_no in range(1, MAX_ATTEMPTS):
        job = store.claim()
        assert store.release_owned(job) is True
        row = run_row(db, run_id)
        assert row["state"] == "QUEUED"
        assert row["attempt_count"] == attempt_no
        assert row["error_code"] is None
        assert row["current_token"] is None and row["lease_expires_at"] is None
        latest = attempts(db, run_id)[-1]
        assert latest["id"] == job.attempt_id
        assert latest["finished_at"] is not None
        assert latest["failure_code"] == "worker_shutdown"
    job = store.claim()
    assert store.release_owned(job) is True
    row = run_row(db, run_id)
    assert row["state"] == "FAILED"
    assert row["attempt_count"] == MAX_ATTEMPTS
    assert row["error_code"] == "attempts_exhausted"
    assert attempts(db, run_id)[-1]["failure_code"] == "worker_shutdown"
    assert store.claim() is None


def test_release_owned_cancels_requested_cancel(db, store):
    run_id = insert_run(db)
    job = store.claim()
    request_cancel(db, run_id)
    assert store.release_owned(job) is True
    row = run_row(db, run_id)
    assert row["state"] == "CANCELLED"
    assert row["current_token"] is None and row["lease_expires_at"] is None
    [attempt] = attempts(db, run_id)
    assert attempt["finished_at"] is not None
    assert attempt["failure_code"] == "cancelled"


def test_release_owned_leaves_unowned_run_untouched(db, store):
    run_id = insert_run(db)
    job = store.claim()
    stale = dataclasses.replace(job, token=uuid.uuid4())
    assert store.release_owned(stale) is False
    assert run_row(db, run_id)["state"] == "RUNNING"
    assert attempts(db, run_id)[0]["finished_at"] is None


def test_invalid_stored_request_fails_without_blocking_queue(db, store):
    invalid = insert_run(db, request={**SMOKE_REQUEST, "contract_version": 2},
                         created_at="2026-01-01T00:00:00Z")
    valid = insert_run(db, created_at="2026-01-02T00:00:00Z")
    assert store.claim() is None
    row = run_row(db, invalid)
    assert row["state"] == "FAILED"
    assert row["error_code"] == "invalid_request"
    assert row["attempt_count"] == 0
    assert attempts(db, invalid) == []

    job = store.claim()
    assert isinstance(job, Claimed)
    assert job.run_id == valid
    assert run_row(db, valid)["state"] == "RUNNING"


def test_invalid_reclaimed_request_closes_prior_attempt(db, store):
    run_id = insert_run(db)
    first = store.claim()
    assert first is not None
    db.execute("""
        UPDATE experiment_run SET request_json=%s WHERE id=%s
    """, (Jsonb({**SMOKE_REQUEST, "contract_version": 2}), run_id))
    expire_lease(db, run_id)

    assert store.claim() is None
    row = run_row(db, run_id)
    assert row["state"] == "FAILED"
    assert row["error_code"] == "invalid_request"
    assert row["attempt_count"] == 1
    assert row["current_token"] is None and row["lease_expires_at"] is None
    [attempt] = attempts(db, run_id)
    assert attempt["id"] == first.attempt_id
    assert attempt["finished_at"] is not None
    assert attempt["failure_code"] == "invalid_request"
