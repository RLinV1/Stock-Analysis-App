package dev.portfoliolab.api.web;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.not;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import java.util.UUID;

import dev.portfoliolab.api.contract.SyntheticRequestContract.Accepted;
import dev.portfoliolab.api.jobs.ArtifactStore;
import dev.portfoliolab.api.jobs.ArtifactStore.ArtifactUnavailable;
import dev.portfoliolab.api.jobs.RunRepository;
import dev.portfoliolab.api.jobs.RunRepository.IdempotencyConflict;
import dev.portfoliolab.api.jobs.RunRepository.Snapshot;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

class RunControllerTest {
    private final FakeRepository repository = new FakeRepository();
    private final FakeArtifacts artifacts = new FakeArtifacts();

    private org.springframework.test.web.servlet.MockMvc mvc() {
        return MockMvcBuilders.standaloneSetup(new RunController(repository, artifacts))
                .setControllerAdvice(new RunErrorHandler())
                .addFilters(new LocalOperatorFilter("unit-test-secret-123"))
                .build();
    }

    @Test
    void requiresBearerBeforeAcceptingCompute() throws Exception {
        byte[] body = Files.readAllBytes(Path.of("..", "contracts", "examples", "synthetic-smoke.v1.json"));
        mvc().perform(post("/api/v1/runs").contentType("application/json")
                .header("Idempotency-Key", "one").content(body))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value("unauthorized"));
        assertEquals(0, repository.submissions);
    }

    @Test
    void pathParameterVariantsStillRequireBearer() throws Exception {
        UUID id = UUID.randomUUID();
        for (String path : new String[] {"/api;x=1/v1/runs/" + id, "/api/v1;x=1/runs/" + id,
                "/api/v1/runs;x=1/" + id}) {
            mvc().perform(get(path)).andExpect(status().isUnauthorized())
                    .andExpect(jsonPath("$.code").value("unauthorized"));
        }
    }

    @Test
    void onlyExactHealthPathSkipsBearer() throws Exception {
        mvc().perform(get("/actuator/health")).andExpect(status().isNotFound());
        for (String path : new String[] {"/actuator/health;x=1", "/actuator/env", "/unknown"}) {
            mvc().perform(get(path)).andExpect(status().isUnauthorized());
        }
    }

    @Test
    void acceptsValidBodyAndReturnsLocation() throws Exception {
        byte[] body = Files.readAllBytes(Path.of("..", "contracts", "examples", "synthetic-smoke.v1.json"));
        UUID id = UUID.randomUUID();
        repository.nextId = id;
        mvc().perform(post("/api/v1/runs").contentType("application/json")
                .header("Authorization", "Bearer unit-test-secret-123")
                .header("Idempotency-Key", "one").content(body))
                .andExpect(status().isAccepted())
                .andExpect(header().string("Location", "/api/v1/runs/" + id))
                .andExpect(jsonPath("$.runId").value(id.toString()));
        assertEquals(1, repository.submissions);
    }

    @Test
    void rejectsInvalidBodyBeforeRepository() throws Exception {
        mvc().perform(post("/api/v1/runs").contentType("application/json")
                .header("Authorization", "Bearer unit-test-secret-123")
                .header("Idempotency-Key", "one").content("{\"contract_version\":2}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("invalid_request"));
        assertEquals(0, repository.submissions);
    }

    @Test
    void rejectsOversizedBodyBeforeRepository() throws Exception {
        mvc().perform(post("/api/v1/runs").contentType("application/json")
                .header("Authorization", "Bearer unit-test-secret-123")
                .header("Idempotency-Key", "one").content(new byte[8193]))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("invalid_request"));
        assertEquals(0, repository.submissions);
    }

    @Test
    void reportsConflictingIdempotencyReuse() throws Exception {
        byte[] body = Files.readAllBytes(Path.of("..", "contracts", "examples", "synthetic-smoke.v1.json"));
        repository.conflict = true;
        mvc().perform(post("/api/v1/runs").contentType("application/json")
                .header("Authorization", "Bearer unit-test-secret-123")
                .header("Idempotency-Key", "one").content(body))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("idempotency_conflict"));
    }

    @Test
    void rejectsMissingIdempotencyKey() throws Exception {
        byte[] body = Files.readAllBytes(Path.of("..", "contracts", "examples", "synthetic-smoke.v1.json"));
        mvc().perform(post("/api/v1/runs").contentType("application/json")
                .header("Authorization", "Bearer unit-test-secret-123").content(body))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("invalid_request"));
        assertEquals(0, repository.submissions);
    }

    @Test
    void statusHidesManifestUntilComplete() throws Exception {
        UUID id = UUID.randomUUID();
        repository.snapshot = new Snapshot(id, "RUNNING", 1, null, null, null);
        mvc().perform(get("/api/v1/runs/" + id).header("Authorization", "Bearer unit-test-secret-123"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.state").value("RUNNING"))
                .andExpect(jsonPath("$.attemptCount").value(1))
                .andExpect(jsonPath("$.manifestAvailable").value(false));
        repository.snapshot = new Snapshot(id, "COMPLETE", 1, "runs/key", "a".repeat(64), null);
        mvc().perform(get("/api/v1/runs/" + id).header("Authorization", "Bearer unit-test-secret-123"))
                .andExpect(jsonPath("$.manifestAvailable").value(true))
                .andExpect(jsonPath("$.manifestKey").doesNotExist());
    }

    @Test
    void unknownRunIsNotFoundForStatusAndCancel() throws Exception {
        UUID id = UUID.randomUUID();
        mvc().perform(get("/api/v1/runs/" + id).header("Authorization", "Bearer unit-test-secret-123"))
                .andExpect(status().isNotFound());
        mvc().perform(post("/api/v1/runs/" + id + "/cancel")
                .header("Authorization", "Bearer unit-test-secret-123"))
                .andExpect(status().isNotFound());
    }

    @Test
    void cancelReturnsResultingState() throws Exception {
        UUID id = UUID.randomUUID();
        repository.snapshot = new Snapshot(id, "CANCEL_REQUESTED", 1, null, null, null);
        mvc().perform(post("/api/v1/runs/" + id + "/cancel")
                .header("Authorization", "Bearer unit-test-secret-123"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.state").value("CANCEL_REQUESTED"));
        assertEquals(1, repository.cancels);
    }

    @Test
    void manifestRequiresBearer() throws Exception {
        mvc().perform(get("/api/v1/runs/" + UUID.randomUUID() + "/manifest"))
                .andExpect(status().isUnauthorized());
        assertEquals(0, artifacts.reads);
    }

    @Test
    void manifestReturnsVerifiedBytesForCompleteRun() throws Exception {
        UUID id = UUID.randomUUID();
        String digest = "b".repeat(64);
        repository.snapshot = new Snapshot(id, "COMPLETE", 1, "runs/" + id + "/index.json", digest, null);
        artifacts.content = "{\"kind\":\"synthetic-a0\"}".getBytes(StandardCharsets.UTF_8);
        mvc().perform(get("/api/v1/runs/" + id + "/manifest")
                .header("Authorization", "Bearer unit-test-secret-123"))
                .andExpect(status().isOk())
                .andExpect(header().string("Content-Type", "application/json"))
                .andExpect(content().string("{\"kind\":\"synthetic-a0\"}"));
        assertEquals("runs/" + id + "/index.json", artifacts.lastKey);
        assertEquals(digest, artifacts.lastSha256);
    }

    @Test
    void manifestOfIncompleteRunIsConflictWithoutStorageRead() throws Exception {
        UUID id = UUID.randomUUID();
        repository.snapshot = new Snapshot(id, "RUNNING", 1, null, null, null);
        mvc().perform(get("/api/v1/runs/" + id + "/manifest")
                .header("Authorization", "Bearer unit-test-secret-123"))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("run_not_complete"));
        assertEquals(0, artifacts.reads);
    }

    @Test
    void manifestOfUnknownRunIsNotFound() throws Exception {
        mvc().perform(get("/api/v1/runs/" + UUID.randomUUID() + "/manifest")
                .header("Authorization", "Bearer unit-test-secret-123"))
                .andExpect(status().isNotFound());
        assertEquals(0, artifacts.reads);
    }

    @Test
    void manifestIntegrityFailureIsBadGatewayWithStableCode() throws Exception {
        UUID id = UUID.randomUUID();
        repository.snapshot = new Snapshot(id, "COMPLETE", 1, "runs/secret-key", "c".repeat(64), null);
        artifacts.failure = new ArtifactUnavailable("artifact_integrity_failure", null);
        mvc().perform(get("/api/v1/runs/" + id + "/manifest")
                .header("Authorization", "Bearer unit-test-secret-123"))
                .andExpect(status().isBadGateway())
                .andExpect(jsonPath("$.code").value("artifact_integrity_failure"))
                .andExpect(content().string(not(containsString("secret-key"))));
    }

    private static final class FakeArtifacts extends ArtifactStore {
        private int reads;
        private byte[] content;
        private ArtifactUnavailable failure;
        private String lastKey;
        private String lastSha256;

        private FakeArtifacts() {
            super(null, "unused");
        }

        @Override
        public byte[] readVerified(String key, String expectedSha256) {
            reads++;
            lastKey = key;
            lastSha256 = expectedSha256;
            if (failure != null) {
                throw failure;
            }
            return content;
        }
    }

    private static final class FakeRepository extends RunRepository {
        private int submissions;
        private int cancels;
        private UUID nextId;
        private boolean conflict;
        private Snapshot snapshot;

        private FakeRepository() {
            super(null);
        }

        @Override
        public Submission submit(String operator, String key, Accepted request) {
            submissions++;
            assertEquals("local", operator);
            assertEquals("one", key);
            if (conflict) {
                throw new IdempotencyConflict();
            }
            return new Submission(nextId, true);
        }

        @Override
        public Optional<Snapshot> find(String operator, UUID id) {
            assertEquals("local", operator);
            return Optional.ofNullable(snapshot).filter(row -> row.id().equals(id));
        }

        @Override
        public Optional<Snapshot> cancel(String operator, UUID id) {
            cancels++;
            return find(operator, id);
        }
    }
}
