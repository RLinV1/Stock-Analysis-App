"""Single CPU worker for bounded synthetic requests; PostgreSQL owns job state."""

from __future__ import annotations

import hashlib
import json
import os
import signal
import socket
import tempfile
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from portfolio_lab.service_contract import RunStopped, execute_synthetic_request, validate_request


LEASE_SECONDS = 60
HEARTBEAT_SECONDS = 10
MAX_ATTEMPTS = 3
# Set by the SIGTERM/SIGINT handler installed in main().
STOP = threading.Event()


@dataclass(frozen=True)
class Claimed:
    run_id: uuid.UUID
    attempt_id: uuid.UUID
    token: uuid.UUID
    request: dict


class JobStore:
    def __init__(self, dsn: str, worker_id: str):
        self.dsn = dsn
        self.worker_id = worker_id[:128]

    def _connect(self):
        import psycopg
        return psycopg.connect(self.dsn, autocommit=True)

    def claim(self) -> Claimed | None:
        with self._connect() as conn, conn.transaction():
            with conn.cursor() as cur:
                # Sweeps end abandoned runs and close their last attempt in the same
                # statement, so no attempt stays open after its run is terminal.
                cur.execute("""
                    WITH swept AS (
                        UPDATE experiment_run SET state='CANCELLED', current_token=NULL,
                            lease_expires_at=NULL, updated_at=CURRENT_TIMESTAMP
                        WHERE state='CANCEL_REQUESTED' AND lease_expires_at < CURRENT_TIMESTAMP
                        RETURNING id)
                    UPDATE run_attempt SET finished_at=CURRENT_TIMESTAMP, failure_code='cancelled'
                    WHERE finished_at IS NULL AND run_id IN (SELECT id FROM swept)
                """)
                cur.execute("""
                    WITH swept AS (
                        UPDATE experiment_run SET state='FAILED', current_token=NULL,
                            lease_expires_at=NULL, error_code='attempts_exhausted',
                            updated_at=CURRENT_TIMESTAMP
                        WHERE state='RUNNING' AND lease_expires_at < CURRENT_TIMESTAMP
                          AND attempt_count >= %s
                        RETURNING id)
                    UPDATE run_attempt SET finished_at=CURRENT_TIMESTAMP, failure_code='lease_expired'
                    WHERE finished_at IS NULL AND run_id IN (SELECT id FROM swept)
                """, (MAX_ATTEMPTS,))
                cur.execute("""
                    SELECT id, request_json, attempt_count FROM experiment_run
                    WHERE state='QUEUED' OR
                          (state='RUNNING' AND lease_expires_at < CURRENT_TIMESTAMP
                           AND attempt_count < %s)
                    ORDER BY created_at, id FOR UPDATE SKIP LOCKED LIMIT 1
                """, (MAX_ATTEMPTS,))
                row = cur.fetchone()
                if row is None:
                    return None
                run_id, raw_request, prior_attempts = row
                try:
                    request = (json.loads(raw_request) if isinstance(raw_request, str)
                               else raw_request)
                    validate_request(request)
                except ValueError:
                    # Raising here would roll back and reselect the same oldest row
                    # forever, blocking the queue. Fail it terminally instead.
                    cur.execute("""
                        UPDATE experiment_run SET state='FAILED', current_token=NULL,
                            lease_expires_at=NULL, error_code='invalid_request',
                            updated_at=CURRENT_TIMESTAMP WHERE id=%s
                    """, (run_id,))
                    return None
                cur.execute("""
                    UPDATE run_attempt SET finished_at=CURRENT_TIMESTAMP,
                        failure_code='lease_expired'
                    WHERE run_id=%s AND finished_at IS NULL
                """, (run_id,))
                attempt_id, token = uuid.uuid4(), uuid.uuid4()
                cur.execute("""
                    UPDATE experiment_run SET state='RUNNING', attempt_count=%s,
                        current_token=%s, lease_expires_at=CURRENT_TIMESTAMP + INTERVAL '60 seconds',
                        error_code=NULL, updated_at=CURRENT_TIMESTAMP WHERE id=%s
                """, (prior_attempts + 1, token, run_id))
                cur.execute("""
                    INSERT INTO run_attempt (id, run_id, attempt_no, fencing_token,
                                             worker_id, lease_expires_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '60 seconds')
                """, (attempt_id, run_id, prior_attempts + 1, token, self.worker_id))
                return Claimed(run_id, attempt_id, token, request)

    def heartbeat(self, job: Claimed) -> bool:
        with self._connect() as conn, conn.transaction():
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE experiment_run SET lease_expires_at=CURRENT_TIMESTAMP + INTERVAL '60 seconds',
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s AND current_token=%s AND state='RUNNING'
                      AND lease_expires_at > CURRENT_TIMESTAMP
                """, (job.run_id, job.token))
                if cur.rowcount != 1:
                    return False
                cur.execute("""
                    UPDATE run_attempt SET heartbeat_at=CURRENT_TIMESTAMP,
                        lease_expires_at=CURRENT_TIMESTAMP + INTERVAL '60 seconds'
                    WHERE id=%s AND fencing_token=%s
                """, (job.attempt_id, job.token))
                if cur.rowcount != 1:
                    raise RuntimeError("Attempt ownership disappeared")
                return True

    def cancel_owned(self, job: Claimed) -> bool:
        with self._connect() as conn, conn.transaction():
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE experiment_run SET state='CANCELLED', current_token=NULL,
                        lease_expires_at=NULL, updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s AND current_token=%s AND state='CANCEL_REQUESTED'
                """, (job.run_id, job.token))
                if cur.rowcount != 1:
                    return False
                cur.execute("""
                    UPDATE run_attempt SET finished_at=CURRENT_TIMESTAMP,
                        failure_code='cancelled' WHERE id=%s AND fencing_token=%s
                """, (job.attempt_id, job.token))
                return True

    def publish(self, job: Claimed, manifest_key: str, manifest_sha256: str) -> bool:
        with self._connect() as conn, conn.transaction():
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE experiment_run SET state='COMPLETE', manifest_key=%s,
                        manifest_sha256=%s, current_token=NULL, lease_expires_at=NULL,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s AND current_token=%s AND state='RUNNING'
                      AND lease_expires_at > CURRENT_TIMESTAMP
                """, (manifest_key, manifest_sha256, job.run_id, job.token))
                if cur.rowcount != 1:
                    return False
                cur.execute("""
                    UPDATE run_attempt SET finished_at=CURRENT_TIMESTAMP
                    WHERE id=%s AND fencing_token=%s
                """, (job.attempt_id, job.token))
                if cur.rowcount != 1:
                    raise RuntimeError("Attempt ownership disappeared")
                return True

    def fail_owned(self, job: Claimed) -> None:
        with self._connect() as conn, conn.transaction():
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE experiment_run SET state=CASE WHEN attempt_count >= %s
                        THEN 'FAILED' ELSE 'QUEUED' END,
                        current_token=NULL, lease_expires_at=NULL,
                        error_code='worker_failure', updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s AND current_token=%s AND state='RUNNING'
                """, (MAX_ATTEMPTS, job.run_id, job.token))
                if cur.rowcount == 1:
                    cur.execute("""
                        UPDATE run_attempt SET finished_at=CURRENT_TIMESTAMP,
                            failure_code='worker_failure'
                        WHERE id=%s AND fencing_token=%s
                    """, (job.attempt_id, job.token))

    def release_owned(self, job: Claimed) -> bool:
        """Return an owned run to the queue on worker shutdown.

        The claimed attempt stays counted. On the last allowed attempt the run
        fails instead, because attempt_count may never exceed MAX_ATTEMPTS.
        """
        with self._connect() as conn, conn.transaction():
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE experiment_run SET state=CASE WHEN attempt_count >= %s
                        THEN 'FAILED' ELSE 'QUEUED' END,
                        current_token=NULL, lease_expires_at=NULL,
                        error_code=CASE WHEN attempt_count >= %s
                        THEN 'attempts_exhausted' ELSE NULL END,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s AND current_token=%s AND state='RUNNING'
                """, (MAX_ATTEMPTS, MAX_ATTEMPTS, job.run_id, job.token))
                failure_code = "worker_shutdown"
                if cur.rowcount != 1:
                    cur.execute("""
                        UPDATE experiment_run SET state='CANCELLED', current_token=NULL,
                            lease_expires_at=NULL, updated_at=CURRENT_TIMESTAMP
                        WHERE id=%s AND current_token=%s AND state='CANCEL_REQUESTED'
                    """, (job.run_id, job.token))
                    if cur.rowcount != 1:
                        return False
                    failure_code = "cancelled"
                cur.execute("""
                    UPDATE run_attempt SET finished_at=CURRENT_TIMESTAMP, failure_code=%s
                    WHERE id=%s AND fencing_token=%s
                """, (failure_code, job.attempt_id, job.token))
                return True


def upload_artifacts(s3: Any, bucket: str, job: Claimed, run_dir: Path) -> tuple[str, str]:
    """Verify uploaded bytes by readback; return attempt-scoped index key/hash."""
    prefix = f"runs/{job.run_id}/attempts/{job.attempt_id}"
    files = []
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file() or path.name == ".run.lock":
            continue
        relative = path.relative_to(run_dir).as_posix()
        key = f"{prefix}/{relative}"
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        s3.put_object(Bucket=bucket, Key=key, Body=content)
        returned = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        if hashlib.sha256(returned).hexdigest() != digest:
            raise ValueError(f"Artifact readback hash mismatch: {relative}")
        files.append({"path": relative, "key": key, "sha256": digest, "bytes": len(content)})
    if not files or not any(item["path"] == "report.json" for item in files):
        raise ValueError("Completed run is missing its report")
    index = {"run_id": str(job.run_id), "attempt_id": str(job.attempt_id),
             "kind": "synthetic-a0", "files": files}
    content = json.dumps(index, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("utf-8")
    key = f"{prefix}/artifact-index.json"
    digest = hashlib.sha256(content).hexdigest()
    s3.put_object(Bucket=bucket, Key=key, Body=content)
    returned = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    if hashlib.sha256(returned).hexdigest() != digest:
        raise ValueError("Artifact index readback hash mismatch")
    return key, digest


def run_one(store: JobStore, s3: Any, bucket: str, job: Claimed,
            stop: threading.Event | None = None) -> None:
    """Run one claimed job. A `stop` set before training releases the job.

    A worker `stop` never interrupts training. Once training has finished,
    uploading and publishing are cheaper than a rerun, so a stop that arrives
    during training still publishes; Compose's stop grace period covers that.

    Losing ownership does interrupt training: when a heartbeat finds the run no
    longer RUNNING under this token (for example CANCEL_REQUESTED), training
    stops at the next epoch boundary and the run is cancelled if still owned.
    """
    finished, lost = threading.Event(), threading.Event()

    def keep_lease() -> None:
        while not finished.wait(HEARTBEAT_SECONDS):
            try:
                if not store.heartbeat(job):
                    lost.set()
                    return
            except Exception:
                lost.set()
                return

    thread = threading.Thread(target=keep_lease, daemon=True)
    thread.start()
    try:
        if stop is not None and stop.is_set():
            store.release_owned(job)
            return
        with tempfile.TemporaryDirectory(prefix="portfolio-worker-") as temporary:
            try:
                run_dir = execute_synthetic_request(job.request, Path(temporary),
                                                    should_stop=lost.is_set)
            except RunStopped:
                # Only `lost` stops training. cancel_owned succeeds only for our
                # CANCEL_REQUESTED run; False means another owner took over.
                store.cancel_owned(job)
                return
            if lost.is_set():
                store.cancel_owned(job)
                return
            key, digest = upload_artifacts(s3, bucket, job, run_dir)
            if not store.publish(job, key, digest):
                store.cancel_owned(job)
    except Exception:
        store.fail_owned(job)
        raise
    finally:
        finished.set()
        thread.join(timeout=HEARTBEAT_SECONDS + 1)


def main() -> None:
    import boto3
    from botocore.config import Config
    from psycopg.conninfo import make_conninfo

    dsn = make_conninfo(host=os.environ["DATABASE_HOST"],
                        dbname=os.environ["DATABASE_NAME"],
                        user=os.environ["DATABASE_USER"],
                        password=os.environ["DATABASE_PASSWORD"])
    bucket = os.environ["ARTIFACT_BUCKET"]
    endpoint = os.environ["S3_ENDPOINT_URL"]
    worker_id = f"{socket.gethostname()}-{uuid.uuid4()}"[:128]
    store = JobStore(dsn, worker_id)
    s3 = boto3.client("s3", endpoint_url=endpoint, region_name="us-east-1",
                      config=Config(s3={"addressing_style": "path"}))
    # Docker stop sends SIGTERM; never claim new work after it, and release an
    # owned job instead of publishing it (see run_one).
    signal.signal(signal.SIGTERM, lambda signum, frame: STOP.set())
    signal.signal(signal.SIGINT, lambda signum, frame: STOP.set())
    while not STOP.is_set():
        try:
            job = store.claim()
            if job is None:
                STOP.wait(2)
                continue
            run_one(store, s3, bucket, job, stop=STOP)
        except Exception as exc:
            # A retry or terminal failure is recorded in PostgreSQL when ownership
            # still exists. Keep one worker alive; never log request contents.
            print(f"Worker cycle failed: {type(exc).__name__}", flush=True)
            STOP.wait(2)
    print("Worker stopped", flush=True)


if __name__ == "__main__":
    main()
