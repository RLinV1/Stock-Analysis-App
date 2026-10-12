package dev.portfoliolab.api.contract;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

import tools.jackson.core.JacksonException;
import tools.jackson.core.StreamReadFeature;
import tools.jackson.core.json.JsonFactory;
import tools.jackson.databind.DeserializationFeature;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;

/** Strict consumer of the bounded synthetic request v1, not a general schema validator. */
public final class SyntheticRequestContract {
    private static final int MAX_BYTES = 8192;
    private static final JsonMapper JSON = JsonMapper.builder(
            JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS).build();

    private SyntheticRequestContract() {}

    public record Dataset(int observations, long seed) {}
    public record Model(int lookback, int hiddenSize, int epochs) {}
    public record Execution(long seed, int costBps) {}
    public record Accepted(Dataset dataset, Model model, Execution execution,
                           String canonicalJson, String sha256) {}

    public static Accepted parse(byte[] body) {
        if (body == null || body.length == 0 || body.length > MAX_BYTES) {
            throw new IllegalArgumentException("Request body must contain 1..8192 bytes");
        }
        final JsonNode root;
        try {
            root = JSON.readTree(body);
        } catch (JacksonException ex) {
            throw new IllegalArgumentException("Invalid JSON request", ex);
        }
        object(root, "request", "contract_version", "dataset", "model", "execution");
        if (integer(root.get("contract_version"), "contract_version", 1, 1) != 1) {
            throw new IllegalArgumentException("Unsupported contract version");
        }
        JsonNode datasetNode = object(root.get("dataset"), "dataset", "kind", "observations", "seed");
        JsonNode kind = datasetNode.get("kind");
        if (!kind.isTextual() || !"synthetic".equals(kind.textValue())) {
            throw new IllegalArgumentException("dataset.kind must be synthetic");
        }
        Dataset dataset = new Dataset(
                Math.toIntExact(integer(datasetNode.get("observations"), "dataset.observations", 140, 420)),
                integer(datasetNode.get("seed"), "dataset.seed", 0, 4294967295L));

        JsonNode modelNode = object(root.get("model"), "model", "lookback", "hidden_size", "epochs");
        Model model = new Model(
                Math.toIntExact(integer(modelNode.get("lookback"), "model.lookback", 10, 50)),
                Math.toIntExact(integer(modelNode.get("hidden_size"), "model.hidden_size", 8, 64)),
                Math.toIntExact(integer(modelNode.get("epochs"), "model.epochs", 1, 3)));

        JsonNode executionNode = object(root.get("execution"), "execution", "seed", "cost_bps");
        Execution execution = new Execution(
                integer(executionNode.get("seed"), "execution.seed", 0, 4294967295L),
                Math.toIntExact(integer(executionNode.get("cost_bps"), "execution.cost_bps", 0, 100)));

        // All values are fixed ASCII keys/literals and integers. This is exactly Python's
        // json.dumps(sort_keys=True, separators=(",", ":")) for request v1.
        String canonical = "{\"contract_version\":1,\"dataset\":{\"kind\":\"synthetic\",\"observations\":"
                + dataset.observations() + ",\"seed\":" + dataset.seed()
                + "},\"execution\":{\"cost_bps\":" + execution.costBps()
                + ",\"seed\":" + execution.seed()
                + "},\"model\":{\"epochs\":" + model.epochs()
                + ",\"hidden_size\":" + model.hiddenSize()
                + ",\"lookback\":" + model.lookback() + "}}";
        return new Accepted(dataset, model, execution, canonical, hash(canonical));
    }

    private static JsonNode object(JsonNode value, String name, String... keys) {
        if (value == null || !value.isObject() || value.size() != keys.length) {
            throw new IllegalArgumentException(name + " must contain exactly the required fields");
        }
        for (String key : keys) {
            if (!value.has(key)) {
                throw new IllegalArgumentException(name + " missing " + key);
            }
        }
        return value;
    }

    private static long integer(JsonNode value, String name, long minimum, long maximum) {
        if (value == null || !value.isIntegralNumber()) {
            throw new IllegalArgumentException(name + " must be an integer");
        }
        BigInteger number = value.bigIntegerValue();
        if (number.compareTo(BigInteger.valueOf(minimum)) < 0
                || number.compareTo(BigInteger.valueOf(maximum)) > 0) {
            throw new IllegalArgumentException(name + " is outside its allowed range");
        }
        return number.longValueExact();
    }

    private static String hash(String canonical) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(canonical.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException ex) {
            throw new IllegalStateException("SHA-256 is unavailable", ex);
        }
    }
}
