package dev.portfoliolab.api.web;

import java.io.IOException;
import java.net.URI;
import java.util.List;
import java.util.UUID;
import java.util.regex.Pattern;

import jakarta.servlet.http.HttpServletRequest;
import dev.portfoliolab.api.contract.SyntheticRequestContract;
import dev.portfoliolab.api.jobs.ArtifactStore;
import dev.portfoliolab.api.jobs.RunRepository;
import dev.portfoliolab.api.jobs.RunRepository.Snapshot;
import dev.portfoliolab.api.jobs.RunRepository.Summary;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** First local HTTP surface; completed artifact retrieval follows the worker. */
@RestController
@RequestMapping("/api/v1/runs")
public final class RunController {
    private static final String LOCAL_OPERATOR = "local";
    private static final int DEFAULT_PAGE_SIZE = 20;
    private static final Pattern PAGE_SIZE = Pattern.compile("[0-9]{1,2}");
    // Canonical 8-4-4-4-12 form only; UUID.fromString alone accepts shortened groups.
    private static final Pattern CURSOR = Pattern.compile(
            "[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}");
    private final RunRepository runs;
    private final ArtifactStore artifacts;

    public RunController(RunRepository runs, ArtifactStore artifacts) {
        this.runs = runs;
        this.artifacts = artifacts;
    }

    /** The run exists but has no registered result yet. */
    public static final class RunNotComplete extends RuntimeException {
        public RunNotComplete() {
            super("Run has no completed manifest");
        }
    }

    public record AcceptedRun(UUID runId) {}
    public record RunStatus(UUID runId, String state, int attemptCount,
                            boolean manifestAvailable, String errorCode) {}
    /** createdAt is an ISO-8601 UTC instant string, independent of Jackson date settings. */
    public record RunSummary(UUID runId, String state, int attemptCount,
                             boolean manifestAvailable, String errorCode, String createdAt) {}
    public record RunPage(List<RunSummary> items, UUID nextCursor) {}

    @GetMapping(produces = "application/json")
    public ResponseEntity<RunPage> list(@RequestParam(name = "limit", required = false) String limit,
                                        @RequestParam(name = "cursor", required = false) String cursor) {
        int size = parsePageSize(limit);
        UUID after = parseCursor(cursor);
        var page = runs.list(LOCAL_OPERATOR, after, size);
        List<RunSummary> items = page.items().stream().map(RunController::toSummary).toList();
        return ResponseEntity.ok(new RunPage(items, page.nextCursor()));
    }

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

    @GetMapping(path = "/{id}/manifest", produces = "application/json")
    public ResponseEntity<byte[]> manifest(@PathVariable UUID id) {
        Snapshot snapshot = completed(id);
        if (snapshot == null) {
            return ResponseEntity.notFound().build();
        }
        return immutableJson(artifacts.readVerified(snapshot.manifestKey(), snapshot.manifestSha256()));
    }

    @GetMapping(path = "/{id}/report", produces = "application/json")
    public ResponseEntity<byte[]> report(@PathVariable UUID id) {
        Snapshot snapshot = completed(id);
        if (snapshot == null) {
            return ResponseEntity.notFound().build();
        }
        byte[] index = artifacts.readVerified(snapshot.manifestKey(), snapshot.manifestSha256());
        ArtifactStore.IndexedFile report = ArtifactStore.reportEntry(index, snapshot.manifestKey());
        return immutableJson(artifacts.readVerified(report.key(), report.sha256()));
    }

    /** Null for an unknown run; throws before any storage read when no result is registered. */
    private Snapshot completed(UUID id) {
        Snapshot snapshot = runs.find(LOCAL_OPERATOR, id).orElse(null);
        if (snapshot != null && (!"COMPLETE".equals(snapshot.state()) || snapshot.manifestKey() == null)) {
            throw new RunNotComplete();
        }
        return snapshot;
    }

    private static ResponseEntity<byte[]> immutableJson(byte[] content) {
        return ResponseEntity.ok().contentType(MediaType.APPLICATION_JSON)
                .header("Cache-Control", "private, max-age=31536000, immutable")
                .body(content);
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

    private static RunSummary toSummary(Summary summary) {
        return new RunSummary(summary.id(), summary.state(), summary.attemptCount(),
                summary.manifestKey() != null && "COMPLETE".equals(summary.state()),
                summary.errorCode(), summary.createdAt().toString());
    }

    private static int parsePageSize(String limit) {
        if (limit == null) {
            return DEFAULT_PAGE_SIZE;
        }
        if (!PAGE_SIZE.matcher(limit).matches()) {
            throw new IllegalArgumentException("Invalid page size");
        }
        int size = Integer.parseInt(limit);
        if (size < 1 || size > RunRepository.MAX_PAGE_SIZE) {
            throw new IllegalArgumentException("Invalid page size");
        }
        return size;
    }

    private static UUID parseCursor(String cursor) {
        if (cursor == null) {
            return null;
        }
        if (!CURSOR.matcher(cursor).matches()) {
            throw new IllegalArgumentException("Invalid page cursor");
        }
        return UUID.fromString(cursor);
    }
}
