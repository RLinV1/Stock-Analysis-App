package dev.portfoliolab.api.web;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/** Single-operator local credential until a broader identity design is approved. */
@Component
public final class LocalOperatorFilter extends OncePerRequestFilter {
    private final byte[] expected;

    public LocalOperatorFilter(@Value("${PORTFOLIO_OPERATOR_TOKEN:}") String secret) {
        if (secret == null || secret.length() < 16) {
            throw new IllegalStateException("PORTFOLIO_OPERATOR_TOKEN must contain at least 16 characters");
        }
        this.expected = secret.getBytes(StandardCharsets.UTF_8);
    }

    // Fail closed: only the exact raw health URI is public. A prefix allowlist on the
    // raw URI let path-parameter variants such as /api;x/v1/runs reach controllers.
    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return "/actuator/health".equals(request.getRequestURI());
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        String authorization = request.getHeader("Authorization");
        if (authorization == null || !authorization.startsWith("Bearer ")
                || !MessageDigest.isEqual(expected,
                    authorization.substring(7).getBytes(StandardCharsets.UTF_8))) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.setContentType("application/problem+json");
            response.getWriter().write("{\"type\":\"about:blank\",\"title\":\"Unauthorized\","
                    + "\"status\":401,\"code\":\"unauthorized\"}");
            return;
        }
        chain.doFilter(request, response);
    }
}
