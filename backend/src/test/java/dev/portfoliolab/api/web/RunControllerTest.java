package dev.portfoliolab.api.web;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;

import dev.portfoliolab.api.contract.SyntheticRequestContract.Accepted;
import dev.portfoliolab.api.jobs.RunRepository;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

class RunControllerTest {
    private final FakeRepository repository = new FakeRepository();

    private org.springframework.test.web.servlet.MockMvc mvc() {
        return MockMvcBuilders.standaloneSetup(new RunController(repository))
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

    private static final class FakeRepository extends RunRepository {
        private int submissions;
        private UUID nextId;

        private FakeRepository() {
            super(null);
        }

        @Override
        public Submission submit(String operator, String key, Accepted request) {
            submissions++;
            assertEquals("local", operator);
            assertEquals("one", key);
            return new Submission(nextId, true);
        }
    }
}
