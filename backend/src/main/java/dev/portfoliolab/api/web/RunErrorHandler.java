package dev.portfoliolab.api.web;

import java.util.Map;

import dev.portfoliolab.api.jobs.ArtifactStore.ArtifactUnavailable;
import dev.portfoliolab.api.jobs.RunRepository.IdempotencyConflict;
import dev.portfoliolab.api.web.RunController.RunNotComplete;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MissingRequestHeaderException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

@RestControllerAdvice
public final class RunErrorHandler {
    // A malformed run ID path segment is a client error with the same stable code.
    @ExceptionHandler({IllegalArgumentException.class, MissingRequestHeaderException.class,
            MethodArgumentTypeMismatchException.class})
    public ResponseEntity<Map<String, Object>> invalidRequest(Exception ignored) {
        return problem(HttpStatus.BAD_REQUEST, "invalid_request");
    }

    @ExceptionHandler(IdempotencyConflict.class)
    public ResponseEntity<Map<String, Object>> idempotencyConflict(IdempotencyConflict ignored) {
        return problem(HttpStatus.CONFLICT, "idempotency_conflict");
    }

    @ExceptionHandler(RunNotComplete.class)
    public ResponseEntity<Map<String, Object>> runNotComplete(RunNotComplete ignored) {
        return problem(HttpStatus.CONFLICT, "run_not_complete");
    }

    @ExceptionHandler(ArtifactUnavailable.class)
    public ResponseEntity<Map<String, Object>> artifactUnavailable(ArtifactUnavailable failure) {
        // Stable code only; object keys, bucket names and SDK messages stay server-side.
        return problem(HttpStatus.BAD_GATEWAY, failure.code());
    }

    private static ResponseEntity<Map<String, Object>> problem(HttpStatus status, String code) {
        return ResponseEntity.status(status).contentType(MediaType.parseMediaType("application/problem+json"))
                .body(Map.of("type", "about:blank", "title", status.getReasonPhrase(),
                        "status", status.value(), "code", code));
    }
}
