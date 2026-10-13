package dev.portfoliolab.api.jobs;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;

import dev.portfoliolab.api.contract.SyntheticRequestContract.Accepted;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

/** PostgreSQL-backed submission and read transitions. Worker ownership follows separately. */
@Repository
public class RunRepository {
    public static final int MAX_PAGE_SIZE = 50;
    private static final RowMapper<Summary> SUMMARY = (rs, rowNum) -> new Summary(
            rs.getObject("id", UUID.class), rs.getString("state"), rs.getInt("attempt_count"),
            rs.getString("manifest_key"), rs.getString("error_code"),
            rs.getTimestamp("created_at").toInstant());
    private final JdbcTemplate jdbc;

    public RunRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public record Submission(UUID runId, boolean created) {}
    public record Snapshot(UUID id, String state, int attemptCount, String manifestKey,
                           String manifestSha256, String errorCode) {}
    public record Summary(UUID id, String state, int attemptCount, String manifestKey,
                          String errorCode, Instant createdAt) {}
    /** One newest-first page; nextCursor is the last item's ID when more rows exist. */
    public record Page(List<Summary> items, UUID nextCursor) {}

    public static final class IdempotencyConflict extends RuntimeException {
        public IdempotencyConflict() {
            super("Idempotency key was already used with a different request");
        }
    }

    @Transactional
    public Submission submit(String operator, String key, Accepted request) {
        validateOperator(operator);
        validateKey(key);
        Objects.requireNonNull(request, "request");
        UUID candidate = UUID.randomUUID();
        jdbc.update("""
                INSERT INTO experiment_run (id, operator_id, request_json, request_sha256)
                VALUES (?, ?, CAST(? AS jsonb), ?)
                """, candidate, operator, request.canonicalJson(), request.sha256());
        int inserted = jdbc.update("""
                INSERT INTO submission (operator_id, idempotency_key, request_sha256, run_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (operator_id, idempotency_key) DO NOTHING
                """, operator, key, request.sha256(), candidate);
        if (inserted == 1) {
            return new Submission(candidate, true);
        }
        // This transaction's candidate is not referenced; discard it before returning
        // the run committed by the first submitter. The unique-key conflict may have
        // waited for an in-flight submitter, so read after the INSERT attempt.
        jdbc.update("DELETE FROM experiment_run WHERE id = ?", candidate);
        List<SubmissionRow> rows = jdbc.query("""
                SELECT run_id, request_sha256 FROM submission
                WHERE operator_id = ? AND idempotency_key = ?
                """, (rs, rowNum) -> new SubmissionRow(
                rs.getObject("run_id", UUID.class), rs.getString("request_sha256")), operator, key);
        if (rows.size() != 1) {
            throw new IllegalStateException("Idempotency mapping disappeared");
        }
        SubmissionRow prior = rows.getFirst();
        if (!prior.requestSha256().equals(request.sha256())) {
            throw new IdempotencyConflict();
        }
        return new Submission(prior.runId(), false);
    }

    @Transactional(readOnly = true)
    public Optional<Snapshot> find(String operator, UUID id) {
        validateOperator(operator);
        List<Snapshot> rows = jdbc.query("""
                SELECT id, state, attempt_count, manifest_key, manifest_sha256, error_code
                FROM experiment_run WHERE id = ? AND operator_id = ?
                """, (rs, rowNum) -> new Snapshot(
                rs.getObject("id", UUID.class), rs.getString("state"), rs.getInt("attempt_count"),
                rs.getString("manifest_key"), rs.getString("manifest_sha256"),
                rs.getString("error_code")), id, operator);
        return rows.stream().findFirst();
    }

    @Transactional(readOnly = true)
    public Page list(String operator, UUID cursor, int limit) {
        validateOperator(operator);
        if (limit < 1 || limit > MAX_PAGE_SIZE) {
            throw new IllegalArgumentException("Invalid page size");
        }
        List<Summary> rows;
        if (cursor == null) {
            rows = jdbc.query("""
                    SELECT id, state, attempt_count, manifest_key, error_code, created_at
                    FROM experiment_run WHERE operator_id = ?
                    ORDER BY created_at DESC, id DESC LIMIT ?
                    """, SUMMARY, operator, limit + 1);
        } else {
            // Resolve the cursor first so an unknown or foreign run ID is a client
            // error rather than an indistinguishable empty page.
            Integer known = jdbc.queryForObject("""
                    SELECT COUNT(*) FROM experiment_run WHERE id = ? AND operator_id = ?
                    """, Integer.class, cursor, operator);
            if (known == null || known == 0) {
                throw new IllegalArgumentException("Unknown page cursor");
            }
            rows = jdbc.query("""
                    SELECT id, state, attempt_count, manifest_key, error_code, created_at
                    FROM experiment_run
                    WHERE operator_id = ? AND (created_at, id) <
                        (SELECT created_at, id FROM experiment_run WHERE id = ? AND operator_id = ?)
                    ORDER BY created_at DESC, id DESC LIMIT ?
                    """, SUMMARY, operator, cursor, operator, limit + 1);
        }
        if (rows.size() <= limit) {
            return new Page(List.copyOf(rows), null);
        }
        List<Summary> items = List.copyOf(rows.subList(0, limit));
        return new Page(items, items.getLast().id());
    }

    @Transactional
    public Optional<Snapshot> cancel(String operator, UUID id) {
        validateOperator(operator);
        jdbc.update("""
                UPDATE experiment_run
                SET state = CASE WHEN state = 'QUEUED' THEN 'CANCELLED'
                                 WHEN state = 'RUNNING' THEN 'CANCEL_REQUESTED'
                                 ELSE state END,
                    cancel_requested_at = CASE WHEN state = 'RUNNING' THEN CURRENT_TIMESTAMP
                                               ELSE cancel_requested_at END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND operator_id = ? AND state IN ('QUEUED', 'RUNNING')
                """, id, operator);
        return find(operator, id);
    }

    private static void validateOperator(String operator) {
        if (operator == null || !operator.matches("[A-Za-z0-9._:-]{1,64}")) {
            throw new IllegalArgumentException("Invalid operator identity");
        }
    }

    private static void validateKey(String key) {
        if (key == null || !key.matches("[A-Za-z0-9._:-]{1,128}")) {
            throw new IllegalArgumentException("Invalid idempotency key");
        }
    }

    private record SubmissionRow(UUID runId, String requestSha256) {}
}
