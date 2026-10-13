package dev.portfoliolab.api.jobs;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.net.URI;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.regex.Pattern;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import software.amazon.awssdk.core.exception.SdkException;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import tools.jackson.core.JacksonException;
import tools.jackson.core.StreamReadFeature;
import tools.jackson.core.json.JsonFactory;
import tools.jackson.databind.DeserializationFeature;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;

/** Reads worker-registered artifacts; never trusts object bytes without the database hash. */
@Component
public class ArtifactStore {
    static final int MAX_MANIFEST_BYTES = 1024 * 1024;
    static final String INDEX_NAME = "artifact-index.json";
    static final String INDEX_INVALID = "artifact_index_invalid";
    private static final String REPORT_PATH = "report.json";
    private static final Pattern SHA256 = Pattern.compile("[0-9a-f]{64}");
    private static final JsonMapper JSON = JsonMapper.builder(
            JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS).build();
    private final S3Client s3;
    private final String bucket;

    @Autowired
    public ArtifactStore(@Value("${ARTIFACT_BUCKET:portfolio-lab-artifacts}") String bucket,
                         @Value("${S3_ENDPOINT_URL:}") String endpoint,
                         @Value("${AWS_REGION:us-east-1}") String region) {
        this(client(endpoint, region), bucket);
    }

    public ArtifactStore(S3Client s3, String bucket) {
        this.s3 = s3;
        this.bucket = bucket;
    }

    /** Raised when an object is missing, unreadable, oversized or fails its registered hash. */
    public static final class ArtifactUnavailable extends RuntimeException {
        private final String code;

        public ArtifactUnavailable(String code, Throwable cause) {
            super(code, cause);
            this.code = code;
        }

        public String code() {
            return code;
        }
    }

    public byte[] readVerified(String key, String expectedSha256) {
        final byte[] content;
        try (InputStream body = s3.getObject(GetObjectRequest.builder().bucket(bucket).key(key).build())) {
            content = body.readNBytes(MAX_MANIFEST_BYTES + 1);
        } catch (SdkException | IOException ex) {
            throw new ArtifactUnavailable("artifact_unavailable", ex);
        }
        if (content.length > MAX_MANIFEST_BYTES) {
            throw new ArtifactUnavailable("artifact_too_large", null);
        }
        if (!sha256(content).equals(expectedSha256)) {
            throw new ArtifactUnavailable("artifact_integrity_failure", null);
        }
        return content;
    }

    /** One artifact named by a verified index: object key and its registered SHA-256. */
    public record IndexedFile(String key, String sha256) {}

    /**
     * Finds the single report.json entry of an already hash-verified artifact index.
     * The index hash comes from PostgreSQL; the prefix check is defense in depth so an
     * entry can never name an object outside the index's own attempt directory.
     */
    public static IndexedFile reportEntry(byte[] index, String manifestKey) {
        if (manifestKey == null || !manifestKey.endsWith("/" + INDEX_NAME)) {
            throw invalidIndex(null);
        }
        String prefix = manifestKey.substring(0, manifestKey.length() - INDEX_NAME.length());
        final JsonNode root;
        try {
            root = JSON.readTree(index);
        } catch (JacksonException ex) {
            throw invalidIndex(ex);
        }
        JsonNode files = root == null || !root.isObject() ? null : root.get("files");
        if (files == null || !files.isArray()) {
            throw invalidIndex(null);
        }
        JsonNode report = null;
        for (int i = 0; i < files.size(); i++) {
            JsonNode entry = files.get(i);
            JsonNode path = entry.isObject() ? entry.get("path") : null;
            if (path == null || !path.isTextual()) {
                throw invalidIndex(null);
            }
            if (REPORT_PATH.equals(path.textValue())) {
                if (report != null) {
                    throw invalidIndex(null);
                }
                report = entry;
            }
        }
        if (report == null) {
            throw invalidIndex(null);
        }
        JsonNode key = report.get("key");
        JsonNode sha256 = report.get("sha256");
        JsonNode bytes = report.get("bytes");
        // The worker writes exactly <attempt prefix>/report.json; accept nothing else.
        if (key == null || !key.isTextual() || !key.textValue().equals(prefix + "report.json")
                || sha256 == null || !sha256.isTextual() || !SHA256.matcher(sha256.textValue()).matches()
                || bytes == null || !bytes.isIntegralNumber()
                || bytes.bigIntegerValue().signum() < 0
                || bytes.bigIntegerValue().compareTo(BigInteger.valueOf(MAX_MANIFEST_BYTES)) > 0) {
            throw invalidIndex(null);
        }
        return new IndexedFile(key.textValue(), sha256.textValue());
    }

    private static ArtifactUnavailable invalidIndex(Throwable cause) {
        return new ArtifactUnavailable(INDEX_INVALID, cause);
    }

    private static S3Client client(String endpoint, String region) {
        var builder = S3Client.builder().region(Region.of(region))
                .forcePathStyle(true);
        if (!endpoint.isBlank()) {
            builder.endpointOverride(URI.create(endpoint));
        }
        return builder.build();
    }

    private static String sha256(byte[] content) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(content));
        } catch (NoSuchAlgorithmException ex) {
            throw new IllegalStateException("SHA-256 is unavailable", ex);
        }
    }
}
