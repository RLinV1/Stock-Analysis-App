package dev.portfoliolab.api.web;

import java.util.Map;

import dev.portfoliolab.api.jobs.RunRepository.IdempotencyConflict;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MissingRequestHeaderException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public final class RunErrorHandler {
    @ExceptionHandler({IllegalArgumentException.class, MissingRequestHeaderException.class})
    public ResponseEntity<Map<String, Object>> invalidRequest(Exception ignored) {
        return problem(HttpStatus.BAD_REQUEST, "invalid_request");
    }

    @ExceptionHandler(IdempotencyConflict.class)
    public ResponseEntity<Map<String, Object>> idempotencyConflict(IdempotencyConflict ignored) {
        return problem(HttpStatus.CONFLICT, "idempotency_conflict");
    }

    private static ResponseEntity<Map<String, Object>> problem(HttpStatus status, String code) {
        return ResponseEntity.status(status).contentType(MediaType.parseMediaType("application/problem+json"))
                .body(Map.of("type", "about:blank", "title", status.getReasonPhrase(),
                        "status", status.value(), "code", code));
    }
}
