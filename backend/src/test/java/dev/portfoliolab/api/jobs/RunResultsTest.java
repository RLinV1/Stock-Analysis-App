package dev.portfoliolab.api.jobs;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import dev.portfoliolab.api.jobs.ArtifactStore.ArtifactUnavailable;
import org.junit.jupiter.api.Test;

class RunResultsTest {
    private static final Path FIXTURE = Path.of("src", "test", "resources", "fixtures", "a0-synthetic");

    private static byte[] bytes(String text) {
        return text.getBytes(StandardCharsets.UTF_8);
    }

    private static void assertInvalid(Runnable parse) {
        var failure = assertThrows(ArtifactUnavailable.class, parse::run);
        assertEquals("artifact_content_invalid", failure.code());
    }

    @Test
    void parsesRealRunnerOutput() throws Exception {
        // Produced by research execute_synthetic_request on the smoke request; guards format drift.
        var curve = RunResults.equityCurve(Files.readAllBytes(FIXTURE.resolve("report.json")));
        assertFalse(curve.dates().isEmpty());
        assertEquals("lstm", curve.series().getFirst().strategy());
        assertTrue(curve.series().stream().allMatch(s -> s.wealth().size() == curve.dates().size()));
        var allocations = RunResults.allocations(Files.readAllBytes(FIXTURE.resolve("allocations.csv")));
        assertFalse(allocations.assets().isEmpty());
        assertEquals(curve.series().stream().map(RunResults.Series::strategy).toList(),
                allocations.strategies().stream().map(RunResults.StrategyAllocations::strategy).toList());
        assertTrue(allocations.strategies().stream()
                .allMatch(s -> s.rows().size() == curve.dates().size()));
    }

    @Test
    void equityCurveKeepsReportOrderAndDates() {
        var curve = RunResults.equityCurve(bytes("{\"test_dates\":[\"2024-01-02\",\"2024-01-03\"],"
                + "\"cost_bps\":1,\"strategies\":{\"lstm\":{\"wealth\":[1.01,1.02]},"
                + "\"equal_weight\":{\"wealth\":[0.99,1.0],\"metrics\":{}}},\"extra\":true}"));
        assertEquals(List.of("2024-01-02", "2024-01-03"), curve.dates());
        assertEquals(1.0, curve.costBps());
        assertEquals(List.of("lstm", "equal_weight"),
                curve.series().stream().map(RunResults.Series::strategy).toList());
        assertEquals(List.of(1.01, 1.02), curve.series().getFirst().wealth());
        assertEquals(RunResults.WEALTH_CONVENTION, curve.convention());
    }

    @Test
    void equityCurveRejectsMalformedReports() {
        for (String body : new String[] {"", "[]", "{}",
                "{\"test_dates\":[],\"cost_bps\":1,\"strategies\":{\"a\":{\"wealth\":[]}}}",
                "{\"test_dates\":[\"d\"],\"cost_bps\":1,\"strategies\":{}}",
                "{\"test_dates\":[\"d\"],\"cost_bps\":\"1\",\"strategies\":{\"a\":{\"wealth\":[1]}}}",
                "{\"test_dates\":[\"d\",\"e\"],\"cost_bps\":1,\"strategies\":{\"a\":{\"wealth\":[1]}}}",
                "{\"test_dates\":[\"d\"],\"cost_bps\":1,\"strategies\":{\"a\":{\"wealth\":[\"1\"]}}}",
                "{\"test_dates\":[1],\"cost_bps\":1,\"strategies\":{\"a\":{\"wealth\":[1]}}}",
                "{\"test_dates\":[\"d\"],\"cost_bps\":1,\"strategies\":{\"a\":{}}}",
                "{\"test_dates\":[\"d\"],\"cost_bps\":1,\"strategies\":{\"a\":{\"wealth\":[1]}}} {}"}) {
            assertInvalid(() -> RunResults.equityCurve(bytes(body)));
        }
    }

    @Test
    void allocationsGroupRowsByStrategyInFileOrder() {
        var allocations = RunResults.allocations(bytes("return_date,strategy,SPY,TLT\r\n"
                + "2024-01-02,lstm,0.7,0.3\r\n2024-01-03,lstm,0.6,0.4\r\n"
                + "2024-01-02,equal_weight,0.5,0.5\r\n2024-01-03,equal_weight,0.5,0.5\r\n"));
        assertEquals(List.of("SPY", "TLT"), allocations.assets());
        assertEquals(List.of("lstm", "equal_weight"),
                allocations.strategies().stream().map(RunResults.StrategyAllocations::strategy).toList());
        var first = allocations.strategies().getFirst().rows().getFirst();
        assertEquals("2024-01-02", first.returnDate());
        assertEquals(List.of(0.7, 0.3), first.weights());
        assertEquals(RunResults.WEIGHT_CONVENTION, allocations.convention());
    }

    @Test
    void allocationsAcceptExponentWeights() {
        var allocations = RunResults.allocations(bytes("return_date,strategy,A,B\n2024-01-02,lstm,1e-07,0.9999999\n"));
        assertEquals(1e-07, allocations.strategies().getFirst().rows().getFirst().weights().getFirst());
    }

    @Test
    void allocationsRejectMalformedFiles() {
        for (String body : new String[] {"", "return_date,strategy,A\n",
                "date,strategy,A\n2024-01-02,lstm,1\n",
                "return_date,strategy\n2024-01-02,lstm\n",
                "return_date,strategy,A,A\n2024-01-02,lstm,0.5,0.5\n",
                "return_date,strategy,A,B\n2024-01-02,lstm,0.5\n",
                "return_date,strategy,A,B\n2024-01-02,lstm,NaN,0.5\n",
                "return_date,strategy,A,B\n2024-01-02,lstm,-0.1,1.1\n",
                "return_date,strategy,A,B\n2024-01-02,lstm,0.5,0.4\n",
                "return_date,strategy,A,B\n2024-01-02,lstm,0x1p-1,0.5\n",
                "return_date,strategy,A,B\n2024-01-02,lstm,0.5d,0.5\n",
                "return_date,strategy,A,B\n2024-01-02,\"lstm\",0.5,0.5\n",
                "return_date,strategy,A,B\n,lstm,0.5,0.5\n"}) {
            assertInvalid(() -> RunResults.allocations(bytes(body)));
        }
        assertInvalid(() -> RunResults.allocations(new byte[] {(byte) 0xff, (byte) 0xfe}));
    }
}
