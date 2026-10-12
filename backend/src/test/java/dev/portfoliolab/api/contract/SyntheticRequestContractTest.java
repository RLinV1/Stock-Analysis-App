package dev.portfoliolab.api.contract;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import org.junit.jupiter.api.Test;

class SyntheticRequestContractTest {
    private static Path fixture(String name) {
        return Path.of("..", "contracts", "examples", name);
    }

    private static byte[] example() throws IOException {
        return Files.readAllBytes(fixture("synthetic-smoke.v1.json"));
    }

    @Test
    void matchesPythonFixtureAndCanonicalOrdering() throws IOException {
        var accepted = SyntheticRequestContract.parse(example());
        assertEquals(Files.readString(fixture("synthetic-smoke.v1.sha256")).trim(), accepted.sha256());
        assertEquals(140, accepted.dataset().observations());
        assertEquals(2026, accepted.dataset().seed());
        assertEquals(1, accepted.model().epochs());
        var reordered = """
                {"model":{"epochs":1,"hidden_size":8,"lookback":10},
                 "execution":{"cost_bps":1,"seed":7},
                 "dataset":{"seed":2026,"observations":140,"kind":"synthetic"},
                 "contract_version":1}
                """;
        assertEquals(accepted.canonicalJson(), SyntheticRequestContract.parse(
                reordered.getBytes(StandardCharsets.UTF_8)).canonicalJson());
    }

    @Test
    void rejectsInvalidShapeAndBudgets() throws IOException {
        String body = new String(example(), StandardCharsets.UTF_8);
        for (String invalid : new String[] {
                body.replace("\"contract_version\": 1", "\"contract_version\": 2"),
                body.replace("\"epochs\": 1", "\"epochs\": 4"),
                body.replace("\"epochs\": 1", "\"epochs\": true"),
                body.replace("\"epochs\": 1", "\"epochs\": 1.0"),
                body.replace("\"observations\": 140", "\"observations\": 139"),
                body.replace("\"seed\": 2026", "\"seed\": 18446744073709551617"),
                body.replace("\"kind\": \"synthetic\"", "\"kind\": \"historical\""),
                body.replace("\"epochs\": 1", "\"epochs\": 1, \"extra\": 0"),
                body.replace("\"epochs\": 1", "\"epochs\": 1, \"epochs\": 1"),
                body + " true",
        }) {
            assertThrows(IllegalArgumentException.class,
                    () -> SyntheticRequestContract.parse(invalid.getBytes(StandardCharsets.UTF_8)), invalid);
        }
        assertThrows(IllegalArgumentException.class,
                () -> SyntheticRequestContract.parse(new byte[8193]));
    }
}
