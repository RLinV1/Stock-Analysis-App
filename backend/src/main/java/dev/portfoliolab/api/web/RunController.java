package dev.portfoliolab.api.web;

import java.io.IOException;
import java.net.URI;
import java.util.UUID;

import jakarta.servlet.http.HttpServletRequest;
import dev.portfoliolab.api.contract.SyntheticRequestContract;
import dev.portfoliolab.api.jobs.RunRepository;
import dev.portfoliolab.api.jobs.RunRepository.Snapshot;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** First local HTTP surface; completed artifact retrieval follows the worker. */
@RestController
@RequestMapping("/api/v1/runs")
public final class RunController {
    private static final String LOCAL_OPERATOR = "local";
    private final RunRepository runs;

    public RunController(RunRepository runs) {
        this.runs = runs;
    }

    public record AcceptedRun(UUID runId) {}
    public record RunStatus(UUID runId, String state, int attemptCount,
                            boolean manifestAvailable, String errorCode) {}

    @PostMapping(consumes = "application/json", produces = "application/json")
    public ResponseEntity<AcceptedRun> submit(@RequestHeader("Idempotency-Key") String key,
                                               HttpServletRequest requestBody) throws IOException {
        // Read one byte beyond the limit, then reject before Spring buffers an
        // arbitrarily large authenticated body into a byte[] argument.
        byte[] body = requestBody.getInputStream().readNBytes(8193);
        var request = SyntheticRequestContract.parse(body);
        var accepted = runs.submit(LOCAL_OPERATOR, key, request);
        URI location = URI.create("/api/v1/runs/" + accepted.runId());
        return ResponseEntity.accepted().location(location)
                .body(new AcceptedRun(accepted.runId()));
    }

    @GetMapping(path = "/{id}", produces = "application/json")
    public ResponseEntity<RunStatus> status(@PathVariable UUID id) {
        return runs.find(LOCAL_OPERATOR, id).map(snapshot -> ResponseEntity.ok(toStatus(snapshot)))
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @PostMapping(path = "/{id}/cancel", produces = "application/json")
    public ResponseEntity<RunStatus> cancel(@PathVariable UUID id) {
        return runs.cancel(LOCAL_OPERATOR, id).map(snapshot -> ResponseEntity.ok(toStatus(snapshot)))
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    private static RunStatus toStatus(Snapshot snapshot) {
        return new RunStatus(snapshot.id(), snapshot.state(), snapshot.attemptCount(),
                snapshot.manifestKey() != null && "COMPLETE".equals(snapshot.state()),
                snapshot.errorCode());
    }
}
