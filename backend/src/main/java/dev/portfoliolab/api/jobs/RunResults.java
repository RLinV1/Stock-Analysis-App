package dev.portfoliolab.api.jobs;

import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.regex.Pattern;

import dev.portfoliolab.api.jobs.ArtifactStore.ArtifactUnavailable;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.JsonNode;

/**
 * Typed views of verified A0 run artifacts written by research/src/portfolio_lab/runner.py.
 * Inputs are already hash-verified; parsing is still strict so a format drift between the
 * runner and the API fails loudly instead of returning a misleading series.
 */
public final class RunResults {
    static final String CONTENT_INVALID = "artifact_content_invalid";
    private static final Pattern DECIMAL = Pattern.compile("-?[0-9]+(\\.[0-9]+)?([eE][-+]?[0-9]+)?");
    public static final String WEALTH_CONVENTION =
            "Growth of 1 after net costs: cumulative product of (1 + net return) through each date";
    public static final String WEIGHT_CONVENTION =
            "Long-only target weights decided at the prior close and applied to the return on "
                    + "returnDate; each row sums to 1. A0 does not record raw model outputs.";

    private RunResults() {}

    public record Series(String strategy, List<Double> wealth) {}
    public record EquityCurve(List<String> dates, double costBps, String convention, List<Series> series) {}
    public record AllocationRow(String returnDate, List<Double> weights) {}
    public record StrategyAllocations(String strategy, List<AllocationRow> rows) {}
    public record Allocations(List<String> assets, String convention, List<StrategyAllocations> strategies) {}

    /** Model and baseline wealth on the report's common test dates, in report order. */
    public static EquityCurve equityCurve(byte[] report) {
        final JsonNode root;
        try {
            root = ArtifactStore.JSON.readTree(report);
        } catch (JacksonException ex) {
            throw invalid(ex);
        }
        if (root == null || !root.isObject()) {
            throw invalid(null);
        }
        JsonNode datesNode = root.get("test_dates");
        JsonNode cost = root.get("cost_bps");
        JsonNode strategies = root.get("strategies");
        if (datesNode == null || !datesNode.isArray() || datesNode.size() == 0
                || cost == null || !cost.isNumber() || !Double.isFinite(cost.doubleValue())
                || strategies == null || !strategies.isObject() || strategies.size() == 0) {
            throw invalid(null);
        }
        List<String> dates = new ArrayList<>(datesNode.size());
        for (int i = 0; i < datesNode.size(); i++) {
            JsonNode date = datesNode.get(i);
            if (!date.isTextual() || date.textValue().isEmpty()) {
                throw invalid(null);
            }
            dates.add(date.textValue());
        }
        List<Series> series = new ArrayList<>();
        for (Entry<String, JsonNode> strategy : strategies.properties()) {
            JsonNode wealth = strategy.getValue().isObject() ? strategy.getValue().get("wealth") : null;
            if (wealth == null || !wealth.isArray() || wealth.size() != dates.size()) {
                throw invalid(null);
            }
            List<Double> values = new ArrayList<>(wealth.size());
            for (int i = 0; i < wealth.size(); i++) {
                values.add(finite(wealth.get(i)));
            }
            series.add(new Series(strategy.getKey(), List.copyOf(values)));
        }
        return new EquityCurve(List.copyOf(dates), cost.doubleValue(), WEALTH_CONVENTION, List.copyOf(series));
    }

    /** Per-strategy daily target weights from allocations.csv, assets in header order. */
    public static Allocations allocations(byte[] csv) {
        String text;
        try {
            text = StandardCharsets.UTF_8.newDecoder()
                    .onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(csv)).toString();
        } catch (CharacterCodingException ex) {
            throw invalid(ex);
        }
        // Python's csv module writes CRLF; the runner never needs quoting for its fields.
        String[] lines = text.split("\r?\n", -1);
        int end = lines.length;
        while (end > 0 && lines[end - 1].isEmpty()) {
            end--;
        }
        if (end < 2 || text.indexOf('"') >= 0) {
            throw invalid(null);
        }
        String[] header = lines[0].split(",", -1);
        if (header.length < 3 || !"return_date".equals(header[0]) || !"strategy".equals(header[1])) {
            throw invalid(null);
        }
        List<String> assets = List.of(header).subList(2, header.length);
        if (assets.stream().anyMatch(String::isEmpty) || assets.stream().distinct().count() != assets.size()) {
            throw invalid(null);
        }
        Map<String, List<AllocationRow>> byStrategy = new LinkedHashMap<>();
        for (int line = 1; line < end; line++) {
            String[] fields = lines[line].split(",", -1);
            if (fields.length != header.length || fields[0].isEmpty() || fields[1].isEmpty()) {
                throw invalid(null);
            }
            List<Double> weights = new ArrayList<>(assets.size());
            double sum = 0.0;
            for (int i = 2; i < fields.length; i++) {
                double weight = parseWeight(fields[i]);
                weights.add(weight);
                sum += weight;
            }
            // Same tolerance the runner's evaluate() enforces before writing the file.
            if (Math.abs(sum - 1.0) > 1e-6) {
                throw invalid(null);
            }
            byStrategy.computeIfAbsent(fields[1], key -> new ArrayList<>())
                    .add(new AllocationRow(fields[0], List.copyOf(weights)));
        }
        List<StrategyAllocations> strategies = byStrategy.entrySet().stream()
                .map(entry -> new StrategyAllocations(entry.getKey(), List.copyOf(entry.getValue())))
                .toList();
        return new Allocations(List.copyOf(assets), WEIGHT_CONVENTION, strategies);
    }

    private static double finite(JsonNode value) {
        if (value == null || !value.isNumber() || !Double.isFinite(value.doubleValue())) {
            throw invalid(null);
        }
        return value.doubleValue();
    }

    private static double parseWeight(String field) {
        // Python float repr only; Double.parseDouble alone would also take "NaN", "1d" or hex.
        if (!DECIMAL.matcher(field).matches()) {
            throw invalid(null);
        }
        double weight = Double.parseDouble(field);
        if (!(weight >= 0.0 && weight <= 1.0)) {
            throw invalid(null);
        }
        return weight;
    }

    private static ArtifactUnavailable invalid(Throwable cause) {
        return new ArtifactUnavailable(CONTENT_INVALID, cause);
    }
}
