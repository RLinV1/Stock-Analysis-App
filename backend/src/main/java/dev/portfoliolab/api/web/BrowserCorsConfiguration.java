package dev.portfoliolab.api.web;

import java.net.URI;
import java.util.ArrayList;
import java.util.List;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.Ordered;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsUtils;
import org.springframework.web.cors.DefaultCorsProcessor;
import org.springframework.web.filter.CorsFilter;

/** Explicit browser permission only; every actual API request still requires bearer auth. */
@Configuration(proxyBeanMethods = false)
public class BrowserCorsConfiguration {
    static final int CORS_FILTER_ORDER = Ordered.HIGHEST_PRECEDENCE + 10;
    static final int AUTH_FILTER_ORDER = Ordered.HIGHEST_PRECEDENCE + 20;
    private final CorsConfiguration policy;

    public BrowserCorsConfiguration(
            @Value("${PORTFOLIO_CORS_ALLOWED_ORIGINS:}") String origins) {
        policy = new CorsConfiguration();
        policy.setAllowedOrigins(parseOrigins(origins));
        policy.setAllowedMethods(List.of("GET", "POST"));
        policy.setAllowedHeaders(List.of("Authorization", "Content-Type", "Idempotency-Key"));
        policy.setAllowCredentials(false);
        policy.setMaxAge(0L);
    }

    @Bean
    public FilterRegistrationBean<CorsFilter> browserCorsFilter() {
        // Match the raw path ourselves. MVC path normalization must not broaden
        // the unauthenticated preflight exception to parameter/encoded variants.
        var filter = new CorsFilter(request -> request.getRequestURI().matches(
                "/api/v1/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+") ? policy
                : CorsUtils.isPreFlightRequest(request) ? new CorsConfiguration() : null);
        filter.setCorsProcessor(new DefaultCorsProcessor() {
            @Override
            protected List<String> checkHeaders(CorsConfiguration configuration,
                                                List<String> requestedHeaders) {
                var approved = super.checkHeaders(configuration, requestedHeaders);
                // Spring normally returns an approved subset. This policy rejects
                // the whole preflight when any requested header is unapproved.
                return approved != null && approved.size() == requestedHeaders.size()
                        ? approved : null;
            }
        });
        var registration = new FilterRegistrationBean<>(filter);
        registration.setName("portfolioBrowserCors");
        registration.addUrlPatterns("/*");
        registration.setOrder(CORS_FILTER_ORDER);
        return registration;
    }

    private static List<String> parseOrigins(String configured) {
        if (configured == null || configured.isBlank()) {
            return List.of();
        }
        List<String> origins = new ArrayList<>();
        for (String entry : configured.split(",", -1)) {
            String origin = entry.trim();
            try {
                URI uri = URI.create(origin);
                if (!("http".equals(uri.getScheme()) || "https".equals(uri.getScheme()))
                        || uri.getHost() == null || uri.getRawUserInfo() != null
                        || !uri.getRawPath().isEmpty() || uri.getRawQuery() != null
                        || uri.getRawFragment() != null || uri.getPort() == 0
                        || uri.getPort() > 65535 || uri.getRawAuthority().endsWith(":")) {
                    throw new IllegalArgumentException();
                }
            } catch (IllegalArgumentException exception) {
                // Never echo an accidentally pasted credential or whole URL.
                throw new IllegalStateException(
                        "PORTFOLIO_CORS_ALLOWED_ORIGINS requires exact HTTP(S) origins");
            }
            origins.add(origin);
        }
        return List.copyOf(origins);
    }
}
