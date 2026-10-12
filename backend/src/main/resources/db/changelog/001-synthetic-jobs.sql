--liquibase formatted sql

--changeset portfolio-lab:001-synthetic-jobs
CREATE TABLE experiment_run (
    id UUID PRIMARY KEY,
    operator_id VARCHAR(64) NOT NULL,
    kind VARCHAR(32) NOT NULL DEFAULT 'SYNTHETIC',
    state VARCHAR(24) NOT NULL DEFAULT 'QUEUED',
    request_json JSONB NOT NULL,
    request_sha256 CHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    current_token UUID,
    lease_expires_at TIMESTAMPTZ,
    cancel_requested_at TIMESTAMPTZ,
    manifest_key TEXT,
    manifest_sha256 CHAR(64),
    error_code VARCHAR(80),
    CONSTRAINT experiment_run_kind_ck CHECK (kind = 'SYNTHETIC'),
    CONSTRAINT experiment_run_state_ck CHECK (state IN
        ('QUEUED', 'RUNNING', 'CANCEL_REQUESTED', 'CANCELLED', 'COMPLETE', 'FAILED')),
    CONSTRAINT experiment_run_attempt_ck CHECK (attempt_count BETWEEN 0 AND 3),
    CONSTRAINT experiment_run_manifest_ck CHECK
        ((state = 'COMPLETE' AND manifest_key IS NOT NULL AND manifest_sha256 IS NOT NULL)
         OR (state <> 'COMPLETE' AND manifest_key IS NULL AND manifest_sha256 IS NULL))
);

CREATE TABLE submission (
    operator_id VARCHAR(64) NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    request_sha256 CHAR(64) NOT NULL,
    run_id UUID NOT NULL REFERENCES experiment_run(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (operator_id, idempotency_key),
    CONSTRAINT submission_run_unique UNIQUE (run_id)
);

CREATE TABLE run_attempt (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES experiment_run(id),
    attempt_no INTEGER NOT NULL,
    fencing_token UUID NOT NULL UNIQUE,
    worker_id VARCHAR(128) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lease_expires_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    checkpoint_key TEXT,
    checkpoint_sha256 CHAR(64),
    failure_code VARCHAR(80),
    CONSTRAINT run_attempt_number_ck CHECK (attempt_no BETWEEN 1 AND 3),
    CONSTRAINT run_attempt_run_number_unique UNIQUE (run_id, attempt_no)
);

CREATE INDEX experiment_run_claim_idx ON experiment_run (created_at, id)
    WHERE state = 'QUEUED';
CREATE INDEX experiment_run_expired_idx ON experiment_run (lease_expires_at, id)
    WHERE state IN ('RUNNING', 'CANCEL_REQUESTED');

--rollback DROP TABLE run_attempt;
--rollback DROP TABLE submission;
--rollback DROP TABLE experiment_run;
