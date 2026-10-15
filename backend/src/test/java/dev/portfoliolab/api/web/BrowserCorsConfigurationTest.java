package dev.portfoliolab.api.web;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.options;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.core.annotation.Order;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

class BrowserCorsConfigurationTest {
    private static final String ORIGIN = "http://localhost:8081";
    private static final String TOKEN = "unit-test-secret-123";

    private MockMvc mvc(String origins) {
        return MockMvcBuilders.standaloneSetup(new TestController())
                .addFilters(new BrowserCorsConfiguration(origins).browserCorsFilter().getFilter(),
                        new LocalOperatorFilter(TOKEN)).build();
    }

    private MockHttpServletRequestBuilder preflight(String origin, String method, String headers) {
        return options("/api/v1/runs").header("Origin", origin)
                .header("Access-Control-Request-Method", method)
                .header("Access-Control-Request-Headers", headers);
    }

    @Test
    void validatedPreflightNeedsNoBearer() throws Exception {
        mvc(ORIGIN).perform(preflight(ORIGIN, "POST", "authorization,content-type,idempotency-key"))
                .andExpect(status().isOk())
                .andExpect(header().string("Access-Control-Allow-Origin", ORIGIN))
                .andExpect(header().string("Access-Control-Allow-Methods", "GET,POST"))
                .andExpect(header().doesNotExist("Access-Control-Allow-Credentials"));
    }

    @Test
    void allowedActualGetAndPostRequireBearerAndReturnCorsHeaders() throws Exception {
        var mvc = mvc(ORIGIN);
        for (var request : new MockHttpServletRequestBuilder[] {
                get("/api/v1/runs"), post("/api/v1/runs")}) {
            mvc.perform(request.header("Origin", ORIGIN).header("Authorization", "Bearer " + TOKEN))
                    .andExpect(status().isOk())
                    .andExpect(header().string("Access-Control-Allow-Origin", ORIGIN))
                    .andExpect(content().string("runs"));
        }
        mvc.perform(get("/api/v1/runs").header("Origin", ORIGIN))
                .andExpect(status().isUnauthorized())
                .andExpect(header().string("Access-Control-Allow-Origin", ORIGIN));
    }

    @Test
    void rejectsUnknownOriginsMethodsAndHeaders() throws Exception {
        var mvc = mvc(ORIGIN);
        for (var request : new MockHttpServletRequestBuilder[] {
                preflight("https://unconfigured.invalid", "POST", "Authorization"),
                preflight("http://localhost:8081.attacker.invalid", "POST", "Authorization"),
                preflight(ORIGIN, "DELETE", "Authorization"),
                preflight(ORIGIN, "POST", "Authorization,X-Unapproved")}) {
            mvc.perform(request).andExpect(result -> assertEquals(403,
                            result.getResponse().getStatus(), result.getRequest().getHeader("Origin")
                                    + " " + result.getRequest().getHeader("Access-Control-Request-Method")
                                    + " " + result.getRequest().getHeader("Access-Control-Request-Headers")))
                    .andExpect(header().doesNotExist("Access-Control-Allow-Origin"));
        }
    }

    @Test
    void noOriginsMeansNoCrossOriginPermission() throws Exception {
        var mvc = mvc("");
        mvc.perform(preflight(ORIGIN, "GET", "Authorization"))
                .andExpect(status().isForbidden())
                .andExpect(header().doesNotExist("Access-Control-Allow-Origin"));
        mvc.perform(get("/api/v1/runs").header("Origin", ORIGIN)
                .header("Authorization", "Bearer " + TOKEN))
                .andExpect(status().isForbidden());
        mvc.perform(get("/api/v1/runs").header("Authorization", "Bearer " + TOKEN))
                .andExpect(status().isOk());
    }

    @Test
    void preflightDoesNotPermitPathVariantsOrOtherRoutes() throws Exception {
        var mvc = mvc(ORIGIN);
        for (String path : new String[] {"/api;x=1/v1/runs", "/api/v1/runs;x=1",
                "/api/v1//runs", "/api/v1/../runs", "/api/v1/%72uns",
                "/actuator/health", "/unknown"}) {
            // MockMvc's URI builder normalizes duplicate separators; preserve the
            // raw servlet URI so this exercises the filter's actual path guard.
            mvc.perform(options("/api/v1/runs").with(request -> {
                        request.setRequestURI(path);
                        return request;
                    }).header("Origin", ORIGIN)
                    .header("Access-Control-Request-Method", "GET")
                    .header("Access-Control-Request-Headers", "Authorization"))
                    .andExpect(result -> assertEquals(403, result.getResponse().getStatus(), path))
                    .andExpect(header().doesNotExist("Access-Control-Allow-Origin"));
        }
        mvc.perform(get("/api;x=1/v1/runs").header("Origin", ORIGIN))
                .andExpect(status().isUnauthorized());
        mvc.perform(get("/actuator/health")).andExpect(status().isOk());
    }

    @Test
    void acceptsMultipleExactOriginsWithOptionalWhitespace() throws Exception {
        mvc(" " + ORIGIN + ", https://lab.example:8443 ")
                .perform(preflight("https://lab.example:8443", "GET", "Authorization"))
                .andExpect(status().isOk())
                .andExpect(header().string("Access-Control-Allow-Origin", "https://lab.example:8443"));
    }

    @Test
    void invalidConfigurationFailsWithoutEchoingIt() {
        for (String origins : new String[] {"*", "http://*.example", "null", "file://host",
                "http://localhost:8081/", "https://example/path", "https://user:password@example",
                "https://example?query=1", "https://example#fragment", "https://example:",
                "https://example:0", "https://example:65536", "https://example:-2",
                ORIGIN + ",", "," + ORIGIN, ORIGIN + ",," + ORIGIN}) {
            var exception = assertThrows(IllegalStateException.class,
                    () -> new BrowserCorsConfiguration(origins), origins);
            assertEquals("PORTFOLIO_CORS_ALLOWED_ORIGINS requires exact HTTP(S) origins",
                    exception.getMessage());
        }
    }

    @Test
    void corsRegistrationPrecedesBearerFilter() {
        int corsOrder = new BrowserCorsConfiguration(ORIGIN).browserCorsFilter().getOrder();
        int authOrder = LocalOperatorFilter.class.getAnnotation(Order.class).value();
        assertTrue(corsOrder < authOrder);
    }

    @RestController
    static class TestController {
        @GetMapping("/api/v1/runs")
        String list() { return "runs"; }
        @PostMapping("/api/v1/runs")
        String submit() { return "runs"; }
        @GetMapping("/actuator/health")
        String health() { return "healthy"; }
    }
}
