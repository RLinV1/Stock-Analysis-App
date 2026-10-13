--liquibase formatted sql

--changeset portfolio-lab:002-run-list-index
CREATE INDEX experiment_run_operator_created_idx
    ON experiment_run (operator_id, created_at DESC, id DESC);

--rollback DROP INDEX experiment_run_operator_created_idx;
