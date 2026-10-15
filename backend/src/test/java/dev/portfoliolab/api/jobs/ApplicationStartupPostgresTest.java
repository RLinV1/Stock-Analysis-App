package dev.portfoliolab.api.jobs;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;

import dev.portfoliolab.api.PortfolioLabApplication;
import dev.portfoliolab.api.contract.SyntheticRequestContract;
import liquibase.integration.spring.SpringLiquibase;
import org.junit.jupiter.api.Test;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.jdbc.core.JdbcTemplate;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;

/** Exercises Boot startup rather than constructing the migration bean manually. */
@Testcontainers(disabledWithoutDocker = true)
class ApplicationStartupPostgresTest {
    @Container
    static final PostgreSQLContainer POSTGRES = new PostgreSQLContainer("postgres:17.11");

    private ConfigurableApplicationContext start() {
        return new SpringApplicationBuilder(PortfolioLabApplication.class)
                .web(WebApplicationType.NONE)
                .run("--spring.datasource.url=" + POSTGRES.getJdbcUrl(),
                        "--spring.datasource.username=" + POSTGRES.getUsername(),
                        "--spring.datasource.password=" + POSTGRES.getPassword(),
                        "--PORTFOLIO_OPERATOR_TOKEN=unit-test-secret-startup",
                        "--PORTFOLIO_CORS_ALLOWED_ORIGINS=",
                        "--spring.main.banner-mode=off");
    }

    @Test
    void migratesFreshDatabaseAndReopensPersistedTransactionalSubmission() throws Exception {
        var request = SyntheticRequestContract.parse(Files.readAllBytes(
                Path.of("../contracts/examples/synthetic-smoke.v1.json")));
        UUID runId;
        try (var context = start()) {
            assertNotNull(context.getBean(SpringLiquibase.class));
            var jdbc = context.getBean(JdbcTemplate.class);
            assertEquals(2, jdbc.queryForObject("SELECT count(*) FROM databasechangelog", Integer.class));
            var runs = context.getBean(RunRepository.class);
            runId = runs.submit("startup-test", "same-draft", request).runId();
            var changed = SyntheticRequestContract.parse(request.canonicalJson()
                    .replace("\"epochs\":1", "\"epochs\":2").getBytes(java.nio.charset.StandardCharsets.UTF_8));
            assertThrows(RunRepository.IdempotencyConflict.class,
                    () -> runs.submit("startup-test", "same-draft", changed));
            // The conflicting candidate insert must roll back through Boot's proxy.
            assertEquals(1, jdbc.queryForObject("SELECT count(*) FROM experiment_run", Integer.class));
        }
        try (var context = start()) {
            var runs = context.getBean(RunRepository.class);
            var repeated = runs.submit("startup-test", "same-draft", request);
            assertEquals(runId, repeated.runId());
            assertFalse(repeated.created());
            assertEquals("QUEUED", runs.find("startup-test", runId).orElseThrow().state());
            assertEquals(2, context.getBean(JdbcTemplate.class)
                    .queryForObject("SELECT count(*) FROM databasechangelog", Integer.class));
        }
    }
}
