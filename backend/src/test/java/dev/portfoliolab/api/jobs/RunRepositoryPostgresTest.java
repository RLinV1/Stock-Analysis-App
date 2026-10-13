package dev.portfoliolab.api.jobs;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import dev.portfoliolab.api.contract.SyntheticRequestContract;
import dev.portfoliolab.api.contract.SyntheticRequestContract.Accepted;
import dev.portfoliolab.api.jobs.RunRepository.IdempotencyConflict;
import dev.portfoliolab.api.jobs.RunRepository.Page;
import dev.portfoliolab.api.jobs.RunRepository.Snapshot;
import dev.portfoliolab.api.jobs.RunRepository.Submission;
import dev.portfoliolab.api.jobs.RunRepository.Summary;
import liquibase.integration.spring.SpringLiquibase;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.core.io.DefaultResourceLoader;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.transaction.support.TransactionTemplate;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;

/**
 * Runs RunRepository against a real PostgreSQL with the production Liquibase changelog.
 * Skipped automatically when no Docker engine is reachable.
 *
 * <p>There is no Spring proxy here, so RunRepository's {@code @Transactional} annotations
 * have no effect. Every submit is wrapped in its own TransactionTemplate to match the single
 * transaction production gets; other calls run in auto-commit mode.
 */
@Testcontainers(disabledWithoutDocker = true)
class RunRepositoryPostgresTest {
    private static final String OPERATOR = "local-operator";
    private static final String OTHER_OPERATOR = "other-operator";

    @Container
    static final PostgreSQLContainer POSTGRES = new PostgreSQLContainer("postgres:17.11");

    private static DriverManagerDataSource dataSource;
    private static JdbcTemplate jdbc;
    private static TransactionTemplate transactions;
    private static RunRepository repository;

    @BeforeAll
    static void migrate() throws Exception {
        dataSource = new DriverManagerDataSource(
                POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword());
        dataSource.setDriverClassName("org.postgresql.Driver");

        SpringLiquibase liquibase = new SpringLiquibase();
        liquibase.setDataSource(dataSource);
        liquibase.setChangeLog("classpath:db/changelog/db.changelog-master.yaml");
        liquibase.setResourceLoader(new DefaultResourceLoader());
        liquibase.afterPropertiesSet();

        jdbc = new JdbcTemplate(dataSource);
        transactions = new TransactionTemplate(new DataSourceTransactionManager(dataSource));
        repository = new RunRepository(jdbc);
    }

    @BeforeEach
    void clean() {
        jdbc.execute("TRUNCATE submission, run_attempt, experiment_run CASCADE");
    }

    @Test
    void liquibaseAppliesBothChangesetsAndListIndex() {
        List<String> ids = jdbc.queryForList(
                "SELECT id FROM databasechangelog ORDER BY orderexecuted", String.class);
        assertEquals(List.of("001-synthetic-jobs", "002-run-list-index"), ids);
        Integer index = jdbc.queryForObject("""
                SELECT COUNT(*) FROM pg_indexes
                WHERE tablename = 'experiment_run' AND indexname = 'experiment_run_operator_created_idx'
                """, Integer.class);
        assertEquals(1, index);
    }

    @Test
    void submitCreatesQueuedRunWithCanonicalRequest() throws Exception {
        Accepted request = smoke();
        Submission submission = submit(OPERATOR, "key-1", request);

        assertTrue(submission.created());
        Snapshot snapshot = repository.find(OPERATOR, submission.runId()).orElseThrow();
        assertEquals("QUEUED", snapshot.state());
        assertEquals(0, snapshot.attemptCount());
        assertNull(snapshot.manifestKey());
        assertNull(snapshot.manifestSha256());
        assertNull(snapshot.errorCode());

        // jsonb normalises whitespace and key order, so compare as jsonb rather than text.
        Boolean sameJson = jdbc.queryForObject(
                "SELECT request_json = CAST(? AS jsonb) FROM experiment_run WHERE id = ?",
                Boolean.class, request.canonicalJson(), submission.runId());
        assertEquals(Boolean.TRUE, sameJson);
        assertEquals(request.sha256(), jdbc.queryForObject(
                "SELECT request_sha256 FROM experiment_run WHERE id = ?", String.class,
                submission.runId()));
        assertEquals(request.sha256(), jdbc.queryForObject(
                "SELECT request_sha256 FROM submission WHERE operator_id = ? AND idempotency_key = ?",
                String.class, OPERATOR, "key-1"));
        assertEquals(1, runCount());
    }

    @Test
    void sameKeyAndBodyReturnsExistingRun() throws Exception {
        Submission first = submit(OPERATOR, "key-1", smoke());
        Submission second = submit(OPERATOR, "key-1", smoke());

        assertTrue(first.created());
        assertFalse(second.created());
        assertEquals(first.runId(), second.runId());
        assertEquals(1, runCount());
    }

    @Test
    void sameKeyDifferentBodyConflicts() throws Exception {
        Submission first = submit(OPERATOR, "key-1", smoke());
        Accepted different = variant();

        assertThrows(IdempotencyConflict.class, () -> submit(OPERATOR, "key-1", different));
        assertEquals(1, runCount());
        assertEquals(first.runId(), jdbc.queryForObject("SELECT id FROM experiment_run", UUID.class));
    }

    @Test
    void concurrentDuplicateSubmissionsCreateOneRun() throws Exception {
        Accepted request = smoke();
        int threads = 8;
        CountDownLatch start = new CountDownLatch(1);
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        try {
            List<Future<Submission>> futures = new ArrayList<>();
            for (int i = 0; i < threads; i++) {
                futures.add(pool.submit(() -> {
                    start.await();
                    return submit(OPERATOR, "same-key", request);
                }));
            }
            start.countDown();
            Set<UUID> runIds = new HashSet<>();
            int created = 0;
            for (Future<Submission> future : futures) {
                Submission submission = future.get(60, TimeUnit.SECONDS);
                runIds.add(submission.runId());
                if (submission.created()) {
                    created++;
                }
            }
            assertEquals(1, runIds.size());
            assertEquals(1, created);
            assertEquals(1, runCount());
            assertEquals(runIds.iterator().next(),
                    jdbc.queryForObject("SELECT id FROM experiment_run", UUID.class));
        } finally {
            pool.shutdownNow();
        }
    }

    @Test
    void findIsOperatorScoped() throws Exception {
        UUID runId = submit(OPERATOR, "key-1", smoke()).runId();

        assertTrue(repository.find(OPERATOR, runId).isPresent());
        assertEquals(Optional.empty(), repository.find(OTHER_OPERATOR, runId));
        assertEquals(Optional.empty(), repository.find(OPERATOR, UUID.randomUUID()));
    }

    @Test
    void cancelQueuedRunCancelsIt() throws Exception {
        UUID runId = submit(OPERATOR, "key-1", smoke()).runId();

        assertEquals(Optional.empty(), repository.cancel(OTHER_OPERATOR, runId));
        assertEquals("QUEUED", repository.find(OPERATOR, runId).orElseThrow().state());

        Snapshot cancelled = repository.cancel(OPERATOR, runId).orElseThrow();
        assertEquals("CANCELLED", cancelled.state());
        assertNull(cancelRequestedAt(runId));
    }

    @Test
    void cancelRunningRunRequestsCancellation() throws Exception {
        UUID runId = submit(OPERATOR, "key-1", smoke()).runId();
        jdbc.update("UPDATE experiment_run SET state = 'RUNNING', attempt_count = 1 WHERE id = ?", runId);

        Snapshot requested = repository.cancel(OPERATOR, runId).orElseThrow();
        assertEquals("CANCEL_REQUESTED", requested.state());
        assertNotNull(cancelRequestedAt(runId));
    }

    @Test
    void cancelCompleteRunLeavesItUnchanged() throws Exception {
        UUID runId = submit(OPERATOR, "key-1", smoke()).runId();
        String sha = "a".repeat(64);
        jdbc.update("""
                UPDATE experiment_run
                SET state = 'COMPLETE', attempt_count = 1, manifest_key = ?, manifest_sha256 = ?
                WHERE id = ?
                """, "runs/" + runId + "/manifest.json", sha, runId);

        Snapshot snapshot = repository.cancel(OPERATOR, runId).orElseThrow();
        assertEquals("COMPLETE", snapshot.state());
        assertEquals("runs/" + runId + "/manifest.json", snapshot.manifestKey());
        assertEquals(sha, snapshot.manifestSha256());
        assertNull(cancelRequestedAt(runId));
    }

    @Test
    void manifestConstraintRejectsCompleteWithoutManifest() throws Exception {
        UUID runId = submit(OPERATOR, "key-1", smoke()).runId();

        assertThrows(DataIntegrityViolationException.class, () -> jdbc.update(
                "UPDATE experiment_run SET state = 'COMPLETE' WHERE id = ?", runId));
        assertEquals("QUEUED", repository.find(OPERATOR, runId).orElseThrow().state());
    }

    @Test
    void listPagesNewestFirstWithoutDuplicatesOrSkips() throws Exception {
        Accepted request = smoke();
        Instant base = Instant.parse("2026-01-01T00:00:00Z");
        List<UUID> runs = new ArrayList<>();
        for (int i = 0; i < 6; i++) {
            runs.add(submit(OPERATOR, "key-" + i, request).runId());
        }
        // Distinct timestamps, plus one tie so the id tiebreaker is exercised.
        int[] offsets = {0, 10, 20, 20, 30, 40};
        for (int i = 0; i < runs.size(); i++) {
            jdbc.update("UPDATE experiment_run SET created_at = ? WHERE id = ?",
                    Timestamp.from(base.plusSeconds(offsets[i])), runs.get(i));
        }
        UUID foreign = submit(OTHER_OPERATOR, "key-0", request).runId();

        // PostgreSQL compares UUIDs bytewise, unlike UUID.compareTo, so ask it for the order.
        List<UUID> expected = jdbc.queryForList("""
                SELECT id FROM experiment_run WHERE operator_id = ?
                ORDER BY created_at DESC, id DESC
                """, UUID.class, OPERATOR);
        assertEquals(runs.get(5), expected.getFirst());
        assertEquals(runs.get(0), expected.getLast());

        List<UUID> seen = new ArrayList<>();
        UUID cursor = null;
        List<Integer> pageSizes = new ArrayList<>();
        do {
            Page page = repository.list(OPERATOR, cursor, 2);
            pageSizes.add(page.items().size());
            Instant previous = null;
            for (Summary summary : page.items()) {
                assertEquals("QUEUED", summary.state());
                if (previous != null) {
                    assertFalse(summary.createdAt().isAfter(previous));
                }
                previous = summary.createdAt();
                seen.add(summary.id());
            }
            cursor = page.nextCursor();
            if (cursor != null) {
                assertEquals(page.items().getLast().id(), cursor);
            }
        } while (cursor != null && pageSizes.size() < 10);

        assertEquals(List.of(2, 2, 2), pageSizes);
        assertEquals(expected, seen);
        assertEquals(6, new HashSet<>(seen).size());
        assertFalse(seen.contains(foreign));
    }

    @Test
    void listWithExactFitHasNoNextCursor() throws Exception {
        submit(OPERATOR, "key-1", smoke());
        submit(OPERATOR, "key-2", smoke());

        Page page = repository.list(OPERATOR, null, 2);
        assertEquals(2, page.items().size());
        assertNull(page.nextCursor());
        assertTrue(repository.list(OTHER_OPERATOR, null, 2).items().isEmpty());
    }

    @Test
    void listRejectsUnknownOrForeignCursor() throws Exception {
        submit(OPERATOR, "key-1", smoke());
        UUID foreign = submit(OTHER_OPERATOR, "key-1", smoke()).runId();

        assertThrows(IllegalArgumentException.class,
                () -> repository.list(OPERATOR, UUID.randomUUID(), 2));
        assertThrows(IllegalArgumentException.class,
                () -> repository.list(OPERATOR, foreign, 2));
    }

    @Test
    void listEnforcesLimitBounds() {
        assertThrows(IllegalArgumentException.class, () -> repository.list(OPERATOR, null, 0));
        assertThrows(IllegalArgumentException.class,
                () -> repository.list(OPERATOR, null, RunRepository.MAX_PAGE_SIZE + 1));
        assertTrue(repository.list(OPERATOR, null, 1).items().isEmpty());
        assertTrue(repository.list(OPERATOR, null, RunRepository.MAX_PAGE_SIZE).items().isEmpty());
    }

    private static Submission submit(String operator, String key, Accepted request) {
        return transactions.execute(status -> repository.submit(operator, key, request));
    }

    private static int runCount() {
        return jdbc.queryForObject("SELECT COUNT(*) FROM experiment_run", Integer.class);
    }

    private static Timestamp cancelRequestedAt(UUID runId) {
        return jdbc.queryForObject(
                "SELECT cancel_requested_at FROM experiment_run WHERE id = ?", Timestamp.class, runId);
    }

    private static Accepted smoke() throws Exception {
        return SyntheticRequestContract.parse(smokeBytes());
    }

    private static Accepted variant() throws Exception {
        String json = new String(smokeBytes(), StandardCharsets.UTF_8);
        String changed = json.replace("\"cost_bps\": 1", "\"cost_bps\": 2");
        if (changed.equals(json)) {
            throw new IllegalStateException("Smoke example no longer contains cost_bps 1");
        }
        return SyntheticRequestContract.parse(changed.getBytes(StandardCharsets.UTF_8));
    }

    private static byte[] smokeBytes() throws Exception {
        return Files.readAllBytes(Path.of("..", "contracts", "examples", "synthetic-smoke.v1.json"));
    }
}
